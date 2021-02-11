from typing import Dict

from pydantic import Extra, Field, StrictBool, StrictInt, root_validator

from server import root_dir
from tarkov.inventory.models import InventoryModel, TemplateId
from tarkov.models import Base


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


class ProfileModel(Base):
    class Config:
        extra = Extra.allow

    id: str = Field(alias='_id')
    aid: str
    savage: str
    Info: ProfileInfo

    Customization: ProfileCustomization
    Inventory: InventoryModel
    Skills: dict
    Stats: Dict

    Encyclopedia: Dict[TemplateId, StrictBool] = Field(default_factory=dict)
    ConditionCounters: dict
    BackendCounters: dict
    InsuredItems: list
    Hideout: dict
    Bonuses: list
    Notes: dict
    TraderStandings: dict
    Quests: list
    WishList: list  # TODO

    @root_validator(pre=True)
    def collect_files(cls, values):  # pylint: disable=no-self-argument,no-self-use
        if 'Inventory' not in values or not values['Inventory']:
            inventory_path = root_dir.joinpath('resources', 'profiles', values.get('aid'), 'pmc_inventory.json')
            values['Inventory'] = InventoryModel.parse_file(inventory_path)
        return values
