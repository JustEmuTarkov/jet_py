import enum
from typing import Any, List, Literal, Union

from pydantic import StrictBool, StrictInt

from tarkov import models
from tarkov.inventory import Item


class QuestMessageType(enum.Enum):
    questStart = 10
    questFail = 11
    questSuccess = 1

    npcTrader = 2

    insuranceReturn = 8


class QuestReward(models.Base):
    id: str
    index: StrictInt


class QuestRewardTraderStanding(QuestReward):
    type: Literal['TraderStanding']
    value: str
    target: str


class QuestRewardExperience(QuestReward):
    value: str
    type: Literal['Experience']


class QuestRewardItem(QuestReward):
    type: Literal['Item']
    value: str
    target: str
    items: List[Item]
    unknown: bool = False


class QuestRewardAssortUnlock(QuestReward):
    type: Literal['AssortmentUnlock']
    target: str
    traderId: str
    loyaltyLevel: int
    items: List[Item]


class QuestRewardSkill(QuestReward):
    type: Literal['Skill']
    target: str
    value: str


class QuestRewardTraderUnlock(QuestReward):
    type: Literal['TraderUnlock']
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


class QuestTemplate(models.Base):
    class Config:
        fields = {
            'id': '_id'
        }
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

    conditions: Any
