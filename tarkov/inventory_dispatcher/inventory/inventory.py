from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, List, Optional, TYPE_CHECKING, Tuple

from dependency_injector.wiring import Provide, inject

import tarkov.inventory
from tarkov.exceptions import NotFoundError
from tarkov.fleamarket.models import OfferId
from tarkov.inventory.implementations import SimpleInventory
from tarkov.inventory.inventory import MutableInventory
from tarkov.inventory.models import Item, ItemUpdTogglable
from tarkov.inventory.types import TemplateId
from tarkov.inventory_dispatcher.base import Dispatcher
from tarkov.inventory_dispatcher.models import ActionType, Owner
from tarkov.trader import TraderType
from tarkov.trader.trader import Trader
from .models import (
    ApplyInventoryChanges,
    Bind,
    Examine,
    Fold,
    Insure,
    Merge,
    Move,
    ReadEncyclopedia,
    Remove,
    Repair,
    Split,
    Swap,
    Toggle,
    Transfer,
)
from tarkov.containers.repositories import RepositoriesContainer
from tarkov.fleamarket.containers import FleaMarketContainer


if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory_dispatcher.manager import DispatcherManager
    from tarkov.fleamarket.fleamarket import FleaMarket
    from tarkov.inventory.repositories import ItemTemplatesRepository


class InventoryDispatcher(Dispatcher):
    @inject
    def __init__(
        self,
        manager: "DispatcherManager",
        flea_market: FleaMarket = Provide[FleaMarketContainer.market],
        templates_repository: ItemTemplatesRepository = Provide[RepositoriesContainer.templates],
    ):
        super().__init__(manager)
        self.flea_market = flea_market
        self.templates_repository = templates_repository

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
            ActionType.Bind: self._bind,
            ActionType.Swap: self._swap,
            ActionType.Toggle: self._toggle,
        }

    @contextmanager
    def owner_inventory(self, owner: Optional[Owner] = None) -> Iterator[MutableInventory]:
        if owner is None:
            yield self.inventory
            return

        if owner.type == "Mail":
            message = self.profile.mail.get_message(owner.id)
            message_inventory = SimpleInventory(message.items.data)
            yield message_inventory
            message.items.data = list(message_inventory.items.values())
            return

        raise ValueError(f"Cannot find inventory for owner: {owner}")

    def _move(self, action: Move) -> None:
        with self.owner_inventory(action.fromOwner) as owner_inventory:
            item = owner_inventory.get(action.item)

            self.inventory.move_item(
                item=item,
                move_location=action.to,
            )
            self.response.items.change.append(item)

    def _split(self, action: Split) -> None:
        with self.owner_inventory(action.fromOwner) as owner_inventory:
            item = owner_inventory.get(action.item)
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
                offer = self.flea_market.get_offer(OfferId(action.fromOwner.id))
            except NotFoundError:
                self.response.append_error(title="Item examination error", message="Offer can not be found")
                return

            item = offer.root_item
            assert action.item == item.id
            self.profile.encyclopedia.examine(item)

    def _merge(self, action: Merge) -> None:
        with self.owner_inventory(action.fromOwner) as owner_inventory:
            item = owner_inventory.get(item_id=action.item)
            with_ = self.inventory.get(action.with_)

            self.inventory.merge(item=item, with_=with_)

            self.response.items.del_.append(item)
            self.response.items.change.append(with_)

    def _transfer(self, action: Transfer) -> None:
        with self.owner_inventory(action.fromOwner) as owner_inventory:
            item = owner_inventory.get(item_id=action.item)
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
                changed_items.append((changed_item, child_items))
                self.inventory.remove_item(item, remove_children=True)

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
            item_template = self.templates_repository.get_template(item.tpl)
            repair_cost_per_1_durability = item_template.props.RepairCost

            if item.upd.FaceShield is not None:
                item.upd.FaceShield.Hits = 0

            assert item.upd.Repairable is not None
            new_durability = item.upd.Repairable.Durability + repair_item.count
            item.upd.Repairable.MaxDurability = new_durability
            item.upd.Repairable.Durability = new_durability
            self.response.items.change.append(item)

            total_repair_cost: int = round(repair_cost_per_1_durability * price_rate * repair_item.count)

            assert trader.base.repair.currency is not None
            affected, deleted = self.inventory.take_item(trader.base.repair.currency, total_repair_cost)
            self.response.items.change.extend(affected)
            self.response.items.del_.extend(deleted)

    def _bind(self, action: Bind) -> None:
        fast_panel = self.inventory.inventory.fastPanel

        keys_to_delete = {k for k, v in fast_panel.items() if v == action.item}

        for k in keys_to_delete:
            del fast_panel[k]

        fast_panel[action.index] = action.item

    def _swap(self, action: Swap) -> None:
        with self.owner_inventory(action.fromOwner) as owner_inventory:
            item = owner_inventory.get(action.item)
            item2 = owner_inventory.get(action.item2)

            self.inventory.move_item(
                item=item,
                move_location=action.to,
            )
            self.inventory.move_item(
                item=item2,
                move_location=action.to2,
            )

            self.response.items.change.append(item)
            self.response.items.change.append(item2)

    def _toggle(self, action: Toggle) -> None:
        item = self.inventory.get(action.item)
        item.upd.Togglable = ItemUpdTogglable(On=action.value)
        self.response.items.change.append(item)
