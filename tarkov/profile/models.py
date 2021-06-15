from typing import Any, Dict, List, Optional

from pydantic import Extra, Field, StrictBool, StrictInt

from tarkov.fleamarket.models import Offer
from tarkov.inventory.models import InventoryModel
from tarkov.inventory.types import TemplateId
from tarkov.models import Base
from tarkov.quests.models import Quest
from tarkov.trader.models import ItemInsurance, TraderStanding


class OfflineRaidSettings(Base):
    Role: str
    BotDifficulty: str
    Experience: StrictInt


class ProfileInfo(Base):
    class Config:
        extra = Extra.ignore

    Nickname: str
    LowerNickname: str
    Side: str
    Voice: str
    Level: int
    Experience: int
    RegistrationDate: int
    GameVersion: str
    AccountType: int = 2
    MemberCategory: str = "UniqueId"
    lockedMoveCommands: StrictBool = False
    SavageLockTime: int
    LastTimePlayedAsSavage: int
    Settings: OfflineRaidSettings
    NeedWipe: StrictBool = False
    GlobalWipe: StrictBool = False
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


class ConditionCounters(Base):
    Counters: List[Counter] = Field(default_factory=list)


class BackendCounter(Base):
    id: Optional[str]
    qid: Optional[str]
    value: int


class RagfairInfo(Base):
    rating: float
    isRatingGrowing: bool
    offers: List[Offer]


class ProfileModel(Base):
    class Config:
        extra = Extra.allow

    id: str = Field(alias="_id")
    aid: str
    savage: str
    Info: ProfileInfo

    Customization: ProfileCustomization
    Inventory: InventoryModel
    Skills: Skills
    Stats: dict

    Encyclopedia: Dict[TemplateId, StrictBool] = Field(default_factory=dict)
    ConditionCounters_: ConditionCounters = Field(
        default_factory=ConditionCounters, alias="ConditionCounters"
    )
    BackendCounters: Dict[str, BackendCounter] = Field(
        default_factory=dict
    )  # Dict key is the same as counter id
    InsuredItems: List[ItemInsurance] = Field(default_factory=list)
    Hideout: dict
    Bonuses: list
    Notes: dict
    TraderStandings: Dict[str, TraderStanding]
    Quests: List[Quest]
    WishList: list
    RagfairInfo: RagfairInfo
    Health: dict
