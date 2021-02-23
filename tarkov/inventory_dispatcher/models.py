import enum
from types import SimpleNamespace
from typing import List, Literal, Optional

from pydantic import Extra, Field, StrictBool, StrictInt

from tarkov import models
from tarkov.fleamarket.models import OfferId
from tarkov.inventory.models import AnyMoveLocation, Item
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.models import Base


class ActionType(enum.Enum):
    Eat = "Eat"
    Heal = "Heal"
    RestoreHealth = "RestoreHealth"

    CustomizationWear = "CustomizationWear"
    CustomizationBuy = "CustomizationBuy"

    HideoutUpgrade = "HideoutUpgrade"
    HideoutUpgradeComplete = "HideoutUpgradeComplete"
    HideoutContinuousProductionStart = "HideoutContinuousProductionStart"
    HideoutSingleProductionStart = "HideoutSingleProductionStart"
    HideoutScavCaseProductionStart = "HideoutScavCaseProductionStart"
    HideoutTakeProduction = "HideoutTakeProduction"
    HideoutPutItemsInAreaSlots = "HideoutPutItemsInAreaSlots"
    HideoutTakeItemsFromAreaSlots = "HideoutTakeItemsFromAreaSlots"
    HideoutToggleArea = "HideoutToggleArea"

    Insure = "Insure"
    Move = "Move"
    Remove = "Remove"
    Split = "Split"
    Merge = "Merge"
    Transfer = "Transfer"
    Swap = "Swap"

    AddNote = "AddNote"
    EditNote = "EditNote"
    DeleteNote = "DeleteNote"

    QuestAccept = "QuestAccept"
    QuestComplete = "QuestComplete"
    QuestHandover = "QuestHandover"

    RagFairBuyOffer = "RagFairBuyOffer"
    RagFairAddOffer = "RagFairAddOffer"

    Repair = "Repair"
    Fold = "Fold"
    Toggle = "Toggle"
    Tag = "Tag"
    Bind = "Bind"
    Examine = "Examine"
    ReadEncyclopedia = "ReadEncyclopedia"
    TradingConfirm = "TradingConfirm"

    SaveBuild = "SaveBuild"
    RemoveBuild = "RemoveBuild"

    AddToWishList = "AddToWishList"
    RemoveFromWishList = "RemoveFromWishList"

    ApplyInventoryChanges = "ApplyInventoryChanges"


class ActionModel(models.Base):
    class Config:
        extra = Extra.forbid
        use_enum_values = True

    Action: ActionType


class InventoryExamineActionOwnerModel(models.Base):
    id: ItemId
    type: Optional[Literal["Trader", "HideoutUpgrade", "HideoutProduction", "RagFair"]] = None


class Owner(models.Base):
    id: str
    type: Literal["Mail"]


class InventoryActions(SimpleNamespace):
    class ApplyInventoryChanges(ActionModel):
        changedItems: Optional[List[Item]]
        deletedItems: Optional[List[Item]]

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


class HideoutActions(SimpleNamespace):
    class Upgrade(ActionModel):
        areaType: StrictInt
        items: List[dict]
        timestamp: StrictInt

    class UpgradeComplete(ActionModel):
        areaType: StrictInt
        timestamp: StrictInt

    class PutItemsInAreaSlots(ActionModel):
        areaType: StrictInt
        items: dict
        timestamp: StrictInt

    class ToggleArea(ActionModel):
        areaType: StrictInt
        enabled: bool
        timestamp: StrictInt

    class TakeItemsFromAreaSlots(ActionModel):
        areaType: StrictInt
        slots: List[StrictInt]
        timestamp: StrictInt

    class SingleProductionStart(ActionModel):
        recipeId: str
        items: List[dict]
        timestamp: StrictInt

    class TakeProduction(ActionModel):
        recipeId: str
        timestamp: StrictInt


class TradingSchemeItemModel(models.Base):
    id: ItemId
    count: StrictInt
    scheme_id: Optional[int]


class TradingActions(SimpleNamespace):
    class Trading(ActionModel):
        class Config:
            extra = Extra.allow

        type: Literal["buy_from_trader", "sell_to_trader"]

    class BuyFromTrader(Trading):
        class Config:
            extra = Extra.forbid

        tid: str
        item_id: ItemId
        count: StrictInt
        scheme_id: StrictInt
        scheme_items: List[TradingSchemeItemModel]

    class SellToTrader(Trading):
        class Config:
            extra = Extra.forbid

        tid: str
        items: List[TradingSchemeItemModel]


class QuestHandoverItem(models.Base):
    id: ItemId
    count: int


class QuestActions(SimpleNamespace):
    class Accept(ActionModel):
        qid: str

    class Handover(ActionModel):
        qid: str
        conditionId: str
        items: List[QuestHandoverItem]

    class Complete(ActionModel):
        qid: str
        removeExcessItems: StrictBool


class RequiredItem(Base):
    id: ItemId
    count: int


class RagfairBuyOffer(Base):
    offer_id: OfferId = Field(alias="id")
    count: int
    requirements: List[RequiredItem] = Field(alias="items")


class RagfairOfferRequirement(Base):
    template_id: TemplateId = Field(alias="_tpl")
    count: int
    level: int
    side: int
    onlyFunctional: bool


class RagfairActions(SimpleNamespace):
    class Buy(ActionModel):
        Action: ActionType
        offers: List[RagfairBuyOffer]

    class Add(ActionModel):
        Action: ActionType
        sellInOnePiece: bool
        items: List[ItemId]
        requirements: List[RagfairOfferRequirement]
