from typing import Dict, List, Literal

import pydantic
from pydantic import Field, StrictBool

from tarkov.inventory.models import Item
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.profile.models import BackendCounter, ConditionCounters, Skills
from tarkov.quests.models import Quest

BodyPartKey = Literal["Head", "Chest", "Stomach", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]


class BodyPart(pydantic.BaseModel):
    current: float = Field(alias="Current")
    maximum: float = Field(alias="Maximum")
    effects: dict = Field(alias="Effects")


class OffraidHealth(pydantic.BaseModel):
    energy: float = Field(alias="Energy")
    hydration: float = Field(alias="Hydration")
    is_alive: bool = Field(alias="IsAlive")
    health: Dict[BodyPartKey, BodyPart] = Field(alias="Health")


class OffraidInventory(pydantic.BaseModel):
    equipment: ItemId
    questRaidItems: ItemId
    questStashItems: ItemId
    fastPanel: Dict[str, ItemId]
    items: List[Item]


class OffraidProfile(pydantic.BaseModel):
    id: str = Field(alias="_id")
    aid: str
    savage: str

    Encyclopedia: Dict[TemplateId, StrictBool]
    Skills: Skills
    Quests: List[Quest]
    ConditionCounters: ConditionCounters
    BackendCounters: Dict[str, BackendCounter]
    Inventory: OffraidInventory
    Stats: dict
