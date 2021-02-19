from typing import Any, Dict, List, Optional

from pydantic import Extra, Field, StrictBool, StrictInt, root_validator
from werkzeug.routing import ValidationError

from server import root_dir
from tarkov.inventory.models import InventoryModel
from tarkov.inventory.types import TemplateId
from tarkov.models import Base
from tarkov.trader.models import ItemInsurance, TraderStanding


class OfflineRaidSettings(Base):
    Role: str
    BotDifficulty: str
    Experience: StrictInt


class ProfileInfo(Base):
    Nickname: str
    LowerNickname: str
    Side: str
    Voice: str
    Level: int
    Experience: int
    RegistrationDate: int
    GameVersion: str
    AccountType: int
    MemberCategory: str = "UniqueId"
    lockedMoveCommands: StrictBool = False
    SavageLockTime: int
    LastTimePlayedAsSavage: int
    Settings: OfflineRaidSettings
    NeedWipe: StrictBool
    GlobalWipe: StrictBool
    NicknameChangeDate: int
    Bans: list = Field(default_factory=list)


class ProfileCustomization(Base):
    Head: str
    Body: str
    Hands: str
    Feet: str


class SkillCommon(Base):
    Id: str
    Progress: float
    PointsEarnedDuringSession: float
    LastAccess: int


class SkillMastering(Base):
    Id: str
    Progress: float


class Skills(Base):
    Common: List[SkillCommon]
    Mastering: List[SkillMastering]
    Bonuses: Any
    Points: int = 0


class Counter(Base):
    id: str
    value: int


class _ConditionCounters(Base):
    Counters: List[Counter] = Field(default_factory=list)


class BackendCounter(Base):
    id: Optional[str]
    qid: Optional[str]
    value: int


class ProfileModel(Base):
    class Config:
        extra = Extra.allow
        exclude = {
            "Inventory",
        }

    id: str = Field(alias="_id")
    aid: str
    savage: str
    Info: ProfileInfo

    Customization: ProfileCustomization
    Inventory: InventoryModel
    Skills: Skills
    Stats: Dict

    Encyclopedia: Dict[TemplateId, StrictBool] = Field(default_factory=dict)
    ConditionCounters: _ConditionCounters = Field(default_factory=_ConditionCounters)
    BackendCounters: Dict[str, BackendCounter] = Field(
        default_factory=dict
    )  # Dict key is the same as counter id
    InsuredItems: List[ItemInsurance] = Field(default_factory=list)
    Hideout: dict
    Bonuses: list
    Notes: dict
    TraderStandings: Dict[str, TraderStanding]
    Quests: list
    WishList: list

    @root_validator(pre=True)
    def collect_files(cls, values: dict) -> dict:  # pylint: disable=no-self-argument,no-self-use
        profile_id = values.get("aid", None)
        if not profile_id:
            raise ValidationError("Profile has no aid property")

        if "Inventory" not in values or not values["Inventory"]:
            inventory_path = root_dir.joinpath("resources", "profiles", profile_id, "pmc_inventory.json")
            values["Inventory"] = InventoryModel.parse_file(inventory_path)
        return values

    def json(self, *args: Any, **kwargs: Any) -> str:
        if kwargs.get("exclude", None) is None:
            kwargs["exclude"] = self.Config.exclude

        return super().json(*args, **kwargs)
