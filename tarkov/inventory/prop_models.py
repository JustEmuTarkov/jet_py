import typing
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Extra, Field, StrictBool, StrictFloat, StrictInt

from tarkov.inventory.types import TemplateId


class Base(BaseModel):
    class Config:
        extra = Extra.forbid


Color = Union[
    Literal["default"],
    Literal["black"],
    Literal["red"],
    Literal["grey"],
    Literal["blue"],
    Literal["orange"],
    Literal["yellow"],
    Literal["green"],
    Literal["violet"],
]
TracerColor = Union[
    Color,
    Literal["tracerRed"],
    Literal["tracerGreen"],
    Literal["tracerYellow"],
    Literal["tracerGreen"],
]


class FilterProps(Base):
    Filter: List[str] = Field(default_factory=list)
    ExcludedFilter: Optional[List[str]]


class _GridProps(Base):
    class Config:
        allow_mutation = False
        fields = {"width": "cellsH", "height": "cellsV"}

    filters: List[FilterProps]
    width: StrictInt
    height: StrictInt
    minCount: StrictInt
    maxCount: StrictInt
    maxWeight: StrictInt


class Grid(Base):
    name: str = Field(alias="_name")
    id: TemplateId = Field(alias="_id")
    parent: TemplateId = Field(alias="_parent")
    proto: TemplateId = Field(alias="_proto")
    props: _GridProps = Field(alias="_props")


class _CartridgesProps(Base):
    filters: List[FilterProps]


class Cartridges(Base):
    class Config:
        allow_mutation = False
        fields = {
            "name": "_name",
            "id": "_id",
            "parent": "_parent",
            "max_count": "_max_count",
            "props": "_props",
            "proto": "_proto",
        }

    name: Literal["cartridges"]
    id: TemplateId
    parent: TemplateId
    max_count: StrictInt
    props: _CartridgesProps
    proto: str


class Vector(Base):
    x: float
    y: float
    z: float


class PrefabModel(Base):
    path: str
    rcid: str


class BaseItemProps(BaseModel):
    __template_id__: str = "54009119af1c881c07000029"

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
    CreditsPrice: int
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
    AllowSpawnOnLocations: List[
        Literal[
            "laboratory", "Shoreline", "Interchange", "RezervBase", "bigmap", "Woods"
        ]
    ]
    SendToClient: StrictBool
    AnimationVariantsNumber: StrictInt
    DiscardingBlock: StrictBool


class StackableItemProps(BaseItemProps):
    __template_id__: str = "5661632d4bdc2d903d8b456b"

    StackMinRandom: StrictInt
    StackMaxRandom: StrictInt


class MoneyProps(StackableItemProps):
    __template_id__: str = "543be5dd4bdc2deb348b4569"
    type: str
    eqMin: StrictInt
    eqMax: StrictInt
    rate: StrictInt


class AmmoBoxProps(StackableItemProps):
    __template_id__: str = "543be5cb4bdc2deb348b4568"

    ammoCaliber: str
    StackSlots: list


class AmmoProps(StackableItemProps):
    class Config:
        extra = Extra.forbid

    __template_id__: str = "5485a8684bdc2da71d8b4567"
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


class SpecItemProps(BaseItemProps):
    __template_id__: str = "5447e0e74bdc2d3c308b4567"
    apResource: StrictInt
    krResource: StrictInt


class CompoundProps(BaseItemProps):
    __template_id__: str = "566162e44bdc2d3f298b4573"

    Grids: List[Grid]
    Slots: list
    CanPutIntoDuringTheRaid: StrictBool
    CantRemoveFromSlotsDuringRaid: list


class SearchableProps(CompoundProps):
    __template_id__: str = "566168634bdc2d144c8b456c"

    SearchSound: str
    BlocksArmorVest: StrictBool


class LootContainerProps(SearchableProps):
    __template_id__: str = "566965d44bdc2d814c8b4571"

    SpawnFilter: List[Union[TemplateId]]


class VestProps(SearchableProps):
    __template_id__: str = "5448e5284bdc2dcb718b4567"

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


class BackpackProps(SearchableProps):
    __template_id__: str = "5448e53e4bdc2d60728b4567"

    speedPenaltyPercent: StrictInt
    GridLayoutName: str


class MobContainerProps(SearchableProps):
    __template_id__: str = "5448bf274bdc2dfc2f8b456a"

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


class SimpleContainerProps(CompoundProps):
    __template_id__: str = "5795f317245977243854e041"

    TagColor: StrictInt
    TagName: str


class ModProps(CompoundProps):
    __template_id__: str = "5448fe124bdc2da5018b4567"

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


class MasterModProps(ModProps):
    __template_id__: str = "55802f4a4bdc2ddb688b4569"


class HandguardProps(MasterModProps):
    __template_id__: str = "55818a104bdc2db9688b4569"


class PistolGripProps(MasterModProps):
    __template_id__: str = "55818a684bdc2ddd698b456d"


class BarrelModProps(MasterModProps):
    __template_id__: str = "555ef6e44bdc2de9068b457e"

    CenterOfImpact: float
    ShotgunDispersion: float
    IsSilencer: bool


class GearModProps(ModProps):
    __template_id__: str = "55802f3e4bdc2de7118b4584"


class StockProps(GearModProps):
    __template_id__: str = "55818a594bdc2db9688b456a"
    IsShoulderContact: StrictBool
    Foldable: StrictBool
    Retractable: StrictBool
    SizeReduceRight: StrictInt


class ChargeProps(GearModProps):
    __template_id__: str = "55818a6f4bdc2db9688b456b"


class MountProps(GearModProps):
    __template_id__: str = "55818b224bdc2dde698b456f"


class LauncherProps(GearModProps):
    __template_id__: str = "55818b014bdc2ddc698b456b"


class ShaftProps(GearModProps):
    __template_id__: str = "55818a604bdc2db5418b457e"


class MagazineProps(GearModProps):
    __template_id__: str = "5448bc234bdc2d3c308b4569"
    magAnimationIndex: StrictInt
    Cartridges: List[Cartridges]
    CanFast: StrictBool
    CanHit: StrictBool
    CanAdmin: StrictBool
    LoadUnloadModifier: StrictInt
    CheckTimeModifier: StrictInt
    CheckOverride: StrictInt
    ReloadMagType: str
    VisibleAmmoRangesString: str


class FunctionalModProps(ModProps):
    __template_id__: str = "550aa4154bdc2dd8348b456b"


class BipodProps(FunctionalModProps):
    __template_id__: str = "55818afb4bdc2dde698b456d"


class LightLaserProps(FunctionalModProps):
    __template_id__: str = "55818b0e4bdc2dde698b456e"


class TacticalComboProps(FunctionalModProps):
    __template_id__: str = "55818b164bdc2ddc698b456c"
    ModesCount: StrictInt


class FlashlightProps(FunctionalModProps):
    __template_id__: str = "55818b084bdc2d5b648b4571"
    ModesCount: StrictInt = 0


class ForegripProps(FunctionalModProps):
    __template_id__: str = "55818af64bdc2d5b648b4570"


class RailCoverProps(FunctionalModProps):
    __template_id__: str = "55818b1d4bdc2d5b648b4572"


class GasBlockProps(FunctionalModProps):
    __template_id__: str = "56ea9461d2720b67698b456f"


class AuxiliaryModProps(FunctionalModProps):
    __template_id__: str = "5a74651486f7744e73386dd1"


class MuzzleProps(FunctionalModProps):
    __template_id__: str = "5448fe394bdc2d0d028b456c"

    muzzleModType: str


class SightProps(FunctionalModProps):
    __template_id__: str = "5448fe7a4bdc2d6f028b456b"

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


class SpecialScopeProps(SightProps):
    __template_id__: str = "55818aeb4bdc2ddc698b456a"


class NightVisionScopeProps(SpecialScopeProps):
    __template_id__: str = "5a2c3a9486f774688b05e574"
    Intensity: float
    Mask: str
    MaskSize: float
    NoiseIntensity: float
    NoiseScale: float
    Color: dict
    DiffuseIntensity: float
    HasHinge: StrictBool


class ThermalVisionProps(SpecialScopeProps):
    __template_id__: str = "5d21f59b6dbe99052b54ef83"

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


class LockableContainerProps(CompoundProps):
    __template_id__: str = "5671435f4bdc2d96058b4569"

    KeyIds: List[TemplateId]
    TagColor: StrictInt
    TagName: str


class StationaryContainerProps(CompoundProps):
    __template_id__: str = "567583764bdc2d98058b456e"


class InventoryProps(CompoundProps):
    __template_id__: str = "55d720f24bdc2d88028b456d"


class StashProps(CompoundProps):
    __template_id__: str = "566abbb64bdc2d144c8b457d"


class EquipmentProps(CompoundProps):
    __template_id__: str = "543be5f84bdc2dd4348b456a"

    BlocksEarpiece: StrictBool
    BlocksEyewear: StrictBool
    BlocksHeadwear: StrictBool
    BlocksFaceCover: StrictBool


class ArmbandProps(EquipmentProps):
    __template_id__: str = "5b3f15d486f77432d0509248"


class ArmoredEquipmentProps(EquipmentProps):
    __template_id__: str = "57bef4c42459772e8d35a53b"

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


class HeadphonesProps(EquipmentProps):
    __template_id__: str = "5645bcb74bdc2ded0b8b4578"

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


class WeaponProps(CompoundProps):
    __template_id__: str = "5422acb9af1c889c16000029"

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


class ShotgunProps(WeaponProps):
    __template_id__: str = "5447b6094bdc2dc3278b4567"
    ShotgunDispersion: float


class MapProps(BaseItemProps):
    __template_id__: str = "567849dd4bdc2d150f8b456e"
    ConfigPathStr: str
    MaxMarkersCount: StrictInt
    scaleMin: float
    scaleMax: float


class KnifeProps(BaseItemProps):
    __template_id__: str = "5447e1d04bdc2dff2f8b4567"
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


class BarterItemProps(BaseItemProps):
    __template_id__: str = "5448eb774bdc2d0a728b4567"

    MaxResource: float
    Resource: float


class KeyProps(BaseItemProps):
    __template_id__: str = "543be5e94bdc2df1348b4568"

    MaximumNumberOfUsage: StrictInt


class FoodDrinkProps(BaseItemProps):
    __template_id__: str = "543be6674bdc2df1348b4569"

    foodUseTime: StrictInt
    foodEffectType: str
    MaxResource: StrictInt
    StimulatorBuffs: str
    effects_damage: Any
    effects_health: Any


class MedsProps(BaseItemProps):
    __template_id__: str = "543be5664bdc2dd4348b4569"
    medUseTime: StrictInt
    medEffectType: str
    MaxHpResource: StrictInt
    hpResourceRate: float
    StimulatorBuffs: str
    effects_damage: Any
    effects_health: Any


class ThrowingProps(BaseItemProps):
    __template_id__: str = "543be6564bdc2df4348b4568"

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


class ArmorProps(ArmoredEquipmentProps):
    __template_id__: str = "5448e54d4bdc2dcc718b4568"


class AssaultCarbineProps(WeaponProps):
    __template_id__: str = "5447b5fc4bdc2d87278b4567"


class AssaultRifleProps(WeaponProps):
    __template_id__: str = "5447b5f14bdc2d61278b4567"


class AssaultScopeProps(SightProps):
    __template_id__: str = "55818add4bdc2d5b648b456f"


class BatteryProps(BarterItemProps):
    __template_id__: str = "57864ee62459775490116fc1"


class BuildingMaterialProps(BarterItemProps):
    __template_id__: str = "57864ada245977548638de91"


class CollimatorProps(SightProps):
    __template_id__: str = "55818ad54bdc2ddc698b4569"


class CompactCollimatorProps(SightProps):
    __template_id__: str = "55818acf4bdc2dde698b456b"


class CompassProps(SpecItemProps):
    __template_id__: str = "5f4fbaaca5573a5ac31db429"


class DrinkProps(FoodDrinkProps):
    __template_id__: str = "5448e8d64bdc2dce718b4568"


class FoodProps(FoodDrinkProps):
    __template_id__: str = "5448e8d04bdc2ddf718b4569"


class DrugsProps(MedsProps):
    __template_id__: str = "5448f3a14bdc2d27728b4569"


class ElectronicsProps(BarterItemProps):
    __template_id__: str = "57864a66245977548f04a81f"


class FaceCoverProps(ArmoredEquipmentProps):
    __template_id__: str = "5a341c4686f77469e155819e"


class FlashHiderProps(MuzzleProps):
    __template_id__: str = "550aa4bf4bdc2dd6348b456b"


class LubricantProps(BarterItemProps):
    __template_id__: str = "57864e4c24597754843f8723"


class FuelProps(LubricantProps):
    __template_id__: str = "5d650c3e815116009f6201d2"


class GrenadeLauncherProps(WeaponProps):
    __template_id__: str = "5447bedf4bdc2d87278b4568"


class HeadwearProps(ArmorProps):
    __template_id__: str = "5a341c4086f77401f2541505"


class HouseholdGoodsProps(BarterItemProps):
    __template_id__: str = "57864c322459775490116fbf"


class InfoProps(BaseItemProps):
    __template_id__: str = "5448ecbe4bdc2d60728b4568"


class IronSightProps(SightProps):
    __template_id__: str = "55818ac54bdc2d5b648b456e"


class JewelryProps(BarterItemProps):
    __template_id__: str = "57864a3d24597754843f8721"


class KeycardProps(KeyProps):
    __template_id__: str = "5c164d2286f774194c5e69fa"


class KeyMechanicalProps(KeyProps):
    __template_id__: str = "5c99f98d86f7745c314214b3"


class MachineGunProps(WeaponProps):
    __template_id__: str = "5447bed64bdc2d97278b4568"


class MarksmanRifleProps(WeaponProps):
    __template_id__: str = "5447b6194bdc2d67278b4567"


class MedicalProps(MedsProps):
    __template_id__: str = "5448f3ac4bdc2dce718b4569"


class MedicalSuppliesProps(BarterItemProps):
    __template_id__: str = "57864c8c245977548867e7f1"


class MedKitProps(MedsProps):
    __template_id__: str = "5448f39d4bdc2d0a728b4568"


class MuzzleComboProps(MuzzleProps):
    __template_id__: str = "550aa4dd4bdc2dc9348b4569"


class OpticScopeProps(SightProps):
    __template_id__: str = "55818ae44bdc2dde698b456c"


class OtherProps(BarterItemProps):
    __template_id__: str = "590c745b86f7743cc433c5f2"
    DogTagQualities: StrictBool


class PistolProps(WeaponProps):
    __template_id__: str = "5447b5cf4bdc2d65278b4567"


class PocketsProps(SearchableProps):
    __template_id__: str = "557596e64bdc2dc2118b4571"


class ReceiverProps(MasterModProps):
    __template_id__: str = "55818a304bdc2db5418b457d"


class SilencerProps(MuzzleProps):
    __template_id__: str = "550aa4cd4bdc2dd8348b456c"


class SmgProps(WeaponProps):
    __template_id__: str = "5447b5e04bdc2d62278b4567"


class SniperRifleProps(WeaponProps):
    __template_id__: str = "5447b6254bdc2dc3278b4568"


class StimulatorProps(MedsProps):
    __template_id__: str = "5448f3a64bdc2d60728b456a"


class ToolProps(BarterItemProps):
    __template_id__: str = "57864bb7245977548b3b66c2"


class VisorsProps(ArmoredEquipmentProps):
    __template_id__: str = "5448e5724bdc2ddf718b4568"


AnyProp = Union[
    BaseItemProps,
    StackableItemProps,
    MoneyProps,
    AmmoProps,
    AmmoBoxProps,
    SpecItemProps,
    CompoundProps,
    SearchableProps,
    LootContainerProps,
    VestProps,
    BackpackProps,
    MobContainerProps,
    SimpleContainerProps,
    ModProps,
    MasterModProps,
    HandguardProps,
    PistolGripProps,
    BarrelModProps,
    GearModProps,
    StockProps,
    ChargeProps,
    MountProps,
    LauncherProps,
    ShaftProps,
    MagazineProps,
    FunctionalModProps,
    BipodProps,
    LightLaserProps,
    TacticalComboProps,
    FlashlightProps,
    ForegripProps,
    RailCoverProps,
    GasBlockProps,
    AuxiliaryModProps,
    MuzzleProps,
    SightProps,
    SpecialScopeProps,
    NightVisionScopeProps,
    ThermalVisionProps,
    LockableContainerProps,
    StationaryContainerProps,
    InventoryProps,
    StashProps,
    EquipmentProps,
    ArmbandProps,
    ArmoredEquipmentProps,
    HeadphonesProps,
    WeaponProps,
    ShotgunProps,
    MapProps,
    KnifeProps,
    BarterItemProps,
    KeyProps,
    FoodDrinkProps,
    MedsProps,
    ThrowingProps,
    ArmorProps,
    AssaultCarbineProps,
    AssaultRifleProps,
    AssaultScopeProps,
    BatteryProps,
    BuildingMaterialProps,
    CollimatorProps,
    CompactCollimatorProps,
    CompassProps,
    DrinkProps,
    FoodProps,
    DrugsProps,
    ElectronicsProps,
    FaceCoverProps,
    FlashHiderProps,
    LubricantProps,
    FuelProps,
    GrenadeLauncherProps,
    HeadwearProps,
    HouseholdGoodsProps,
    InfoProps,
    IronSightProps,
    JewelryProps,
    KeycardProps,
    KeyMechanicalProps,
    MachineGunProps,
    MarksmanRifleProps,
    MedicalProps,
    MedicalSuppliesProps,
    MedKitProps,
    MuzzleComboProps,
    OpticScopeProps,
    OtherProps,
    PistolProps,
    PocketsProps,
    ReceiverProps,
    SilencerProps,
    SmgProps,
    SniperRifleProps,
    StimulatorProps,
    ToolProps,
    VisorsProps,
]

props_models_map: Dict[str, AnyProp] = {
    model.__template_id__: model for model in typing.get_args(AnyProp)
}
