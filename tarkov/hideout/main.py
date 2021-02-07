import time
from typing import Dict, List, cast

import ujson

import tarkov.profile.profile as profile_
from server import db_dir, logger
from tarkov import inventory
from .models import HideoutArea, HideoutAreaType, HideoutProduction
from tarkov.inventory import item_templates_repository


class Hideout:
    # Fuel burn rate, per second
    __FUEL_BURN_RATE = 60 / (14 * 60 * 60 + 27 * 60 + 28)
    __GENERATOR_SPEED_WITHOUT_FUEL = 0.15
    # __FUEL_BURN_RATE = 0.0011527777777778
    data: Dict
    metadata: Dict

    time_elapsed: int
    work_time_elapsed: int
    current_time: int

    def __init__(self, profile: 'profile_.Profile'):
        self.path = profile.profile_dir.joinpath('pmc_hideout.json')
        self.meta_path = profile.profile_dir.joinpath('pmc_hideout.meta.json')

        self.profile: 'profile_.Profile' = profile

    @staticmethod
    def get_recipe(recipe_id):
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

    def put_items_in_area_slots(self, area_type: HideoutAreaType, slot_id: int, item: inventory.Item):
        area = self.get_area(area_type)

        item.location = None
        item.parent_id = None
        item.slotId = None

        area_slots = area['slots']
        diff = slot_id + 1 - len(area_slots)
        if diff > 0:
            area_slots.extend([{'item': None} for _ in range(diff)])

        area_slots[slot_id]['item'] = [item]

    def take_item_from_area_slot(self, area_type: HideoutAreaType, slot_id: int) -> inventory.Item:
        area = self.get_area(area_type)
        slot = area['slots'][slot_id]
        item = slot['item'][0]
        slot['item'] = None
        return item

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

    def take_production(self, recipe_id: str) -> List[inventory.Item]:
        recipe = self.get_recipe(recipe_id)

        product_tpl = recipe['endProduct']
        count = recipe['count']

        items = item_templates_repository.create_item(product_tpl, count)

        for item in items:
            item.upd.SpawnedInSession = True

        del self.data['Production'][recipe_id]

        return items

    def toggle_area(self, area_type: HideoutAreaType, enabled: bool):
        area = self.get_area(area_type)
        area['active'] = enabled

    def __update_production_time(self, time_elapsed: int, generator_worked: int):
        for production in self.data['Production'].values():
            production = cast(HideoutProduction, production)

            generator_didnt_work_for = time_elapsed - generator_worked
            if generator_didnt_work_for < 0:
                raise AssertionError('generator_didnt_work_for < 0')

            production['Progress'] += generator_worked + time_elapsed * self.__GENERATOR_SPEED_WITHOUT_FUEL
            # production['SkipTime'] += skip_time

    def __update_fuel(self) -> int:
        """
        :returns: Amount of time hideout had a generator working
        """
        # Return 0 if generator was not active
        generator_area = self.get_area(HideoutAreaType.Generator)
        if not generator_area['active']:
            return 0

        fuel_should_be_consumed = self.time_elapsed * Hideout.__FUEL_BURN_RATE
        fuel_consumed = 0

        for slot in generator_area['slots']:
            if not fuel_should_be_consumed:
                break

            if not slot['item']:
                continue

            fuel_tank = slot['item'][0]

            # TODO: hideout will crash if fuel tank doesn't have these properties
            fuel_in_tank = fuel_tank['upd']['Resource']['Value']

            consumed = min(fuel_should_be_consumed, fuel_in_tank)
            fuel_consumed += consumed
            fuel_tank['upd']['Resource']['Value'] -= consumed
            fuel_should_be_consumed -= consumed

        if fuel_consumed < fuel_should_be_consumed:
            self.toggle_area(HideoutAreaType.Generator, False)

        return int(fuel_consumed / self.__FUEL_BURN_RATE)
        pass

    def read(self):
        self.data: dict = ujson.load(self.path.open('r', encoding='utf8'))

        if not self.meta_path.exists():
            self.metadata = {'updated_at': int(time.time())}
        else:
            self.metadata = ujson.load(self.meta_path.open('r', encoding='utf8'))

        self.current_time = int(time.time())
        self.time_elapsed = self.current_time - self.metadata['updated_at']
        time_generator_worked = self.__update_fuel()
        skip_time = self.time_elapsed - time_generator_worked

        logger.debug(f'Generator worked for: {time_generator_worked}')
        logger.debug(f'Time skipped: {skip_time}')

        self.__update_production_time(self.time_elapsed, time_generator_worked)

        self.metadata['updated_at'] = self.current_time

    def write(self):
        ujson.dump(self.data, self.path.open('w', encoding='utf8'), indent=4)
        ujson.dump(self.metadata, self.meta_path.open('w', encoding='utf8'), indent=4)
