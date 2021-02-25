from typing import List

from pydantic import Field

from tarkov import models
from tarkov.fleamarket.models import OfferId
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.inventory_dispatcher.models import ActionModel, ActionType


class RequiredItem(models.Base):
    id: ItemId
    count: int


class RagfairBuyOffer(models.Base):
    offer_id: OfferId = Field(alias="id")
    count: int
    requirements: List[RequiredItem] = Field(alias="items")


class RagfairOfferRequirement(models.Base):
    template_id: TemplateId = Field(alias="_tpl")
    count: int
    level: int
    side: int
    onlyFunctional: bool


class Buy(ActionModel):
    Action: ActionType
    offers: List[RagfairBuyOffer]


class Add(ActionModel):
    Action: ActionType
    sellInOnePiece: bool
    items: List[ItemId]
    requirements: List[RagfairOfferRequirement]
