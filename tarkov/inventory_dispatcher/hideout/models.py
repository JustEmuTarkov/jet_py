from typing import List

from pydantic import StrictInt

from tarkov.inventory_dispatcher.models import ActionModel


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
