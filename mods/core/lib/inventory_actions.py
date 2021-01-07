from __future__ import annotations

import enum
from typing import TypedDict, List

from mods.core.lib.items import MoveLocation, ItemId


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
    RagFairAddOffer = "RagFairAddOffer"
    Repair = "Repair"
    Fold = "Fold"
    Toggle = "Toggle"
    Tag = "Tag"
    Bind = "Bind"
    Examine = "Examine"
    ReadEncyclopedia = "ReadEncyclopedia"
    TradingConfirm = "TradingConfirm"
    RagFairBuyOffer = "RagFairBuyOffer"
    SaveBuild = "SaveBuild"
    RemoveBuild = "RemoveBuild"
    AddToWishList = "AddToWishList"
    RemoveFromWishList = "RemoveFromWishList"
    ApplyInventoryChanges = "ApplyInventoryChanges"


class Action(TypedDict):
    Action: ActionType


class MoveAction(Action):
    item: ItemId
    to: MoveLocation


class SplitAction(Action):
    item: ItemId
    container: MoveLocation
    count: int


class FoldAction(Action):
    item: ItemId
    value: bool


# class MergeAction(Action):
#     item: str
#     to: str
#     with: str
MergeAction = TypedDict('MergeAction', {'Action': ActionType, 'item': ItemId, 'with': ItemId})


class TransferAction(MergeAction):
    count: int


class ExamineActionOwner(TypedDict):
    id: ItemId
    type: str


class ExamineAction(Action, total=False):
    item: ItemId
    fromOwner: ExamineActionOwner


class TradingSchemeItem(TypedDict):
    id: ItemId
    count: int
    scheme_id: int


class TradingAction(Action):
    type: str


class TradingConfirmAction(TradingAction):
    tid: str
    item_id: str
    count: int
    scheme_id: int
    scheme_items: List[TradingSchemeItem]


class TradingSellAction(TradingAction):
    tid: str
    items: List[TradingSchemeItem]


class ItemRemoveAction(Action):
    item: ItemId


class QuestAcceptAction(Action):
    qid: str


class ReadEncyclopediaAction(Action):
    ids: List[str]
