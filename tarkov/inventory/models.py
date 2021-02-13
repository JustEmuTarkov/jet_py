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
        # extra = Extra.allow
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
    AllowSpawnOnLocations: List[Literal['laboratory', 'Shoreline', 'Interchange', 'RezervBase', 'bigmap', 'Woods']]
    # "SendToClient": false,
    # "AnimationVariantsNumber": 0,
    # "DiscardingBlock": false,
    ammoDist: Optional[StrictInt]
    ammoAccr: Optional[StrictInt]
    ammoHear: Optional[StrictInt]
    ammoRec: Optional[StrictInt]
    ammoSfx: Optional[str]
    ammoShiftChance: Optional[StrictInt]
    ammoType: Optional[str]
    ammoCaliber: Optional[str]
    StackSlots: Optional[list]
    Slots: Optional[list]
    buckshotBullets: Optional[StrictInt]
    casingEjectPower: Optional[StrictInt]
    casingMass: Optional[float]
    casingSounds: Optional[str]
    casingName: Optional[str]

    AmmoLifeTimeSec: Optional[StrictInt]
    AnimationVariantsNumber: Optional[StrictInt]
    ArmorDamage: Optional[StrictInt]
    ArmorDistanceDistanceDamage: Optional[dict]
    BallisticCoeficient: Optional[float]
    Blindness: Optional[dict]
    Contusion: Optional[dict]
    Caliber: Optional[str]
    Damage: Optional[StrictInt]
    Deterioration: Optional[StrictInt]
    DiscardingBlock: StrictBool
    ExplosionStrength: Optional[StrictInt]
    ExplosionType: Optional[str]
    FragmentType: Optional[TemplateId]
    FragmentationChance: Optional[float]
    FragmentsCount: Optional[int]
    FuzeArmTimeSec: Optional[float]
    HasGrenaderComponent: Optional[StrictBool]
    InitialSpeed: Optional[float]
    IsLightAndSoundShot: Optional[StrictBool]
    LightAndSoundShotAngle: Optional[StrictInt]
    LightAndSoundShotSelfContusionStrength: Optional[float]
    LightAndSoundShotSelfContusionTime: Optional[StrictInt]
    MaxExplosionDistance: Optional[StrictInt]
    MinFragmentsCount: Optional[StrictInt]
    MaxFragmentsCount: Optional[StrictInt]
    MinExplosionDistance: Optional[float]
    MisfireChance: Optional[float]
    PenetrationChance: Optional[float]
    PenetrationPower: Optional[StrictInt]
    PenetrationPowerDiviation: Optional[float]
    ProjectileCount: Optional[StrictInt]
    RicochetChance: Optional[float]
    SendToClient: Optional[StrictBool]
    ShowBullet: Optional[StrictBool]
    ShowHitEffectOnExplode: Optional[StrictBool]
    SpeedRetardation: Optional[float]
    StaminaBurnPerDamage: Optional[float]
    Tracer: Optional[StrictBool]
    TracerColor: Optional[TracerColor]
    TracerDistance: Optional[float]
    Prefab: dict
    UsePrefab: dict

    BackgroundColor: Color

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

    CantRemoveFromSlotsDuringRaid: Optional[list]
    UnlootableFromSide: list

    BlocksEarpiece: Optional[StrictBool]
    BlocksEyewear: Optional[StrictBool]
    BlocksFaceCover: Optional[StrictBool]
    BlocksHeadwear: Optional[StrictBool]
    CanPutIntoDuringTheRaid: Optional[StrictBool]

    ArmorMaterial: Optional[str]
    BluntThroughput: Optional[float]
    DeafStrength: Optional[str]
    Durability: Optional[StrictInt]
    FaceShieldComponent: Optional[StrictBool]
    FaceShieldMask: Optional[str]
    HasHinge: Optional[StrictBool]
    Indestructibility: Optional[float]
    MaterialType: Optional[str]
    MaxDurability: Optional[StrictInt]
    RicochetParams: Optional[dict]
    armorClass: Optional[str]
    armorZone: Optional[List[str]]
    headSegments: Optional[List[str]]
    mousePenalty: Optional[StrictInt]
    speedPenaltyPercent: Optional[StrictInt]
    weaponErgonomicPenalty: Optional[StrictInt]

    IsSilencer: Optional[StrictBool]

    BlocksArmorVest: Optional[StrictBool]
    GridLayoutName: Optional[str]
    SearchSound: Optional[str]

    AimPlane: Optional[float]
    BoltAction: Optional[StrictBool]
    CameraRecoil: Optional[float]
    CameraSnap: Optional[float]
    CenterOfImpact: Optional[float]
    Chambers: Optional[List]
    CompactHandling: Optional[StrictBool]
    Convergence: Optional[float]
    DeviationCurve: Optional[StrictInt]
    DeviationMax: Optional[StrictInt]
    Ergonomics: Optional[Union[StrictInt, float]]
    FoldedSlot: Optional[str]
    HipAccuracyRestorationDelay: Optional[float]
    HipAccuracyRestorationSpeed: Optional[StrictInt]
    HipInnaccuracyGain: Optional[float]
    IronSightRange: Optional[StrictInt]
    ManualBoltCatch: Optional[StrictBool]
    MustBoltBeOpennedForExternalReload: Optional[StrictBool]
    MustBoltBeOpennedForInternalReload: Optional[StrictBool]
    OperatingResource: Optional[StrictInt]
    RecoilAngle: Optional[StrictInt]
    RecoilCenter: Optional[dict]
    RecoilForceBack: Optional[StrictInt]
    MaxRepairDegradation: Optional[float]
    MinRepairDegradation: Optional[float]
    RecoilForceUp: Optional[StrictInt]
    RecolDispersion: Optional[StrictInt]
    ReloadMode: Optional[str]
    RepairComplexity: Optional[StrictInt]
    Retractable: Optional[StrictBool]
    RotationCenter: Optional[dict]
    RotationCenterNoStock: Optional[dict]
    SightingRange: Optional[StrictInt]
    SizeReduceRight: Optional[StrictInt]
    TacticalReloadFixation: Optional[float]
    TacticalReloadStiffnes: Optional[dict]
    Velocity: Optional[float]
    bEffDist: Optional[StrictInt]
    bFirerate: Optional[StrictInt]
    bHearDist: Optional[StrictInt]
    chamberAmmoCount: Optional[StrictInt]
    defAmmo: Optional[TemplateId]
    defMagType: Optional[TemplateId]
    durabSpawnMax: Optional[StrictInt]
    durabSpawnMin: Optional[StrictInt]
    isBoltCatch: Optional[StrictBool]
    isChamberLoad: Optional[StrictBool]
    isFastReload: Optional[StrictBool]
    shotgunDispersion: Optional[StrictInt]
    ShotgunDispersion: Optional[float]
    weapClass: Optional[str]
    weapFireType: Optional[List[str]]
    weapUseType: Optional[str]
    Accuracy: Optional[StrictInt]
    AimSensitivity: Optional[list]
    BlocksCollapsible: Optional[StrictBool]
    BlocksFolding: Optional[StrictBool]
    CalibrationDistances: Optional[List[List[Union[StrictInt, float]]]]
    OpticCalibrationDistances: Optional[List[StrictInt]]
    RaidModdable: Optional[StrictBool]
    ScopesCount: Optional[StrictInt]
    SightModesCount: Optional[StrictInt]
    ToolModdable: Optional[StrictBool]
    Zooms: Optional[List[List[Union[StrictInt, float]]]]
    Recoil: Optional[Union[StrictInt, float]]
    EffectiveDistance: Optional[StrictInt]
    HasShoulderContact: Optional[StrictBool]
    IsAnimated: Optional[StrictBool]
    Loudness: Optional[StrictInt]
    ModesCount: Optional[List[StrictInt]]
    aimingSensitivity: Optional[float]
    sightModType: Optional[str]

    MaxResource: Optional[StrictInt]
    Resource: Optional[StrictInt]

    apResource: Optional[StrictInt]
    krResource: Optional[StrictInt]

    foodUseTime: Optional[StrictInt]
    foodEffectType: Optional[str]
    effects_health: Optional[dict]
    effects_damage: Optional[Union[list, dict]]
    StimulatorBuffs: Optional[str]

    muzzleModType: Optional[str]
    ModesCount: Optional[Union[List[StrictInt], StrictInt]]

    # Probably headsets related
    AmbientVolume: Optional[StrictInt]
    CompressorAttack: Optional[StrictInt]
    CompressorGain: Optional[StrictInt]
    CompressorRelease: Optional[StrictInt]
    CompressorTreshold: Optional[StrictInt]
    CompressorVolume: Optional[StrictInt]
    CutoffFreq: Optional[StrictInt]
    Distortion: Optional[float]
    DryVolume: Optional[StrictInt]
    Resonance: Optional[float]

    MaximumNumberOfUsage: Optional[StrictInt]

    knifeHitDelay: Optional[StrictInt]
    knifeHitSlashRate: Optional[StrictInt]
    knifeHitStabRate: Optional[StrictInt]
    knifeHitRadius: Optional[float]
    knifeHitSlashDam: Optional[StrictInt]
    knifeHitStabDam: Optional[StrictInt]
    knifeDurab: Optional[StrictInt]
    Durability: Optional[StrictInt]
    MaxDurability: Optional[StrictInt]
    PrimaryDistance: Optional[StrictInt]
    SecondryDistance: Optional[StrictInt]
    SlashPenetration: Optional[StrictInt]
    StabPenetration: Optional[StrictInt]
    MinRepairDegradation: Optional[float]
    MaxRepairDegradation: Optional[float]
    PrimaryConsumption: Optional[StrictInt]
    SecondryConsumption: Optional[StrictInt]
    DeflectionConsumption: Optional[StrictInt]
    PrimaryDistance: Optional[float]
    SecondryDistance: Optional[float]

    KeyIds: Optional[List[TemplateId]]
    TagColor: Optional[StrictInt]
    TagName: Optional[str]

    magAnimationIndex: Optional[StrictInt]
    CanFast: Optional[StrictBool]
    CanHit: Optional[StrictBool]
    CanAdmin: Optional[StrictBool]
    LoadUnloadModifier: Optional[StrictInt]
    CheckTimeModifier: Optional[StrictInt]
    CheckOverride: Optional[StrictInt]
    ReloadMagType: Optional[str]
    VisibleAmmoRangesString: Optional[str]

    ConfigPathStr: Optional[str]
    MaxMarkersCount: Optional[StrictInt]
    scaleMax: Optional[float]
    scaleMin: Optional[float]

    containType: Optional[list]
    isSecured: Optional[StrictBool]
    lootFilter: Optional[list]
    maxCountSpawn: Optional[Literal[0]]
    minCountSpawn: Optional[Literal[0]]
    openedByKeyID: Optional[list]
    sizeHeight: Optional[StrictInt]
    sizeWidth: Optional[StrictInt]
    spawnRarity: Optional[str]
    spawnTypes: Optional[str]
    eqMax: Optional[StrictInt]
    eqMin: Optional[StrictInt]
    rate: Optional[StrictInt]
    type: Optional[Any]

    Color: Optional[Union[dict, str]]
    DiffuseIntensity: Optional[float]
    Intensity: Optional[float]
    Mask: Optional[str]
    MaskSize: Optional[float]
    NoiseIntensity: Optional[float]
    NoiseScale: Optional[StrictInt]

    DogTagQualities: Optional[StrictBool]

    IsShoulderContact: Optional[StrictBool]

    # Probably thermal scopes
    ColdMax: Optional[float]
    DepthFade: Optional[float]
    HeatMin: Optional[float]
    IsFpsStuck: Optional[StrictBool]
    IsGlitch: Optional[StrictBool]
    IsMotionBlurred: Optional[StrictBool]
    IsNoisy: Optional[StrictBool]
    IsPixelated: Optional[StrictBool]
    MainTexColorCoef: Optional[float]
    MinimumTemperatureValue: Optional[float]
    PixelationBlockCount: Optional[StrictInt]
    RampPalette: Optional[str]
    RampShift: Optional[float]
    RoughnessCoef: Optional[float]
    SpecularCoef: Optional[float]

    CanBeHiddenDuringThrow: Optional[StrictBool]
    ContusionDistance: Optional[StrictInt]
    EmitTime: Optional[StrictInt]
    ExplDelay: Optional[float]
    Strength: Optional[StrictInt]
    ThrowType: Optional[str]
    explDelay: Optional[float]
    throwDamMax: Optional[float]

    RigLayoutName: Optional[str]


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
    ExcludedFilter: Optional[List[str]]


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
    Value: float


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

    __inventory__: Optional['MutableInventory'] = PrivateAttr(default=None)  # Link to the inventory

    id: ItemId = Field(alias='_id')
    tpl: TemplateId = Field(alias='_tpl')
    slotId: Optional[str] = None
    parent_id: Optional[ItemId] = Field(alias='parentId', default=None)
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

    @root_validator(pre=False, skip_on_failure=True)
    def validate_upd_none(cls, values: dict):  # pylint: disable=no-self-argument,no-self-use
        if 'upd' in values and values['upd'] is None:
            values['upd'] = ItemUpd()

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
    class Config(Base.Config):
        pass

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
