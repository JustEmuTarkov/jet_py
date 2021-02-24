from typing import TYPE_CHECKING

from tarkov.hideout.models import HideoutAreaType
from tarkov.inventory_dispatcher.models import ActionType
from tarkov.inventory_dispatcher.base import Dispatcher

from .models import (
    PutItemsInAreaSlots,
    SingleProductionStart,
    TakeItemsFromAreaSlots,
    TakeProduction,
    ToggleArea,
    Upgrade,
    UpgradeComplete,
)

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory_dispatcher.manager import DispatcherManager


class HideoutDispatcher(Dispatcher):
    def __init__(self, manager: "DispatcherManager"):
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.HideoutUpgrade: self._hideout_upgrade_start,
            ActionType.HideoutUpgradeComplete: self._hideout_upgrade_finish,
            ActionType.HideoutPutItemsInAreaSlots: self._hideout_put_items_in_area_slots,
            ActionType.HideoutToggleArea: self._hideout_toggle_area,
            ActionType.HideoutSingleProductionStart: self._hideout_single_production_start,
            ActionType.HideoutTakeProduction: self._hideout_take_production,
            ActionType.HideoutTakeItemsFromAreaSlots: self._hideout_take_items_from_area_slots,
        }

    def _hideout_upgrade_start(self, action: Upgrade) -> None:
        hideout = self.profile.hideout

        area_type = HideoutAreaType(action.areaType)
        hideout.area_upgrade_start(area_type)

        items_required = action.items
        for item_required in items_required:
            count = item_required["count"]
            item_id = item_required["id"]

            item = self.profile.inventory.get(item_id)
            item.upd.StackObjectsCount -= count
            if not item.upd.StackObjectsCount:
                self.profile.inventory.remove_item(item)
                self.response.items.del_.append(item)
            else:
                self.response.items.change.append(item)

    def _hideout_upgrade_finish(self, action: UpgradeComplete) -> None:
        hideout = self.profile.hideout

        area_type = HideoutAreaType(action.areaType)
        hideout.area_upgrade_finish(area_type)

    def _hideout_put_items_in_area_slots(self, action: PutItemsInAreaSlots) -> None:
        area_type = HideoutAreaType(action.areaType)

        for slot_id, item_data in action.items.items():
            count, item_id = item_data["count"], item_data["id"]
            item = self.profile.inventory.get(item_id)

            if self.profile.inventory.can_split(item):
                splitted_item = self.profile.inventory.simple_split_item(item=item, count=count)
                self.profile.hideout.put_items_in_area_slots(area_type, int(slot_id), splitted_item)
            else:
                self.profile.inventory.remove_item(item)
                self.profile.hideout.put_items_in_area_slots(area_type, int(slot_id), item)

    def _hideout_toggle_area(self, action: ToggleArea) -> None:
        area_type = HideoutAreaType(action.areaType)
        self.profile.hideout.toggle_area(area_type, action.enabled)

    def _hideout_single_production_start(self, action: SingleProductionStart) -> None:
        items_info = action.items
        inventory = self.profile.inventory

        for item_info in items_info:
            item_id = item_info["id"]
            count = item_info["count"]

            item = inventory.get(item_id=item_id)

            if not inventory.can_split(item):
                inventory.remove_item(item)
                self.response.items.del_.append(item)
                continue

            inventory.simple_split_item(item=item, count=count)  # Simply throw away splitted item
            if not item.upd.StackObjectsCount:
                self.response.items.del_.append(item)
            else:
                self.response.items.change.append(item)

        self.profile.hideout.start_single_production(recipe_id=action.recipeId)

    def _hideout_take_production(self, action: TakeProduction) -> None:
        items = self.profile.hideout.take_production(action.recipeId)
        self.response.items.new.extend(items)
        for item in items:
            self.inventory.place_item(item)

    def _hideout_take_items_from_area_slots(self, action: TakeItemsFromAreaSlots) -> None:
        hideout = self.profile.hideout
        area_type = HideoutAreaType(action.areaType)
        for slot_id in action.slots:
            item = hideout.take_item_from_area_slot(area_type=area_type, slot_id=slot_id)

            self.inventory.place_item(item)
            self.response.items.new.append(item)
