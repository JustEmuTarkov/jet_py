from typing import List

from pydantic import StrictBool

from tarkov import models
from tarkov.inventory.types import ItemId
from tarkov.inventory_dispatcher.models import ActionModel


class QuestHandoverItem(models.Base):
    id: ItemId
    count: int


class Accept(ActionModel):
    qid: str


class Handover(ActionModel):
    qid: str
    conditionId: str
    items: List[QuestHandoverItem]


class Complete(ActionModel):
    qid: str
    removeExcessItems: StrictBool
