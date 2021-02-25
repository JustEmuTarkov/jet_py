from types import SimpleNamespace
from typing import Dict, List, Literal, Optional, Union

import pydantic
import ujson
from pydantic import Field

from server import db_dir
from tarkov.hideout.models import HideoutAreaType
from tarkov.inventory.types import TemplateId
from tarkov.models import Base
from tarkov.trader import TraderType


class Requirements(SimpleNamespace):
    class Area(Base):
        areaType: HideoutAreaType
        requiredLevel: int
        type: Literal["Area"]

    class Item(Base):
        templateId: TemplateId
        count: int
        isFunctional: bool
        type: Literal["Item"]

    class TraderLoyalty(Base):
        traderId: TraderType
        loyaltyLevel: int
        type: Literal["TraderLoyalty"]

    class Skill(Base):
        skillName: str
        skillLevel: int
        type: Literal["Skill"]


class _BonusBase(Base):
    value: int
    passive: bool
    production: bool
    visible: bool


class Bonuses(SimpleNamespace):
    class AdditionalSlots(_BonusBase):
        filter: List[TemplateId]
        icon: Optional[str]
        type: Literal["AdditionalSlots"]

    class Text(_BonusBase):
        id: str
        icon: str
        type: Literal["TextBonus"]

    class SkillGroupLevelingBoost(_BonusBase):
        skillType: str
        type: Literal["SkillGroupLevelingBoost"]

    class StashSize(_BonusBase):
        templateId: TemplateId
        type: Literal["StashSize"]

    class GenericBonus(_BonusBase):
        type: Literal[
            "FuelConsumption",
            "EnergyRegeneration",
            "ExperienceRate",
            "RagfairCommission",
            "ScavCooldownTimer",
            "InsuranceReturnTime",
            "QuestMoneyReward",
            "UnlockWeaponModification",
            "MaximumEnergyReserve",
            "DebuffEndDelay",
            "HealthRegeneration",
            "HydrationRegeneration",
        ]


class HideoutAreaStage(Base):
    requirements: List[
        Union[
            Requirements.Area,
            Requirements.Item,
            Requirements.TraderLoyalty,
            Requirements.Skill,
        ]
    ]
    bonuses: List[
        Union[
            Bonuses.AdditionalSlots,
            Bonuses.Text,
            Bonuses.SkillGroupLevelingBoost,
            Bonuses.StashSize,
            Bonuses.GenericBonus,
        ]
    ]
    slots: int
    constructionTime: int
    description: str


class HideoutAreaTemplate(Base):
    id: str = Field(alias="_id")
    type: int
    enabled: bool
    needsFuel: bool
    takeFromSlotLocked: bool
    stages: Dict[str, HideoutAreaStage]


class HideoutAreasRepository:
    areas: List[HideoutAreaTemplate]

    def __init__(self, areas: List[dict]):
        self.areas = pydantic.parse_obj_as(List[HideoutAreaTemplate], areas)


areas_repository = HideoutAreasRepository(
    areas=[ujson.load(path.open()) for path in db_dir.joinpath("hideout", "areas").glob("*.json")]
)
