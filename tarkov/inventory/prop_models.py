from typing import Any, Dict, List, Literal, Optional, Union

import pydantic
import ujson
from pydantic import BaseModel, Extra, StrictBool, StrictFloat, StrictInt

from server import db_dir
from tarkov.inventory.models import Color, ItemGrid, NodeTemplateBase, TemplateId
from tarkov.models import Base


class Vector(Base):
    x: float
    y: float
    z: float


class PrefabModel(Base):
    path: str
    rcid: str


class BaseItemProp(BaseModel):
    __template_id__ = '54009119af1c881c07000029'

    class Config:
        extra = Extra.forbid

    Name: str
    ShortName: str
    Description: str
    Weight: float
    BackgroundColor: Color
    Width: StrictInt
    Height: StrictInt
    StackMaxSize: StrictInt
    Rarity: str
    SpawnChance: Union[StrictInt, StrictFloat]
    CreditsPrice: StrictInt
    ItemSound: str
    Prefab: PrefabModel
    UsePrefab: PrefabModel
    StackObjectsCount: StrictInt
    NotShownInSlot: StrictBool
    ExaminedByDefault: StrictBool
    ExamineTime: StrictInt
    IsUndiscardable: StrictBool
    IsUnsaleable: StrictBool
    IsUnbuyable: StrictBool
    IsUngivable: StrictBool
    IsLockedafterEquip: StrictBool
    QuestItem: StrictBool
    LootExperience: StrictInt
    ExamineExperience: StrictInt
    HideEntrails: StrictBool
    RepairCost: StrictInt
    RepairSpeed: StrictInt
    ExtraSizeLeft: StrictInt
    ExtraSizeRight: StrictInt
    ExtraSizeUp: StrictInt
    ExtraSizeDown: StrictInt
    ExtraSizeForceAdd: StrictBool
    MergesWithChildren: StrictBool
    CanSellOnRagfair: StrictBool
    CanRequireOnRagfair: StrictBool
    BannedFromRagfair: StrictBool
    ConflictingItems: List[TemplateId]
    FixedPrice: StrictBool
    Unlootable: StrictBool
    UnlootableFromSlot: str
    UnlootableFromSide: List[str]
    ChangePriceCoef: float
    AllowSpawnOnLocations: List[Literal['laboratory', 'Shoreline', 'Interchange', 'RezervBase', 'bigmap', 'Woods']]
    SendToClient: StrictBool
    AnimationVariantsNumber: StrictInt
    DiscardingBlock: StrictBool


class StackableItemProp(BaseItemProp):
    __template_id__ = '5661632d4bdc2d903d8b456b'

    StackMinRandom: StrictInt
    StackMaxRandom: StrictInt


class MoneyProp(StackableItemProp):
    __template_id__ = '543be5dd4bdc2deb348b4569'
    type: str
    eqMin: StrictInt
    eqMax: StrictInt
    rate: StrictInt


class AmmoBoxProp(StackableItemProp):
    __template_id__ = '543be5cb4bdc2deb348b4568'

    ammoCaliber: str
    StackSlots: list


class AmmoProp(StackableItemProp):
    class Config:
        extra = Extra.forbid

    __template_id__ = '5485a8684bdc2da71d8b4567'
    ammoType: str
    Damage: StrictInt
    ammoAccr: StrictInt
    ammoRec: StrictInt
    ammoDist: StrictInt
    buckshotBullets: StrictInt
    PenetrationPower: StrictInt
    PenetrationPowerDiviation: float
    ammoHear: StrictInt
    ammoSfx: str
    MisfireChance: float
    MinFragmentsCount: StrictInt
    MaxFragmentsCount: StrictInt
    ammoShiftChance: float
    casingName: Optional[str]
    casingEjectPower: StrictInt
    casingMass: float
    casingSounds: str
    ProjectileCount: StrictInt
    InitialSpeed: float
    PenetrationChance: float
    RicochetChance: float
    FragmentationChance: float
    BallisticCoeficient: float
    Deterioration: StrictInt
    SpeedRetardation: Union[StrictInt, StrictFloat]
    Tracer: StrictBool
    TracerColor: str
    TracerDistance: float
    ArmorDamage: StrictInt
    Caliber: str
    StaminaBurnPerDamage: float
    ShowBullet: StrictBool
    HasGrenaderComponent: StrictBool
    FuzeArmTimeSec: float
    ExplosionStrength: float
    MinExplosionDistance: float
    MaxExplosionDistance: float
    FragmentsCount: StrictInt
    FragmentType: TemplateId
    ShowHitEffectOnExplode: StrictBool
    ExplosionType: str
    AmmoLifeTimeSec: StrictInt
    Contusion: Vector
    ArmorDistanceDistanceDamage: Vector
    Blindness: Vector
    IsLightAndSoundShot: StrictBool
    LightAndSoundShotAngle: float
    LightAndSoundShotSelfContusionTime: float
    LightAndSoundShotSelfContusionStrength: float


class SpecItemProp(BaseItemProp):
    __template_id__ = '5447e0e74bdc2d3c308b4567'
    apResource: StrictInt
    krResource: StrictInt


class CompoundProp(BaseItemProp):
    __template_id__ = '566162e44bdc2d3f298b4573'

    Grids: List[ItemGrid]
    Slots: list
    CanPutIntoDuringTheRaid: StrictBool
    CantRemoveFromSlotsDuringRaid: list


class SearchableProp(CompoundProp):
    __template_id__ = '566168634bdc2d144c8b456c'

    SearchSound: str
    BlocksArmorVest: StrictBool


class LootContainerProp(SearchableProp):
    __template_id__ = '566965d44bdc2d814c8b4571'

    SpawnFilter: List[Union[TemplateId]]


class VestProps(SearchableProp):
    __template_id__ = '5448e5284bdc2dcb718b4567'

    RigLayoutName: str
    Durability: StrictInt
    MaxDurability: StrictInt
    armorZone: List[str]
    armorClass: str
    speedPenaltyPercent: StrictInt
    mousePenalty: StrictInt
    weaponErgonomicPenalty: StrictInt
    BluntThroughput: float
    ArmorMaterial: str


class BackpackProps(SearchableProp):
    __template_id__ = '5448e53e4bdc2d60728b4567'

    speedPenaltyPercent: StrictInt
    GridLayoutName: str


class MobContainerProp(SearchableProp):
    __template_id__ = '5448bf274bdc2dfc2f8b456a'

    containType: list
    sizeWidth: StrictInt
    sizeHeight: StrictInt
    isSecured: StrictBool
    spawnTypes: str
    lootFilter: list
    spawnRarity: str
    minCountSpawn: StrictInt
    maxCountSpawn: StrictInt
    openedByKeyID: list


class SimpleContainerProp(CompoundProp):
    __template_id__ = '5795f317245977243854e041'

    TagColor: StrictInt
    TagName: str


class ModProps(CompoundProp):
    __template_id__ = '5448fe124bdc2da5018b4567'

    Durability: StrictInt
    Accuracy: StrictInt
    Recoil: float
    Loudness: StrictInt
    EffectiveDistance: StrictInt
    Ergonomics: Union[StrictInt, StrictFloat]
    Velocity: float
    RaidModdable: StrictBool
    ToolModdable: StrictBool
    BlocksFolding: StrictBool
    BlocksCollapsible: StrictBool
    IsAnimated: StrictBool
    MergesWithChildren: StrictBool
    HasShoulderContact: StrictBool
    SightingRange: StrictInt


class MasterModProp(ModProps):
    __template_id__ = '55802f4a4bdc2ddb688b4569'


class HandguardProp(MasterModProp):
    __template_id__ = '55818a104bdc2db9688b4569'


class PistolGripProp(MasterModProp):
    __template_id__ = '55818a684bdc2ddd698b456d'


class BarrelModProp(MasterModProp):
    __template_id__ = '555ef6e44bdc2de9068b457e'

    CenterOfImpact: float
    ShotgunDispersion: float
    IsSilencer: bool


class GearModProp(ModProps):
    __template_id__ = '55802f3e4bdc2de7118b4584'


class StockProp(GearModProp):
    __template_id__ = '55818a594bdc2db9688b456a'
    IsShoulderContact: StrictBool
    Foldable: StrictBool
    Retractable: StrictBool
    SizeReduceRight: StrictInt


class ChargeProp(GearModProp):
    __template_id__ = '55818a6f4bdc2db9688b456b'


class MountProp(GearModProp):
    __template_id__ = '55818b224bdc2dde698b456f'


class LauncherProp(GearModProp):
    __template_id__ = '55818b014bdc2ddc698b456b'


class ShaftProp(GearModProp):
    __template_id__ = '55818a604bdc2db5418b457e'


class MagazineProp(GearModProp):
    __template_id__ = '5448bc234bdc2d3c308b4569'
    magAnimationIndex: StrictInt
    Cartridges: list
    CanFast: StrictBool
    CanHit: StrictBool
    CanAdmin: StrictBool
    LoadUnloadModifier: StrictInt
    CheckTimeModifier: StrictInt
    CheckOverride: StrictInt
    ReloadMagType: str
    VisibleAmmoRangesString: str


class FunctionalModProp(ModProps):
    __template_id__ = '550aa4154bdc2dd8348b456b'


class BipodProp(FunctionalModProp):
    __template_id__ = '55818afb4bdc2dde698b456d'


class LightLaserProp(FunctionalModProp):
    __template_id__ = '55818b0e4bdc2dde698b456e'


class TacticalComboProp(FunctionalModProp):
    __template_id__ = '55818b164bdc2ddc698b456c'
    ModesCount: StrictInt


class FlashlightProp(FunctionalModProp):
    __template_id__ = '55818b084bdc2d5b648b4571'
    ModesCount: StrictInt


class ForegripProp(FunctionalModProp):
    __template_id__ = '55818af64bdc2d5b648b4570'


class RailCoverProp(FunctionalModProp):
    __template_id__ = '55818b1d4bdc2d5b648b4572'


class GasBlockProp(FunctionalModProp):
    __template_id__ = '56ea9461d2720b67698b456f'


class AuxiliaryModProp(FunctionalModProp):
    __template_id__ = '5a74651486f7744e73386dd1'


class MuzzleProp(FunctionalModProp):
    __template_id__ = '5448fe394bdc2d0d028b456c'

    muzzleModType: str


class SightProp(FunctionalModProp):
    __template_id__ = '5448fe7a4bdc2d6f028b456b'

    sightModType: str
    aimingSensitivity: float
    SightModesCount: StrictInt
    OpticCalibrationDistances: Optional[List[float]]
    SightingRange: StrictInt
    ScopesCount: StrictInt
    AimSensitivity: List[List[float]]
    ModesCount: List[StrictInt]
    Zooms: List[List[float]]
    CalibrationDistances: List[List[float]]


class SpecialScopeProp(SightProp):
    __template_id__ = '55818aeb4bdc2ddc698b456a'


class NightVisionScopeProp(SpecialScopeProp):
    __template_id__ = '5a2c3a9486f774688b05e574'
    Intensity: float
    Mask: str
    MaskSize: float
    NoiseIntensity: float
    NoiseScale: float
    Color: dict
    DiffuseIntensity: float
    HasHinge: StrictBool


class ThermalVisionProp(SpecialScopeProp):
    __template_id__ = '5d21f59b6dbe99052b54ef83'

    RampPalette: str
    DepthFade: float
    RoughnessCoef: float
    SpecularCoef: float
    MainTexColorCoef: float
    MinimumTemperatureValue: float
    RampShift: float
    HeatMin: float
    ColdMax: float
    IsNoisy: StrictBool
    NoiseIntensity: float
    IsFpsStuck: StrictBool
    IsGlitch: StrictBool
    IsMotionBlurred: StrictBool
    Mask: str
    MaskSize: float
    IsPixelated: StrictBool
    PixelationBlockCount: StrictInt


class LockableContainerProp(CompoundProp):
    __template_id__ = '5671435f4bdc2d96058b4569'

    KeyIds: List[TemplateId]
    TagColor: StrictInt
    TagName: str


class StationaryContainerProp(CompoundProp):
    __template_id__ = '567583764bdc2d98058b456e'


class InventoryProp(CompoundProp):
    __template_id__ = '55d720f24bdc2d88028b456d'


class StashProp(CompoundProp):
    __template_id__ = '566abbb64bdc2d144c8b457d'


class EquipmentProp(CompoundProp):
    __template_id__ = '543be5f84bdc2dd4348b456a'

    BlocksEarpiece: StrictBool
    BlocksEyewear: StrictBool
    BlocksHeadwear: StrictBool
    BlocksFaceCover: StrictBool


class ArmbandProp(EquipmentProp):
    __template_id__ = '5b3f15d486f77432d0509248'


class ArmoredEquipmentProp(EquipmentProp):
    __template_id__ = '57bef4c42459772e8d35a53b'

    Durability: float
    MaxDurability: float
    armorClass: str
    speedPenaltyPercent: StrictInt
    mousePenalty: StrictInt
    weaponErgonomicPenalty: StrictInt
    armorZone: List[str]
    Indestructibility: float
    headSegments: List[str]
    FaceShieldComponent: StrictBool
    FaceShieldMask: str
    HasHinge: StrictBool
    MaterialType: str
    RicochetParams: Vector
    DeafStrength: str
    BluntThroughput: float
    ArmorMaterial: str


class HeadphonesProp(EquipmentProp):
    __template_id__ = '5645bcb74bdc2ded0b8b4578'

    Distortion: float
    CompressorTreshold: float
    CompressorAttack: float
    CompressorRelease: float
    CompressorGain: float
    CutoffFreq: float
    Resonance: float
    CompressorVolume: float
    AmbientVolume: float
    DryVolume: float


class WeaponProp(CompoundProp):
    __template_id__ = '5422acb9af1c889c16000029'

    weapClass: str
    weapUseType: str
    ammoCaliber: str
    Durability: float
    MaxDurability: float
    OperatingResource: StrictInt
    RepairComplexity: StrictInt
    durabSpawnMin: float
    durabSpawnMax: float
    isFastReload: StrictBool
    RecoilForceUp: StrictInt
    RecoilForceBack: StrictInt
    Convergence: float
    RecoilAngle: float
    weapFireType: List[str]
    RecolDispersion: StrictInt
    bFirerate: StrictInt
    Ergonomics: StrictInt
    Velocity: float
    bEffDist: StrictInt
    bHearDist: StrictInt
    isChamberLoad: StrictBool
    chamberAmmoCount: StrictInt
    isBoltCatch: StrictBool
    defMagType: TemplateId
    defAmmo: TemplateId
    shotgunDispersion: StrictInt
    Chambers: list
    CameraRecoil: float
    CameraSnap: float
    ReloadMode: str
    CenterOfImpact: float
    AimPlane: float
    DeviationCurve: StrictInt
    DeviationMax: StrictInt
    Foldable: StrictBool
    Retractable: StrictBool
    TacticalReloadStiffnes: Vector
    TacticalReloadFixation: float
    RecoilCenter: Vector
    RotationCenter: Vector
    RotationCenterNoStock: Vector
    MergesWithChildren: StrictBool
    SizeReduceRight: StrictInt
    FoldedSlot: str
    CompactHandling: StrictBool
    SightingRange: StrictInt
    MinRepairDegradation: float
    MaxRepairDegradation: float
    IronSightRange: StrictInt
    MustBoltBeOpennedForExternalReload: StrictBool
    MustBoltBeOpennedForInternalReload: StrictBool
    BoltAction: StrictBool
    HipAccuracyRestorationDelay: float
    HipAccuracyRestorationSpeed: float
    HipInnaccuracyGain: float
    ManualBoltCatch: StrictBool


class ShotgunProp(WeaponProp):
    __template_id__ = '5447b6094bdc2dc3278b4567'
    ShotgunDispersion: float


class MapProp(BaseItemProp):
    __template_id__ = '567849dd4bdc2d150f8b456e'
    ConfigPathStr: str
    MaxMarkersCount: StrictInt
    scaleMin: float
    scaleMax: float


class KnifeProp(BaseItemProp):
    __template_id__ = '5447e1d04bdc2dff2f8b4567'
    knifeHitDelay: float
    knifeHitSlashRate: float
    knifeHitStabRate: float
    knifeHitRadius: float
    knifeHitSlashDam: float
    knifeHitStabDam: float
    knifeDurab: float
    Durability: float
    MaxDurability: float
    PrimaryDistance: float
    SecondryDistance: float
    SlashPenetration: float
    StabPenetration: float
    MinRepairDegradation: float
    MaxRepairDegradation: float
    PrimaryConsumption: float
    SecondryConsumption: float
    DeflectionConsumption: float


class BarterItemProp(BaseItemProp):
    __template_id__ = '5448eb774bdc2d0a728b4567'

    MaxResource: float
    Resource: float


class BarterItemOtherProp(BarterItemProp):
    DogTagQualities: StrictBool


class KeyProp(BaseItemProp):
    __template_id__ = '543be5e94bdc2df1348b4568'

    MaximumNumberOfUsage: StrictInt


class FoodDrinkProp(BaseItemProp):
    __template_id__ = '543be6674bdc2df1348b4569'

    foodUseTime: StrictInt
    foodEffectType: str
    MaxResource: StrictInt
    StimulatorBuffs: str
    effects_damage: Any
    effects_health: Any


class MedsProp(BaseItemProp):
    __template_id__ = '543be5664bdc2dd4348b4569'
    medUseTime: StrictInt
    medEffectType: str
    MaxHpResource: float
    hpResourceRate: float
    StimulatorBuffs: str
    effects_damage: Any
    effects_health: Any


class ThrowingProp(BaseItemProp):
    __template_id__ = '543be6564bdc2df4348b4568'

    ThrowType: str
    ExplDelay: float
    MinExplosionDistance: float
    MaxExplosionDistance: float
    FragmentsCount: StrictInt
    FragmentType: TemplateId
    Strength: StrictInt
    ContusionDistance: float
    throwDamMax: float
    explDelay: float
    Blindness: Vector
    Contusion: Vector
    ArmorDistanceDistanceDamage: Vector
    EmitTime: StrictInt
    CanBeHiddenDuringThrow: StrictBool


AnyProp = Union[
    BaseItemProp,
    StackableItemProp,
    MoneyProp,
    AmmoProp,
    AmmoBoxProp,
    SpecItemProp,
    CompoundProp,
    SearchableProp,
    LootContainerProp,
    VestProps,
    BackpackProps,
    MobContainerProp,
    SimpleContainerProp,
    ModProps,
    MasterModProp,
    HandguardProp,
    PistolGripProp,
    BarrelModProp,
    GearModProp,
    StockProp,
    ChargeProp,
    MountProp,
    LauncherProp,
    ShaftProp,
    MagazineProp,
    FunctionalModProp,
    BipodProp,
    LightLaserProp,
    TacticalComboProp,
    FlashlightProp,
    ForegripProp,
    RailCoverProp,
    GasBlockProp,
    AuxiliaryModProp,
    MuzzleProp,
    SightProp,
    SpecialScopeProp,
    NightVisionScopeProp,
    ThermalVisionProp,
    LockableContainerProp,
    StationaryContainerProp,
    InventoryProp,
    StashProp,
    EquipmentProp,
    ArmbandProp,
    ArmoredEquipmentProp,
    HeadphonesProp,
    WeaponProp,
    ShotgunProp,
    MapProp,
    KnifeProp,
    BarterItemProp,
    BarterItemOtherProp,
    KeyProp,
    FoodDrinkProp,
    MedsProp,
    ThrowingProp,
]


class ItemTemplate(NodeTemplateBase):
    type: Literal['Item']
    props: AnyProp


class NodeTemplate(NodeTemplateBase):
    type: Literal['Node']
    props: Dict


AnyTemplate = Union[ItemTemplate, NodeTemplate]

for item_file_path in db_dir.joinpath('items').glob('*'):
    file_data = ujson.load(item_file_path.open('r', encoding='utf8'))
    item_templates = (item for item in file_data if item['_type'] == 'Item')
    pydantic.parse_obj_as(List[ItemTemplate], item_templates)

# @staticmethod
# def __read_item_templates() -> Dict[TemplateId, AnyTemplate]:
#     item_templates: List[AnyTemplate] = []
#     # Read every file from db/items
#     for item_file_path in db_dir.joinpath('items').glob('*'):
#         file_data = ujson.load(item_file_path.open('r', encoding='utf8'))
#         items: List[AnyTemplate] = pydantic.parse_obj_as(List[AnyTemplate],
#         item_templates.extend(items)
#     return {tpl.id: tpl for tpl in item_templates}
