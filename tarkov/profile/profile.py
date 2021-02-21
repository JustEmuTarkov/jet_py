from __future__ import annotations

from types import TracebackType
from typing import List, Optional, Union

import ujson
from typing_extensions import Type

import tarkov.inventory.repositories
from server import root_dir
from server.utils import atomic_write
from tarkov import inventory as inventory_, quests
from tarkov.hideout import Hideout
from tarkov.inventory.models import Item
from tarkov.inventory.types import TemplateId
from tarkov.mail import Mail
from tarkov.trader import TraderType
from .models import ItemInsurance, ProfileModel


class Encyclopedia:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.data = profile.pmc_profile.Encyclopedia

    def examine(self, item: Union[Item, TemplateId]) -> None:
        if isinstance(item, Item):
            self.data[item.tpl] = False

        else:
            item_template_id = item
            self.data[item_template_id] = False

    def read(self, item: Union[Item, TemplateId]) -> None:
        if isinstance(item, Item):
            item_tpl_id = item.tpl
        else:
            item_tpl_id = item

        self.data[item_tpl_id] = True


class Profile:
    # pylint: disable=too-many-instance-attributes
    # Disabling that in case of profile is reasonable

    class ProfileDoesNotExistsError(Exception):
        pass

    pmc_profile: ProfileModel

    hideout: Hideout

    quests: quests.Quests
    quests_data: List[dict]

    inventory: inventory_.PlayerInventory
    encyclopedia: Encyclopedia

    mail: Mail

    def __init__(self, profile_id: str):
        self.profile_id = profile_id

        self.profile_dir = root_dir.joinpath("resources", "profiles", profile_id)

        self.pmc_profile_path = self.profile_dir.joinpath("pmc_profile.json")

    @staticmethod
    def exists(profile_id: str) -> bool:
        return root_dir.joinpath("resources", "profiles", profile_id).exists()

    def get_profile(self) -> dict:
        profile_data = {}
        for file in self.profile_dir.glob("pmc_*.json"):
            profile_data[file.stem] = ujson.load(file.open("r", encoding="utf8"))

        profile_base = self.pmc_profile.copy()

        return profile_base.dict(exclude_none=True)

    def add_insurance(self, item: Item, trader: TraderType) -> None:
        self.pmc_profile.InsuredItems.append(ItemInsurance(item_id=item.id, trader_id=trader.value))

        #  Todo remove insurance from items that aren't present in inventory after raid

    def receive_experience(self, amount: int) -> None:
        self.pmc_profile.Info.Experience += amount

    def __read(self) -> None:
        if not self.profile_dir.exists():
            raise Profile.ProfileDoesNotExistsError
        self.pmc_profile: ProfileModel = ProfileModel.parse_file(self.pmc_profile_path)

        self.encyclopedia = Encyclopedia(profile=self)
        self.inventory = tarkov.inventory.PlayerInventory(profile=self)
        self.quests = quests.Quests(profile=self)

        self.hideout = Hideout(profile=self)
        self.hideout.read()

        self.mail = Mail(profile=self)
        self.mail.read()

    def __write(self) -> None:
        atomic_write(self.pmc_profile.json(exclude_defaults=True), self.pmc_profile_path)
        self.hideout.write()
        self.mail.write()

    def __enter__(self) -> Profile:
        self.__read()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if exc_type is None:
            self.__write()
