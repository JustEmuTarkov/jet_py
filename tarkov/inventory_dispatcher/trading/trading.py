from typing import TYPE_CHECKING

from tarkov.inventory.helpers import generate_item_id
from tarkov.inventory.models import Item
from tarkov.inventory.types import CurrencyEnum, TemplateId
from tarkov.inventory_dispatcher.base import Dispatcher
from tarkov.inventory_dispatcher.models import ActionType
from tarkov.trader.models import TraderType
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
        trader = Trader(TraderType(action.tid))

        bought_items_list = trader.buy_item(action.item_id, action.count)

        for bought_item in bought_items_list:
            item = bought_item.item
            children = bought_item.children_items

            self.inventory.place_item(item, child_items=children)

            self.response.items.new.append(item.copy(deep=True))
            self.response.items.new.extend(c.copy(deep=True) for c in children)

        # Take required items from inventory
        for scheme_item in action.scheme_items:
            self.profile.pmc.TraderStandings[action.tid].current_sales_sum += scheme_item.count
            item = self.inventory.get(scheme_item.id)
            item.upd.StackObjectsCount -= scheme_item.count
            if not item.upd.StackObjectsCount:
                self.inventory.remove_item(item)
                self.response.items.del_.append(item)
            else:
                self.response.items.change.append(item)

        trader_view = trader.view(self.profile)
        self.response.currentSalesSums[action.tid] = trader_view.standing.current_sales_sum

    def __sell_to_trader(self, action: SellToTrader) -> None:
        trader_id = action.tid
        items_to_sell = action.items
        trader = Trader(TraderType(trader_id))
        trader_view = trader.view(self.profile)

        items = list(self.inventory.get(i.id) for i in items_to_sell)
        price_sum: int = sum(
            trader.get_sell_price(self.inventory.get(i.id), children_items=[]).amount for i in items_to_sell
        )
        # price_sum: int = sum(trader.get_sell_price(item, children_items=[]).amount for item in items)

        self.response.items.del_.extend(items)
        self.inventory.remove_items(items)

        currency_item = Item(
            id=generate_item_id(),
            tpl=TemplateId(CurrencyEnum[trader_view.base.currency].value),
        )
        currency_item.upd.StackObjectsCount = price_sum

        currency_items = self.inventory.split_into_stacks(currency_item)

        for item in currency_items:
            self.inventory.place_item(item)
        self.response.items.new.extend(currency_items)
