from typing import TYPE_CHECKING

import tarkov.inventory
from tarkov.inventory import generate_item_id, item_templates_repository
from tarkov.inventory.models import Item
from tarkov.inventory.types import TemplateId
from tarkov.inventory_dispatcher.models import ActionType
from tarkov.trader import TraderType

from tarkov.inventory_dispatcher.base import Dispatcher
from tarkov.trader.trader import Trader

from .models import BuyFromTrader, SellToTrader, Trading

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory_dispatcher.manager import DispatcherManager


class TradingDispatcher(Dispatcher):
    def __init__(self, manager: "DispatcherManager"):
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.TradingConfirm: self._trading_confirm,
        }

    def _trading_confirm(self, action: Trading) -> None:
        if action.type == "buy_from_trader":
            self.__buy_from_trader(BuyFromTrader(**action.dict()))
            return

        if action.type == "sell_to_trader":
            self.__sell_to_trader(SellToTrader(**action.dict()))
            return

        raise NotImplementedError(f"Trading action {action} not implemented")

    def __buy_from_trader(self, action: BuyFromTrader) -> None:
        trader = Trader(TraderType(action.tid), self.profile)

        bought_items_list = trader.buy_item(action.item_id, action.count)

        for bought_item in bought_items_list:
            item = bought_item.item
            children = bought_item.children_items

            self.inventory.place_item(item, child_items=children)

            self.response.items.new.append(item.copy(deep=True))
            self.response.items.new.extend(c.copy(deep=True) for c in children)

        # Take required items from inventory
        for scheme_item in action.scheme_items:
            self.profile.pmc_profile.TraderStandings[action.tid].current_sales_sum += scheme_item.count
            item = self.inventory.get(scheme_item.id)
            item.upd.StackObjectsCount -= scheme_item.count
            if not item.upd.StackObjectsCount:
                self.inventory.remove_item(item)
                self.response.items.del_.append(item)
            else:
                self.response.items.change.append(item)

        self.response.currentSalesSums[action.tid] = trader.standing.current_sales_sum

    def __sell_to_trader(self, action: SellToTrader) -> None:
        trader_id = action.tid
        items_to_sell = action.items
        trader_inventory = Trader(TraderType(trader_id), self.profile)

        items = list(self.inventory.get(i.id) for i in items_to_sell)
        price_sum: int = sum(trader_inventory.get_sell_price(item) for item in items)

        self.response.items.del_.extend(items)
        self.inventory.remove_items(items)

        rubles_tpl = item_templates_repository.get_template(
            tarkov.inventory.types.TemplateId("5449016a4bdc2d6f028b456f")
        )
        money_max_stack_size = rubles_tpl.props.StackMaxSize

        while price_sum:
            stack_size = min(money_max_stack_size, price_sum)
            price_sum -= stack_size

            money_stack = Item(
                id=generate_item_id(),
                tpl=TemplateId("5449016a4bdc2d6f028b456f"),
                parent_id=self.inventory.root_id,
                slot_id="hideout",
            )
            money_stack.upd.StackObjectsCount = stack_size

            self.inventory.place_item(money_stack)
            self.response.items.new.append(money_stack)
