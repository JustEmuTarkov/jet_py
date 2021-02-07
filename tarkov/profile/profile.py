from __future__ import annotations

import copy
from typing import List, Union

import ujson
from flask import Request

import tarkov.inventory.repositories
from server import root_dir
from server.utils import TarkovError
from tarkov import inventory as inventory_, quests, notifier
from tarkov.hideout import Hideout
from tarkov.lib.trader import Traders


class Encyclopedia:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.data = profile.pmc_profile['Encyclopedia']

    def examine(self, item: Union[inventory_.Item, inventory_.TemplateId]):
        if isinstance(item, inventory_.Item):
            self.data[item.id] = False

        else:
            item_template_id = item
            self.data[item_template_id] = False

    def read(self, item: Union[inventory_.Item, inventory_.TemplateId]):
        if isinstance(item, inventory_.Item):
            item_tpl_id = item.tpl
        else:
            item_tpl_id = item

        self.data[item_tpl_id] = True


class Profile:
    pmc_profile: dict

    hideout: Hideout

    quests: quests.Quests
    quests_data: List[dict]

    inventory: inventory_.PlayerInventory
    encyclopedia: Encyclopedia

    notifier: notifier.Mail

    def __init__(self, profile_id: str):
        self.profile_id = profile_id

        self.profile_dir = root_dir.joinpath('resources', 'profiles', profile_id)

        self.pmc_profile_path = self.profile_dir.joinpath('pmc_profile.json')

        self.quests_path = self.profile_dir.joinpath('pmc_quests.json')

    @staticmethod
    def from_request(request: Request) -> Profile:
        if not request.cookies['PHPSESSID']:
            raise TarkovError(err=401, errmsg='PHPSESSID cookie was not provided')

        profile_id = request.cookies['PHPSESSID']
        return Profile(profile_id=profile_id)

    def get_profile(self) -> dict:
        profile_data = {}
        for file in self.profile_dir.glob('pmc_*.json'):
            profile_data[file.stem] = ujson.load(file.open('r', encoding='utf8'))

        profile_base = copy.deepcopy(self.pmc_profile)
        profile_base['Hideout'] = self.hideout.data
        profile_base['Inventory'] = self.inventory.inventory.dict()
        profile_base['Quests'] = profile_data['pmc_quests']
        profile_base['Stats'] = profile_data['pmc_stats']
        profile_base['TraderStandings'] = profile_data['pmc_traders']

        return profile_base

    def add_insurance(self, item: inventory_.Item, trader: Traders):
        insurance_info = {
            'itemId': item.id,
            'tid': trader.value
        }
        self.pmc_profile['InsuredItems'].append(insurance_info)

        #  Todo remove insurance from items that aren't present in inventory after raid

    def __read(self):
        self.pmc_profile: dict = ujson.load(self.pmc_profile_path.open('r', encoding='utf8'))

        self.encyclopedia = Encyclopedia(profile=self)

        self.inventory = tarkov.inventory.PlayerInventory(profile=self)
        self.inventory.read()

        self.quests_data: List[dict] = ujson.load(self.quests_path.open('r', encoding='utf8'))
        self.quests = quests.Quests(profile=self)

        self.hideout = Hideout(profile=self)
        self.hideout.read()

        self.notifier = notifier.Mail(profile=self)
        self.notifier.read()

    def __write(self):
        ujson.dump(self.pmc_profile, self.pmc_profile_path.open('w', encoding='utf8'), indent=4)

        self.inventory.write()
        self.hideout.write()

        ujson.dump(self.quests_data, self.quests_path.open('w', encoding='utf8'), indent=4)

        self.notifier.write()

    def __enter__(self):
        self.__read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.__write()
