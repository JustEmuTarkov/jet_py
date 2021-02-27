from typing import List, Literal, Optional

from pydantic import Field, StrictBool, StrictInt

from tarkov import models
from tarkov.inventory.models import AnyMoveLocation, Item
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.inventory_dispatcher.models import ActionModel, Owner


class ApplyInventoryChanges(ActionModel):
    changedItems: Optional[List[Item]]
    deletedItems: Optional[List[Item]]


class InventoryExamineActionOwnerModel(models.Base):
    id: ItemId
    type: Optional[Literal["Trader", "HideoutUpgrade", "HideoutProduction", "RagFair"]] = None


class Examine(ActionModel):
    item: ItemId
    fromOwner: Optional[InventoryExamineActionOwnerModel] = None


class Split(ActionModel):
    item: ItemId
    container: AnyMoveLocation
    count: StrictInt
    fromOwner: Optional[Owner] = None


class Move(ActionModel):
    item: ItemId
    to: AnyMoveLocation
    fromOwner: Optional[Owner] = None


class Merge(ActionModel):
    class Config:
        fields = {"with_": "with"}

    item: ItemId
    with_: ItemId
    fromOwner: Optional[Owner] = None


class Transfer(Merge):
    count: int


class Fold(ActionModel):
    item: ItemId
    value: StrictBool


class Remove(ActionModel):
    item: ItemId


class ReadEncyclopedia(ActionModel):
    ids: List[TemplateId]


class Insure(ActionModel):
    items: List[ItemId]
    tid: str


class Bind(ActionModel):
    item: ItemId
    index: str


class RepairItem(models.Base):
    item_id: ItemId = Field(alias="_id")
    count: float


class Repair(models.Base):
    Action: Literal["Repair"]
    tid: str
    repairItems: List[RepairItem]


class Swap(ActionModel):
    item: ItemId
    to: AnyMoveLocation
    item2: ItemId
    to2: AnyMoveLocation
    fromOwner: Optional[Owner] = None
