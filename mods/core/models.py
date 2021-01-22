from __future__ import annotations

from typing import Literal, List, Optional

import pydantic
from pydantic import Extra, StrictInt, StrictBool


class Base(pydantic.BaseModel):
    class Config:
        extra = Extra.allow
        validate_assignment = True
        use_enum_values = True

    def dict(self, by_alias=True, exclude_unset=True, **kwargs, ) -> 'DictStrAny':
        return super().dict(
            **kwargs,
            by_alias=by_alias,
            exclude_unset=exclude_unset
        )


class ItemTemplateProps(Base):
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


class NodeTemplate(Base):
    class Config:
        extra = Extra.allow
        fields = {
            'id': '_id',
            'name': '_name',
            'parent': '_parent',
            'type': '_type',
            'props': '_props',
            'proto': '_proto'
        }

    id: str
    name: str
    parent: str
    type: str
    proto: Optional[str] = None


class GridPropsFilter(Base):
    Filter: List[str]
    ExcludedFilter: List[str]


class GridProps(Base):
    class Config:
        fields = {
            'width': 'cellsH',
            'height': 'cellsV'
        }

    filters: List[GridPropsFilter]
    width: StrictInt
    height: StrictInt
    minCount: StrictInt
    maxCount: StrictInt
    maxWeight: StrictInt


class ItemGrid(NodeTemplate):
    type: Optional[str] = None  # type: ignore
    props: GridProps


class ItemTemplate(NodeTemplate):
    props: ItemTemplateProps


ItemTemplateProps.update_forward_refs()
