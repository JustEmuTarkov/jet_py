from __future__ import annotations

from pathlib import Path
from typing import Callable

from server.utils import atomic_write
from tarkov.hideout.main import Hideout
from tarkov.inventory.inventory import PlayerInventory
from tarkov.inventory.models import Item
from tarkov.mail.mail import Mail
from tarkov.notifier.notifier import NotifierService
from tarkov.quests.quests import Quests
from tarkov.trader.models import TraderType
from .encyclopedia import Encyclopedia
from .models import ItemInsurance, ProfileModel


class Profile:
    class ProfileDoesNotExistsError(Exception):
        pass

    pmc: ProfileModel
    scav: ProfileModel

    hideout: Hideout
    quests: Quests
    inventory: PlayerInventory
    encyclopedia: Encyclopedia
    mail: Mail

    def __init__(
        self,
        profile_dir: Path,
        profile_id: str,
        encyclopedia_factory: Callable[..., Encyclopedia],
        hideout_factory: Callable[..., Hideout],
        quests_factory: Callable[..., Quests],
        notifier_service: NotifierService,
    ):
        self.__encyclopedia_factory = encyclopedia_factory
        self.__hideout_factory = hideout_factory
        self.__quests_factory = quests_factory
        self.__notifier_service = notifier_service

        self.profile_dir = profile_dir
        self.profile_id = profile_id

        self.pmc_profile_path = self.profile_dir.joinpath("pmc_profile.json")
        self.scav_profile_path = self.profile_dir.joinpath("scav_profile.json")

    def add_insurance(self, item: Item, trader: TraderType) -> None:
        # TODO: Move this function into IInsuranceService
        self.pmc.InsuredItems.append(
            ItemInsurance(item_id=item.id, trader_id=trader.value)
        )

    def receive_experience(self, amount: int) -> None:
        self.pmc.Info.Experience += amount

    def read(self) -> None:
        if any(
            not path.exists()
            for path in (self.pmc_profile_path, self.scav_profile_path)
        ):
            raise Profile.ProfileDoesNotExistsError

        self.pmc = ProfileModel.parse_file(self.pmc_profile_path)
        self.scav = ProfileModel.parse_file(self.scav_profile_path)

        self.encyclopedia = self.__encyclopedia_factory(profile=self)
        self.inventory = PlayerInventory(profile=self)
        self.inventory.read()

        self.quests = self.__quests_factory(profile=self)

        self.hideout = self.__hideout_factory(profile=self)
        self.hideout.read()

        self.mail = Mail(profile=self, notifier_service=self.__notifier_service)
        self.mail.read()

    def write(self) -> None:
        self.hideout.write()
        self.mail.write()
        self.inventory.write()

        atomic_write(self.pmc.json(exclude_defaults=True), self.pmc_profile_path)
        atomic_write(self.scav.json(exclude_defaults=True), self.scav_profile_path)

    def update(self) -> None:
        self.hideout.update()
