from datetime import datetime, timedelta
from typing import List, TYPE_CHECKING

from server import logger
from tarkov.exceptions import NotFoundError
from tarkov.fleamarket.fleamarket import flea_market_instance
from tarkov.inventory.models import Item
from tarkov.inventory_dispatcher.models import ActionType, RagfairActions
from tarkov.mail.models import MailDialogueMessage, MailMessageItems, MailMessageType
from tarkov.trader import TraderType
from .base import Dispatcher
from tarkov.inventory.factories import item_factory

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory_dispatcher.manager import DispatcherManager


class FleaMarketDispatcher(Dispatcher):
    def __init__(self, manager: "DispatcherManager") -> None:
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.RagFairBuyOffer: self._buy_offer,
            ActionType.RagFairAddOffer: self._add_offer,
        }

    def _buy_offer(self, action: RagfairActions.Buy) -> None:
        for offer_to_buy in action.offers:
            try:
                offer = flea_market_instance.get_offer(offer_to_buy.offer_id)
            except NotFoundError:
                self.response.append_error(
                    title="Flea Market Error",
                    message="Item is already bought",
                )
                return
            if not offer.sellInOnePiece:
                bough_stack = self.inventory.simple_split_item(offer.root_item, count=offer_to_buy.count)
                bough_items: List[Item] = self.inventory.split_into_stacks(bough_stack)
                for item in bough_items:
                    self.inventory.place_item(item)
                self.response.items.new.extend(bough_items)

                if not offer.root_item.upd.StackObjectsCount:
                    # I Guess flea market itself can delete offers like these
                    flea_market_instance.remove_offer(offer)
            else:
                bough_item, child_items = offer.get_items()
                flea_market_instance.remove_offer(offer)

                self.inventory.place_item(item=bough_item, child_items=child_items)
                self.response.items.new.append(bough_item)
                self.response.items.new.extend(child_items)

            # Take required items from inventory
            for req in offer_to_buy.requirements:
                item = self.inventory.get(req.id)
                if req.count == item.upd.StackObjectsCount:
                    self.inventory.remove_item(item)
                    self.response.items.del_.append(item)
                else:
                    item.upd.StackObjectsCount -= req.count
                    self.response.items.change.append(item)

    def _add_offer(self, action: RagfairActions.Add) -> None:
        # Todo: Add taxation
        items = [self.inventory.get(item_id) for item_id in action.items]
        self.response.items.del_.extend(item.copy(deep=True) for item in items)
        self.inventory.remove_items(items)

        required_items: List[Item] = []
        for requirement in action.requirements:
            # TODO: This will probably cause issues with nested items, create_item function have to be changed
            required_items_list = item_factory.create_items(requirement.template_id, requirement.count)
            for item, children in required_items_list:
                required_items.extend([item, *children])

        selling_price_rub = flea_market_instance.items_price(required_items)
        selling_time: timedelta = flea_market_instance.selling_time(items, selling_price_rub)
        logger.debug(f"Requirements cost in rubles: {selling_price_rub}")
        logger.debug(f"Selling time: {selling_time}")

        will_sell_in_24_h = selling_time < timedelta(days=1)
        if will_sell_in_24_h:
            # "5bdac0b686f7743e1665e09e": "Your {soldItem}  {itemCount} items was bought by {buyerNickname}",
            sent_at = datetime.now() + selling_time
            message = MailDialogueMessage(
                dt=int(sent_at.timestamp()),
                hasRewards=True,
                uid=TraderType.Ragman.value,
                type=MailMessageType.FleamarketMessage.value,
                templateId="5bdac0b686f7743e1665e09e",
                items=MailMessageItems.from_items(required_items),
                systemData={
                    "soldItem": items[0].tpl,
                    "itemCount": str(items[0].upd.StackObjectsCount),
                    "buyerNickname": "Nikita",
                },
            )
            self.profile.mail.add_message(message)

        else:
            #  "5bdac06e86f774296f5a19c5": "The item was not sold",
            sent_at = datetime.now() + timedelta(days=1)
            message = MailDialogueMessage(
                dt=int(sent_at.timestamp() + 5),
                hasRewards=True,
                uid=TraderType.Ragman.value,
                type=MailMessageType.FleamarketMessage.value,
                templateId="5bdac06e86f774296f5a19c5",
                items=MailMessageItems.from_items(items),
            )
            self.profile.mail.add_message(message)
