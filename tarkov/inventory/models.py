from __future__ import annotations

import datetime
import enum
from typing import Any, List, Literal, NewType, Optional, TYPE_CHECKING, Union, cast

from pydantic import Extra, Field, PrivateAttr, StrictBool, StrictInt, root_validator

import tarkov.inventory
from tarkov.models import Base

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory import MutableInventory

ItemId = NewType('ItemId', str)
TemplateId = NewType('TemplateId', str)


class ItemTemplateProps(Base):
    class Config:
        extra = Extra.allow
        allow_mutation = False

    Name: str
    ShortName: str
    Description: str
    Weight: float
    Width: StrictInt
    Height: StrictInt
    StackMaxSize: StrictInt
    Rarity: Literal['Not_exist', 'Common', 'Rare', 'Superrare']
    SpawnChance: float
    CreditsPrice: float
    ItemSound: str
    StackObjectsCount: StrictInt
    NotShownInSlot: StrictBool
    ExaminedByDefault: StrictBool
    ExamineTime: float

    IsUndiscardable: StrictBool
    IsUnsaleable: StrictBool
    IsUnbuyable: StrictBool
    IsUngivable: StrictBool
    IsLockedafterEquip: StrictBool
    QuestItem: StrictBool

    LootExperience: StrictInt
    ExamineExperience: StrictInt
    HideEntrails: StrictBool
    RepairCost: float
    RepairSpeed: float
    ExtraSizeLeft: StrictInt
    ExtraSizeRight: StrictInt
    ExtraSizeUp: StrictInt
    ExtraSizeDown: StrictInt
    ExtraSizeForceAdd: StrictBool

    MergesWithChildren: StrictBool
    CanSellOnRagfair: StrictBool
    CanRequireOnRagfair: StrictBool
    BannedFromRagfair: StrictBool
    ConflictingItems: List[str]
    FixedPrice: StrictBool
    Unlootable: StrictBool
    UnlootableFromSlot: str

    # UnlootableFromSide: []

    ChangePriceCoef: float
    # AllowSpawnOnLocations": [],
    # "SendToClient": false,
    # "AnimationVariantsNumber": 0,
    # "DiscardingBlock": false,

    StackMinRandom: Optional[StrictInt] = None
    StackMaxRandom: Optional[StrictInt] = None

    medUseTime: Optional[StrictInt]
    medEffectType: Optional[str]
    MaxHpResource: Optional[StrictInt]
    hpResourceRate: Optional[StrictInt]

    Foldable: StrictBool = False

    Grids: Optional[List[ItemGrid]] = None
    SpawnFilter: Optional[List[TemplateId]] = None
    Cartridges: Optional[List[Cartridges]] = None
    # "ammoType": "bullet",
    # "Damage": 67,
    # "ammoAccr": 0,
    # "ammoRec": 0,
    # "ammoDist": 0,
    # "buckshotBullets": 0,
    # "PenetrationPower": 1,
    # "PenetrationPowerDiviation": 0,
    # "ammoHear": 0,
    # "ammoSfx": "standart",
    # "MisfireChance": 0.01,
    # "MinFragmentsCount": 1,
    # "MaxFragmentsCount": 2,
    # "ammoShiftChance": 0,
    # "casingName": "",
    # "casingEjectPower": 1,
    # "casingMass": 10,
    # "casingSounds": "pistol_small",
    # "ProjectileCount": 1,
    # "InitialSpeed": 250,
    # "PenetrationChance": 0.01,
    # "RicochetChance": 0.05,
    # "FragmentationChance": 0.6,
    # "BallisticCoeficient": 1,
    # "Deterioration": 1,
    # "SpeedRetardation": 0.00007,
    # "Tracer": false,
    # "TracerColor": "red",
    # "TracerDistance": 0,
    # "ArmorDamage": 2,
    # "Caliber": "Caliber9x18PM",
    # "StaminaBurnPerDamage": 0.7,
    # "ShowBullet": false,
    # "HasGrenaderComponent": false,
    # "FuzeArmTimeSec": 0,
    # "ExplosionStrength": 0,
    # "MinExplosionDistance": 0,
    # "MaxExplosionDistance": 0,
    # "FragmentsCount": 0,
    # "FragmentType": "5996f6d686f77467977ba6cc",
    # "ShowHitEffectOnExplode": false,
    # "ExplosionType": "",
    # "AmmoLifeTimeSec": 5,
    # "Contusion": {
    #     "x": 0,
    #     "y": 0,
    #     "z": 0
    # },
    # "ArmorDistanceDistanceDamage": {
    #     "x": 0,
    #     "y": 0,
    #     "z": 0
    # },
    # "Blindness": {
    #     "x": 0,
    #     "y": 0,
    #     "z": 0
    # },
    # "IsLightAndSoundShot": false,
    # "LightAndSoundShotAngle": 0,
    # "LightAndSoundShotSelfContusionTime": 0,
    # "LightAndSoundShotSelfContusionStrength": 0
    # "Prefab": {
    #     "path": "assets/content/items/ammo/patrons/patron_9x18pm
    #             "rcid": ""
    # },
    # "UsePrefab": {
    #     "path": "",
    #     "rcid": ""
    # },
    # "BackgroundColor": "yellow",


class NodeTemplateBase(Base):
    class Config:
        extra = Extra.allow

        allow_mutation = False
        fields = {
            'id': '_id',
            'name': '_name',
            'parent': '_parent',
            'type': '_type',
            'props': '_props',
            'proto': '_proto'
        }

    id: TemplateId
    name: str
    parent: str
    proto: Optional[str] = None


class NodeTemplate(NodeTemplateBase):
    type: Literal['Node']


class FilterProp(Base):
    Filter: List[str] = Field(default_factory=list)
    ExcludedFilter: List[str] = Field(default_factory=list)


class CartridgesProps(Base):
    filters: List[FilterProp]


class Cartridges(Base):
    class Config:
        allow_mutation = False
        fields = {
            'name': '_name',
            'id': '_id',
            'parent': '_parent',
            'max_count': '_max_count',
            'props': '_props',
            'proto': '_proto'
        }

    name: Literal['cartridges']
    id: TemplateId
    parent: TemplateId
    max_count: StrictInt
    props: CartridgesProps
    proto: str


class GridProps(Base):
    class Config:
        allow_mutation = False
        fields = {
            'width': 'cellsH',
            'height': 'cellsV'
        }

    filters: List[FilterProp]
    width: StrictInt
    height: StrictInt
    minCount: StrictInt
    maxCount: StrictInt
    maxWeight: StrictInt


class ItemGrid(NodeTemplate):
    type: Optional[str] = None  # type: ignore
    props: GridProps


ItemTemplateProps.update_forward_refs()


class ItemTemplate(NodeTemplateBase):
    type: Literal['Item']
    props: ItemTemplateProps


class ItemUpdDogtag(Base):
    AccountId: str
    ProfileId: str
    Nickname: str
    Side: str
    Level: int
    Time: datetime.datetime
    Status: str
    KillerAccountId: str
    KillerProfileId: str
    KillerName: str
    WeaponName: str


class ItemUpdTag(Base):
    Name: str
    Color: int


class ItemUpdTogglable(Base):
    On: bool


class ItemUpdFaceShield(Base):
    Hits: int
    HitSeed: int


class ItemUpdLockable(Base):
    Locked: bool


class ItemUpdRepairable(Base):
    MaxDurability: Optional[int] = None  # TODO: Some items in bot inventories don't have MaxDurability
    Durability: int


class ItemUpdFoldable(Base):
    Folded: bool


class ItemUpdFireMode(Base):
    FireMode: str


class ItemUpdResource(Base):
    Value: Union[int, float]


class ItemUpdFoodDrink(Base):
    HpPercent: int


class ItemUpdKey(Base):
    NumberOfUsages: int


class ItemUpdMedKit(Base):
    HpResource: int


class ItemUpd(Base):
    StackObjectsCount: int = 1
    SpawnedInSession: bool = False
    Repairable: Optional[ItemUpdRepairable] = None
    Foldable: Optional[ItemUpdFoldable] = None
    FireMode: Optional[ItemUpdFireMode] = None
    Resource: Optional[ItemUpdResource] = None
    FoodDrink: Optional[ItemUpdFoodDrink] = None
    Key: Optional[ItemUpdKey] = None
    MedKit: Optional[ItemUpdMedKit] = None
    Lockable: Optional[ItemUpdLockable] = None
    Sight: Optional[Any] = None
    Light: Optional[Any] = None
    FaceShield: Optional[ItemUpdFaceShield] = None
    Togglable: Optional[ItemUpdTogglable] = None
    Tag: Optional[ItemUpdTag] = None
    Dogtag: Optional[ItemUpdDogtag] = None
    UnlimitedCount: StrictBool = False


ItemAmmoStackPosition = NewType('ItemAmmoStackPosition', int)

ItemOrientation = Literal['Horizontal', 'Vertical']


class ItemOrientationEnum(enum.Enum):
    Horizontal = 'Horizontal'
    Vertical = 'Vertical'


class ItemInventoryLocation(Base):
    x: int
    y: int
    r: str = ItemOrientationEnum.Vertical.value
    isSearched: Optional[bool] = None


AnyItemLocation = Union[ItemInventoryLocation, ItemAmmoStackPosition]


class Item(Base):
    class Config:
        extra = Extra.forbid
        fields = {
            'id': '_id',
            'tpl': '_tpl',
            'parent_id': 'parentId'
        }

    __inventory__: Optional['MutableInventory'] = PrivateAttr(default=None)  # Link to the inventory

    id: ItemId
    tpl: TemplateId
    slotId: Optional[str] = None
    parent_id: Optional[ItemId] = None
    location: Optional[AnyItemLocation] = None
    upd: ItemUpd = Field(default_factory=ItemUpd)

    def get_inventory(self) -> 'MutableInventory':
        if self.__inventory__ is None:
            raise ValueError('Item does not have inventory')
        return self.__inventory__

    @root_validator(pre=False, skip_on_failure=True)
    def validate_medkit_hp(cls, values: dict):  # pylint: disable=no-self-argument,no-self-use
        if 'id' not in values:
            return values

        item_tpl_id: TemplateId = cast(TemplateId, values.get('tpl'))
        item_template = tarkov.inventory.item_templates_repository.get_template(item_tpl_id)
        if item_template.parent == '5448f39d4bdc2d0a728b4568':
            upd: ItemUpd = cast(ItemUpd, values.get('upd'))
            if not isinstance(item_template.props.MaxHpResource, int):
                raise ResourceWarning(
                    f'''Item template that inherits directly form MedKit does not have MaxHpResource property
                    template id: {item_template.id}
                    ''')
            upd.MedKit = upd.MedKit if upd.MedKit else ItemUpdMedKit(HpResource=item_template.props.MaxHpResource)

        return values

    def copy(
            self: Item,
            **kwargs
    ) -> Item:
        item_inventory = self.__inventory__
        # Avoid copying inventory
        self.__inventory__ = None
        item_copy: Item = super().copy(**kwargs)

        self.__inventory__ = item_inventory

        return item_copy


class InventoryModel(Base):
    equipment: ItemId
    stash: ItemId
    questRaidItems: ItemId
    questStashItems: ItemId
    fastPanel: dict
    items: List[Item]


class InventoryMoveLocation(Base):
    id: ItemId
    container: str
    location: ItemInventoryLocation


class CartridgesMoveLocation(Base):
    id: ItemId  # Magazine id
    container: Literal['cartridges']


class PatronInWeaponMoveLocation(Base):
    id: ItemId
    container: Literal['patron_in_weapon']


class ModMoveLocation(Base):
    id: ItemId
    container: str
    # container: Literal[
    #     'mod_handguard',
    #     'mod_muzzle',
    #     'mod_gas_block',
    #     'mod_mount',
    #     'mod_scope',
    #     'mod_sight_rear',
    #     'mod_sight_front',
    #     'mod_tactical',
    #     'mod_barrel',
    #     'mod_pistol_grip',
    #     'mod_magazine',
    #     'mod_reciever',
    #     'mod_stock',
    #     'mod_charge',
    #     'mod_mount_001',
    #     'mod_mount_002',
    #     'mod_foregrip'
    # ]


AnyMoveLocation = Union[InventoryMoveLocation, CartridgesMoveLocation, PatronInWeaponMoveLocation, ModMoveLocation]
