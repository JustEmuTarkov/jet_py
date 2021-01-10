from __future__ import annotations

import enum
import time
from typing import List, TypedDict, Union

import ujson

import mods.core.lib.inventory as inventory_lib
import mods.core.lib.items as items_lib
from mods.core.lib import NotFoundError
from mods.core.lib.trader import Traders
from server import root_dir, db_dir


class Encyclopedia:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.data = profile.pmc_profile['Encyclopedia']

    def examine(self, item: Union[items_lib.Item, items_lib.TemplateId]):
        if isinstance(item, dict):
            item_tpl_id = item['_tpl']
        else:
            item_tpl_id = item

        if item_tpl_id not in self.data:
            self.data[item_tpl_id] = False

    def read(self, item: Union[items_lib.Item, items_lib.TemplateId]):
        if isinstance(item, dict):
            item_tpl_id = item['_tpl']
        else:
            item_tpl_id = item

        self.data[item_tpl_id] = True


class Quests:
    def __init__(self, profile: Profile):
        self.data = profile.quests_data

    def get_quest(self, quest_id: str):
        try:
            return next(quest for quest in self.data if quest['qid'] == quest_id)
        except StopIteration as e:
            raise KeyError from e

    def accept_quest(self, quest_id: str):
        try:
            quest = self.get_quest(quest_id)
            if quest['status'] in ('Started', 'Success'):
                raise ValueError('Quest is already accepted')
        except KeyError:
            pass

        quest = {
            'qid': quest_id,
            'startTime': int(time.time()),
            'completedConditions': [],
            'statusTimers': {},
            'status': 'Started',
        }
        self.data.append(quest)


class HideoutAreaType(enum.Enum):
    Vents = 0
    Security = 1
    Lavatory = 2
    Stash = 3
    Generator = 4
    Heating = 5
    WaterCollector = 6
    MedStation = 7
    NutritionUnit = 8
    RestSpace = 9
    Workbench = 10
    IntelCenter = 11
    ShootingRange = 12
    Library = 13
    ScavCase = 14
    Illumination = 15
    PlaceOfFame = 16
    AirFiltering = 17
    SolarPower = 18
    BoozeGenerator = 19
    BitcoinFarm = 20
    ChristmasTree = 21


class HideoutArea(TypedDict):
    type: int
    level: int
    active: bool
    passiveBonusesEnabled: bool
    completeTime: int
    constructing: bool
    slots: list


class HideoutProduction(TypedDict):
    Progress: int
    inProgress: bool
    RecipeId: str
    Products: List
    SkipTime: int
    StartTime: int


class HideoutRecipe(TypedDict):
    _id: str
    areaType: int
    requirements: List
    continuous: bool
    productionTime: int
    endProduct: str
    count: int
    productionLimitCount: int


class Hideout:
    data: dict

    def __init__(self, profile: Profile):
        self.path = profile.profile_path.joinpath('pmc_hideout.json')

        self.profile: Profile = profile

    def get_recipe(self, recipe_id):
        recipe_path = db_dir.joinpath('hideout', 'production', f'{recipe_id}.json')
        return ujson.load(recipe_path.open('r', encoding='utf8'))

    def get_area(self, area_type: HideoutAreaType) -> HideoutArea:
        area = (a for a in self.data['Areas'] if a['type'] == area_type.value)
        try:
            return next(area)
        except StopIteration as e:
            raise ValueError(f'Hideout are with type {area_type} does not exist') from e

    def area_upgrade_start(self, area_type: HideoutAreaType):
        area = self.get_area(area_type)
        area['completeTime'] = 0  # Todo: grab construction time from db/hideout/areas and current time
        area['constructing'] = True

    def area_upgrade_finish(self, area_type: HideoutAreaType):
        area = self.get_area(area_type)
        area['constructing'] = False
        area['completeTime'] = 0
        area['level'] += 1

    def put_items_in_area_slots(self, area_type: HideoutAreaType, slot_id: int, item: items_lib.Item):
        area = self.get_area(area_type)

        del item['location']
        del item['parentId']
        del item['slotId']

        area_slots = area['slots']
        diff = slot_id + 1 - len(area_slots)
        if diff > 0:
            area_slots.extend([{'item': None} for _ in range(diff)])

        area_slots[slot_id]['item'] = [item]

    def start_single_production(self, recipe_id: str, timestamp: int = None):
        if not timestamp:
            timestamp = int(time.time())

        production = HideoutProduction(
            inProgress=True,
            RecipeId=recipe_id,
            StartTime=timestamp,
            Progress=0,
            SkipTime=0,
            Products=[]
        )

        self.data['Production'][recipe_id] = production

    def take_production(self, recipe_id: str) -> List[items_lib.Item]:

        recipe = self.get_recipe(recipe_id)

        product_tpl = recipe['endProduct']
        count = recipe['count']

        try:
            items = items_lib.ItemTemplatesRepository().get_preset(product_tpl)
        except NotFoundError:
            items = [
                items_lib.Item(_id=inventory_lib.generate_item_id(), _tpl=product_tpl) for _ in range(count)
            ]

        inventory_lib.regenerate_items_ids(items)

        del self.data['Production'][recipe_id]

        return items

    def toggle_area(self, area_type: HideoutAreaType, enabled: bool):
        area = self.get_area(area_type)
        area['active'] = enabled

    def read(self):
        self.data: dict = ujson.load(self.path.open('r', encoding='utf8'))
        self.__update_production_time()

    def write(self):
        ujson.dump(self.data, self.path.open('w', encoding='utf8'), indent=4)

    def __update_production_time(self):
        for recipe_id, production in self.data['Production'].items():
            production: HideoutProduction

            # if not production['inProgress']:
            #     continue

            now = int(time.time())
            last_time_visited = production['StartTime'] + production['Progress'] + production['SkipTime']
            production['Progress'] += now - last_time_visited

            production_recipe = self.get_recipe(recipe_id)
            # if production['Progress'] >= production_recipe['productionTime']:
            #     production['inProgress'] = False


class Profile:
    pmc_profile: dict

    hideout: Hideout

    quests: Quests
    quests_data: List[dict]

    inventory: inventory_lib.Inventory
    encyclopedia: Encyclopedia

    def __init__(self, profile_id: str):
        self.profile_id = profile_id

        self.profile_path = root_dir.joinpath('resources', 'profiles', profile_id)

        self.pmc_profile_path = self.profile_path.joinpath('pmc_profile.json')

        self.quests_path = self.profile_path.joinpath('pmc_quests.json')

    def get_profile(self):
        profile_data = {}
        for file in self.profile_path.glob('pmc_*.json'):
            profile_data[file.stem] = ujson.load(file.open('r', encoding='utf8'))

        profile_base = self.pmc_profile
        profile_base['Hideout'] = self.hideout.data
        profile_base['Inventory'] = self.inventory.stash
        profile_base['Quests'] = profile_data['pmc_quests']
        profile_base['Stats'] = profile_data['pmc_stats']
        profile_base['TraderStandings'] = profile_data['pmc_traders']
        return profile_base

    def add_insurance(self, item: items_lib.Item, trader: Traders):
        insurance_info = {
            'itemId': item['_id'],
            'tid': trader.value
        }
        self.pmc_profile['InsuredItems'].append(insurance_info)

        #  Todo remove insurance from items that aren't present in inventory after raid

    def __read(self):
        self.pmc_profile: dict = ujson.load(self.pmc_profile_path.open('r', encoding='utf8'))

        self.encyclopedia = Encyclopedia(profile=self)

        self.inventory = inventory_lib.Inventory(profile_id=self.profile_id)
        self.inventory.read()

        self.quests_data: List[dict] = ujson.load(self.quests_path.open('r', encoding='utf8'))
        self.quests = Quests(profile=self)

        self.hideout = Hideout(profile=self)
        self.hideout.read()

    def __write(self):
        ujson.dump(self.pmc_profile, self.pmc_profile_path.open('w', encoding='utf8'), indent=4)

        self.inventory.write()
        self.hideout.write()

        ujson.dump(self.quests_data, self.quests_path.open('w', encoding='utf8'), indent=4)

    def __enter__(self):
        self.__read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            raise exc_type from exc_val
        self.__write()
