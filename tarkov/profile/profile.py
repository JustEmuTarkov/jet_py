from __future__ import annotations

from typing import TYPE_CHECKING, Union

from dependency_injector.wiring import Provide, inject

from server import root_dir
from server.container import AppContainer
from server.utils import atomic_write
from tarkov.hideout import Hideout
from tarkov.inventory.inventory import PlayerInventory
from tarkov.inventory.models import Item, ItemTemplate
from tarkov.inventory.types import TemplateId
from tarkov.mail import Mail
from tarkov.notifier.notifier import NotifierService
from tarkov.quests.quests import Quests
from tarkov.trader.models import TraderType
from .models import ItemInsurance, ProfileModel

if TYPE_CHECKING:
    from tarkov.inventory.repositories import ItemTemplatesRepository


class Encyclopedia:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.data = profile.pmc.Encyclopedia

    @inject
    def examine(
        self,
        item: Union[Item, TemplateId],
        templates_repository: ItemTemplatesRepository = Provide[
            AppContainer.repos.templates
        ],
    ) -> None:
        template: ItemTemplate = templates_repository.get_template(item)
        self.data[template.id] = False
        self.profile.receive_experience(template.props.ExamineExperience)

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

    pmc: ProfileModel
    scav: ProfileModel

    hideout: Hideout
    quests: Quests
    inventory: PlayerInventory
    encyclopedia: Encyclopedia
    mail: Mail

    def __init__(self, profile_id: str):
        self.profile_id = profile_id

        self.profile_dir = root_dir.joinpath("resources", "profiles", profile_id)

        self.pmc_profile_path = self.profile_dir.joinpath("pmc_profile.json")
        self.scav_profile_path = self.profile_dir.joinpath("scav_profile.json")

    def add_insurance(self, item: Item, trader: TraderType) -> None:
        self.pmc.InsuredItems.append(
            ItemInsurance(item_id=item.id, trader_id=trader.value)
        )

        #  Todo remove insurance from items that aren't present in inventory after raid

    def receive_experience(self, amount: int) -> None:
        self.pmc.Info.Experience += amount

    @inject
    def read(
        self, notifier_service: NotifierService = Provide[AppContainer.notifier.service]
    ) -> None:
        if any(
            not path.exists()
            for path in (self.pmc_profile_path, self.scav_profile_path)
        ):
            raise Profile.ProfileDoesNotExistsError

        self.pmc = ProfileModel.parse_file(self.pmc_profile_path)
        self.scav = ProfileModel.parse_file(self.scav_profile_path)

        self.encyclopedia = Encyclopedia(profile=self)
        self.inventory = PlayerInventory(profile=self)
        self.inventory.read()

        self.quests = Quests(profile=self)

        self.hideout = Hideout(profile=self)
        self.hideout.read()

        self.mail = Mail(self, notifier_service)
        self.mail.read()

    def write(self) -> None:
        self.hideout.write()
        self.mail.write()
        self.inventory.write()

        atomic_write(self.pmc.json(exclude_defaults=True), self.pmc_profile_path)
        atomic_write(self.scav.json(exclude_defaults=True), self.scav_profile_path)

    def update(self) -> None:
        self.hideout.update()
