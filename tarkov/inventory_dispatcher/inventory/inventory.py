from typing import List, Optional, TYPE_CHECKING, Tuple

import tarkov.inventory
from tarkov.exceptions import NotFoundError
from tarkov.fleamarket.fleamarket import flea_market_instance
from tarkov.fleamarket.models import OfferId
from tarkov.inventory import MutableInventory, item_templates_repository
from tarkov.inventory.implementations import SimpleInventory
from tarkov.inventory.models import Item
from tarkov.inventory.types import TemplateId
from tarkov.inventory_dispatcher.models import ActionType, Owner
from tarkov.trader import TraderType
from tarkov.inventory_dispatcher.base import Dispatcher
from tarkov.trader.trader import Trader

from .models import (
    ApplyInventoryChanges,
    Examine,
    Fold,
    Insure,
    Merge,
    Move,
    ReadEncyclopedia,
    Remove,
    Repair,
    Split,
    Transfer,
)

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory_dispatcher.manager import DispatcherManager


class InventoryDispatcher(Dispatcher):
    def __init__(self, manager: "DispatcherManager"):
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.Move: self._move,
            ActionType.Split: self._split,
            ActionType.Examine: self._examine,
            ActionType.Merge: self._merge,
            ActionType.Transfer: self._transfer,
            ActionType.Fold: self._fold,
            ActionType.Remove: self._remove,
            ActionType.ReadEncyclopedia: self._read_encyclopedia,
            ActionType.Insure: self._insure,
            ActionType.ApplyInventoryChanges: self._apply_inventory_changes,
            ActionType.Repair: self._repair,
        }

    def get_owner_inventory(self, owner: Optional[Owner] = None) -> MutableInventory:
        if owner is None:
            return self.inventory

        if owner.type == "Mail":
            message = self.profile.mail.get_message(owner.id)
            return SimpleInventory(message.items.data)

        raise ValueError(f"Cannot find inventory for owner: {owner}")

    def _move(self, action: Move) -> None:
        donor_inventory = self.get_owner_inventory(action.fromOwner)
        item = donor_inventory.get(action.item)

        self.inventory.move_item(
            item=item,
            move_location=action.to,
        )
        self.response.items.new.append(item)

    def _split(self, action: Split) -> None:
        donor_inventory = self.get_owner_inventory(action.fromOwner)
        item = donor_inventory.get(action.item)
        new_item = self.inventory.simple_split_item(item, count=action.count)

        self.inventory.move_item(new_item, move_location=action.container)

        if new_item:
            self.response.items.new.append(new_item.copy(deep=True))

    def _examine(self, action: Examine) -> None:
        item_id = action.item

        if action.fromOwner is None:
            item = self.inventory.get(item_id)
            self.profile.encyclopedia.examine(item)
            return

        if action.fromOwner.type == "Trader":
            trader_id = action.fromOwner.id

            trader_inventory = Trader(TraderType(trader_id), self.profile).inventory
            item = trader_inventory.get(item_id)
            self.profile.encyclopedia.examine(item)

        elif action.fromOwner.type in ("HideoutUpgrade", "HideoutProduction"):
            item_tpl_id = TemplateId(action.item)
            self.profile.encyclopedia.examine(item_tpl_id)

        elif action.fromOwner.type == "RagFair":
            try:
                offer = flea_market_instance.get_offer(OfferId(action.fromOwner.id))
            except NotFoundError:
                self.response.append_error(title="Item examination error", message="Offer can not be found")
                return

            item = offer.root_item
            assert action.item == item.id
            self.profile.encyclopedia.examine(item)

    def _merge(self, action: Merge) -> None:
        donor_inventory = self.get_owner_inventory(action.fromOwner)
        item = donor_inventory.get(item_id=action.item)
        with_ = self.inventory.get(action.with_)

        self.inventory.merge(item=item, with_=with_)

        self.response.items.del_.append(item)
        self.response.items.change.append(with_)

    def _transfer(self, action: Transfer) -> None:
        donor_inventory = self.get_owner_inventory(action.fromOwner)
        item = donor_inventory.get(item_id=action.item)
        with_ = self.inventory.get(action.with_)

        self.inventory.transfer(item=item, to=with_, count=action.count)
        self.response.items.change.extend((item, with_))

    def _fold(self, action: Fold) -> None:
        item = self.inventory.get(action.item)
        self.inventory.fold(item, action.value)

    def _remove(self, action: Remove) -> None:
        item = self.inventory.get(action.item)
        self.inventory.remove_item(item)

        self.response.items.del_.append(item)

    def _read_encyclopedia(self, action: ReadEncyclopedia) -> None:
        for template_id in action.ids:
            self.profile.encyclopedia.read(template_id)

    def _apply_inventory_changes(self, action: ApplyInventoryChanges) -> None:
        if action.changedItems is not None:
            changed_items: List[Tuple[Item, List[Item]]] = []
            for changed_item in action.changedItems:
                item = self.inventory.get(changed_item.id)
                child_items = list(self.inventory.iter_item_children_recursively(item))
                self.inventory.remove_item(item, remove_children=True)
                changed_items.append((item, child_items))

            for item, child_items in changed_items:
                self.inventory.add_item(item=item, child_items=child_items)

        if action.deletedItems is not None:
            for deleted_item in action.deletedItems:
                item = self.profile.inventory.get(deleted_item.id)
                self.profile.inventory.remove_item(item)
                self.response.items.del_.append(item)

    def _insure(self, action: Insure) -> None:
        trader = TraderType(action.tid)
        trader_inventory = Trader(
            TraderType(action.tid),
            profile=self.profile,
        )

        rubles_tpl_id = tarkov.inventory.types.TemplateId("5449016a4bdc2d6f028b456f")
        total_price = 0
        for item_id in action.items:
            item = self.profile.inventory.get(item_id)
            total_price += trader_inventory.calculate_insurance_price(item)
            self.profile.add_insurance(item, trader)

        affected_items, deleted_items = self.profile.inventory.take_item(rubles_tpl_id, total_price)

        self.response.items.change.extend(affected_items)
        self.response.items.del_.extend(deleted_items)

    def _repair(self, action: Repair) -> None:
        trader = Trader(TraderType(action.tid), self.profile)
        try:
            price_rate: float = 1 + trader.base.repair.price_rate / 100
        except ZeroDivisionError:
            price_rate = 1

        for repair_item in action.repairItems:
            item = self.inventory.get(repair_item.item_id)
            item_template = item_templates_repository.get_template(item.tpl)
            repair_cost_per_1_durability = item_template.props.RepairCost

            if item.upd.FaceShield is not None:
                item.upd.FaceShield.Hits = 0

            assert item.upd.Repairable is not None
            new_durability = item.upd.Repairable.Durability + repair_item.count
            item.upd.Repairable.MaxDurability = new_durability
            item.upd.Repairable.Durability = new_durability
            self.response.items.change.append(item)

            total_repair_cost: int = round(repair_cost_per_1_durability * price_rate)

            assert trader.base.repair.currency is not None
            while total_repair_cost > 0:
                currency_item = self.inventory.get_by_template(trader.base.repair.currency)
                amount_to_take = min(currency_item.upd.StackObjectsCount, total_repair_cost)
                currency_item.upd.StackObjectsCount -= amount_to_take

                total_repair_cost -= amount_to_take

                if not currency_item.upd.StackObjectsCount:
                    self.response.items.del_.append(currency_item.copy(deep=True))
                    self.inventory.remove_item(currency_item)
                else:
                    self.response.items.change.append(currency_item)