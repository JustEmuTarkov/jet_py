from __future__ import annotations

import enum
from typing import TypedDict, Literal, Union, List


class Stash(TypedDict):
    equipment: str
    stash: str
    questRaidItems: str
    questStashItems: str
    fastPanel: dict
    items: List[Item]


class ItemBase(TypedDict):
    _id: str
    _tpl: str


class Item(ItemBase, total=False):
    slotId: str
    parentId: str
    location: Union[ItemLocation, int]
    upd: ItemUpd


class ItemUpd(TypedDict, total=False):
    StackObjectsCount: int
    SpawnedInSession: bool
    Repairable: ItemUpdRepairable
    Foldable: ItemUpdFoldable
    FireMode: ItemUpdFireMode


class ItemUpdRepairable(TypedDict):
    MaxDurability: int
    Durability: int


class ItemUpdFoldable(TypedDict):
    Folded: bool


class ItemUpdFireMode(TypedDict):
    FireMode: Literal['single']


class ItemLocation(TypedDict):
    x: int
    y: int
    r: ItemOrientation
    isSearched: bool


class ItemExtraSize(TypedDict):
    up: int
    down: int
    left: int
    right: int


class ItemNotFoundError(Exception):
    pass


ItemOrientation = Literal['Horizontal', 'Vertical']


class MoveLocation(TypedDict):
    id: str
    container: str
    location: ItemLocation


class MoveAction(TypedDict):
    Action: ActionType
    item: str
    to: MoveLocation


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
