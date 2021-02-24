import enum
from typing import Literal

from pydantic import Extra

from tarkov import models


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


class Owner(models.Base):
    id: str
    type: Literal["Mail"]
