import enum
from typing import List, TypedDict


class HideoutAreaType(enum.Enum):
    Vents = 0
    Security = 1
    Lavatory = 2
    Stash = 3
    Generator = 4
    Heating = 5
    WaterCollector = 6
    MedStation = 7
    NutritionUnit = 8
    RestSpace = 9
    Workbench = 10
    IntelCenter = 11
    ShootingRange = 12
    Library = 13
    ScavCase = 14
    Illumination = 15
    PlaceOfFame = 16
    AirFiltering = 17
    SolarPower = 18
    BoozeGenerator = 19
    BitcoinFarm = 20
    ChristmasTree = 21


class HideoutArea(TypedDict):
    type: int
    level: int
    active: bool
    passiveBonusesEnabled: bool
    completeTime: int
    constructing: bool
    slots: list


class HideoutProduction(TypedDict):
    Progress: int
    inProgress: bool
    RecipeId: str
    Products: List
    SkipTime: int
    StartTime: int


class HideoutRecipe(TypedDict):
    _id: str
    areaType: int
    requirements: List
    continuous: bool
    productionTime: int
    endProduct: str
    count: int
    productionLimitCount: int
