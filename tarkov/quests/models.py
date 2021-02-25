import enum
from typing import Dict, List, Literal, Union

from pydantic import Field, StrictBool, StrictInt

from tarkov import models
from tarkov.inventory.models import Item


class QuestStatus(enum.Enum):
    Locked = "Locked"
    AvailableForStart = "AvailableForStart"
    Started = "Started"
    AvailableForFinish = "AvailableForFinish"
    Success = "Success"
    Fail = "Fail"
    FailRestartable = "FailRestartable"
    MarkedAsFailed = "MarkedAsFailed"


class QuestReward(models.Base):
    id: str
    index: StrictInt


class QuestRewardTraderStanding(QuestReward):
    type: Literal["TraderStanding"]
    value: str
    target: str


class QuestRewardExperience(QuestReward):
    value: str
    type: Literal["Experience"]


class QuestRewardItem(QuestReward):
    type: Literal["Item"]
    value: str
    target: str
    items: List[Item]
    unknown: bool = False


class QuestRewardAssortUnlock(QuestReward):
    type: Literal["AssortmentUnlock"]
    target: str
    traderId: str
    loyaltyLevel: int
    items: List[Item]


class QuestRewardSkill(QuestReward):
    type: Literal["Skill"]
    target: str
    value: str


class QuestRewardTraderUnlock(QuestReward):
    type: Literal["TraderUnlock"]
    target: str


AnyReward = Union[
    QuestRewardTraderStanding,
    QuestRewardExperience,
    QuestRewardAssortUnlock,
    QuestRewardItem,
    QuestRewardSkill,
    QuestRewardTraderUnlock,
]


class QuestRewards(models.Base):
    Started: List[AnyReward]
    Success: List[AnyReward]
    Fail: List[AnyReward]


class QuestCondition(models.Base):
    parent: str = Field(alias="_parent")
    props: dict = Field(alias="_props")


class QuestConditions(models.Base):
    AvailableForStart: List[QuestCondition]
    AvailableForFinish: List[QuestCondition]
    Fail: List[QuestCondition]


class QuestTemplate(models.Base):
    class Config:
        fields = {"id": "_id"}
        allow_mutation = False

    id: str
    traderId: str
    location: str
    image: str
    type: str
    isKey: StrictBool
    restartable: StrictBool
    min_level: StrictInt
    canShowNotificationsInGame: StrictBool
    instantComplete: StrictBool = False
    secretQuest: StrictBool = False
    rewards: QuestRewards

    conditions: QuestConditions


class Quest(models.Base):
    quest_id: str = Field(alias="qid")
    started_at: int = Field(alias="startTime")
    completed_conditions: List[str] = Field(alias="completedConditions", default_factory=list)
    status_timers: Dict[str, float] = Field(alias="statusTimers", default_factory=dict)
    status: QuestStatus
