from __future__ import annotations

from typing import List, Union

import ujson

import tarkov.inventory.repositories
from server import root_dir
from server.utils import atomic_write
from tarkov import inventory as inventory_, quests
from tarkov.hideout import Hideout
from tarkov.inventory.models import Item, TemplateId
from tarkov.notifier import Mail
from tarkov.trader import TraderType
from .models import ItemInsurance, ProfileModel


class Encyclopedia:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.data = profile.pmc_profile.Encyclopedia

    def examine(self, item: Union[Item, TemplateId]):
        if isinstance(item, Item):
            self.data[item.tpl] = False

        else:
            item_template_id = item
            self.data[item_template_id] = False

    def read(self, item: Union[Item, TemplateId]):
        if isinstance(item, Item):
            item_tpl_id = item.tpl
        else:
            item_tpl_id = item

        self.data[item_tpl_id] = True


class Profile:
    # pylint: disable=too-many-instance-attributes
    # Disabling that in case of profile is reasonable

    pmc_profile: ProfileModel

    hideout: Hideout

    quests: quests.Quests
    quests_data: List[dict]

    inventory: inventory_.PlayerInventory
    encyclopedia: Encyclopedia

    notifier: Mail

    def __init__(self, profile_id: str):
        self.profile_id = profile_id

        self.profile_dir = root_dir.joinpath('resources', 'profiles', profile_id)

        self.pmc_profile_path = self.profile_dir.joinpath('pmc_profile.json')

        self.quests_path = self.profile_dir.joinpath('pmc_quests.json')

    @staticmethod
    def exists(profile_id: str):
        return root_dir.joinpath('resources', 'profiles', profile_id).exists() and profile_id

    def get_profile(self) -> dict:
        profile_data = {}
        for file in self.profile_dir.glob('pmc_*.json'):
            profile_data[file.stem] = ujson.load(file.open('r', encoding='utf8'))

        profile_base = self.pmc_profile.copy()
        profile_base.Hideout = self.hideout.data
        # profile_base['Inventory'] = self.inventory.inventory.dict()
        profile_base.Quests = profile_data['pmc_quests']
        profile_base.Stats = profile_data['pmc_stats']

        return profile_base.dict(exclude_none=True)

    def add_insurance(self, item: Item, trader: TraderType):
        self.pmc_profile.InsuredItems.append(ItemInsurance(
            item_id=item.id,
            trader_id=trader.value
        ))

        #  Todo remove insurance from items that aren't present in inventory after raid

    def receive_experience(self, amount: int):
        self.pmc_profile.Info.Experience += amount

    def __read(self):
        self.pmc_profile: ProfileModel = ProfileModel.parse_file(self.pmc_profile_path)

        # self.pmc_profile: dict = ujson.load(self.pmc_profile_path.open('r', encoding='utf8'))

        self.encyclopedia = Encyclopedia(profile=self)

        self.inventory = tarkov.inventory.PlayerInventory(profile=self)
        self.inventory.read()

        self.quests_data: List[dict] = ujson.load(self.quests_path.open('r', encoding='utf8'))
        self.quests = quests.Quests(profile=self)

        self.hideout = Hideout(profile=self)
        self.hideout.read()

        self.notifier = Mail(profile=self)
        self.notifier.read()

    def __write(self):
        atomic_write(self.pmc_profile.json(exclude_defaults=True), self.pmc_profile_path)
        #
        self.inventory.write()
        self.hideout.write()
        #
        atomic_write(ujson.dumps(self.quests_data, indent=4), self.quests_path)
        #
        self.notifier.write()

    def __enter__(self):
        self.__read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.__write()
