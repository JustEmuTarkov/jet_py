from __future__ import annotations

import math
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List

from server import logger
from tarkov import config
from tarkov.exceptions import NotFoundError
from tarkov.inventory.models import Item, ItemTemplate
from tarkov.inventory.types import TemplateId
from .models import Offer, OfferId
from .offer_generator import OfferGenerator
from .views import FleaMarketView


class FleaMarket:
    offers_amount: int
    updated_at: datetime
    generator: OfferGenerator
    _view: FleaMarketView
    offers: Dict[OfferId, Offer]

    def __init__(self) -> None:
        self.offers_amount = config.flea_market.offers_amount

        self.updated_at = datetime.fromtimestamp(0)

        self.generator = OfferGenerator(self)
        self._view = FleaMarketView(self)
        self.offers = {}

    def get_offer(self, offer_id: OfferId) -> Offer:
        """
        Returns specific offer by it's id
        """
        try:
            return self.offers[offer_id]
        except KeyError as error:
            raise NotFoundError from error

    def remove_offer(self, offer: Offer) -> None:
        """
        Simply deletes offer
        """
        del self.offers[offer.id]

    def item_price_view(self, template_id: TemplateId) -> dict:
        """
        Calculates min, max and average price of item on flea. Used by client when selling items.
        """
        offers = [offer for offer in self.offers.values() if offer.root_item.tpl == template_id]
        if not offers:
            return {
                "min": 0,
                "max": 0,
                "avg": 0,
            }
        offers_costs = [offer.itemsCost for offer in offers]
        mean_price = statistics.mean(offers_costs)
        max_price = max(offers_costs)
        min_price = min(offers_costs)
        return {
            "avg": mean_price,
            "min": min_price,
            "max": max_price,
        }

    def items_price(self, items: List[Item]) -> int:
        return int(sum(self.generator.item_prices[item.tpl] * item.upd.StackObjectsCount for item in items))

    def selling_time(self, items: List[Item], selling_price: int) -> timedelta:
        """
        Returns selling time items with given price
        """
        items_price = self.items_price(items)
        base_selling_time = math.log(items_price, 3)
        time_sell_minutes = base_selling_time ** ((selling_price / items_price) ** 1.3) - 1
        time_sell_minutes = min(time_sell_minutes, 2 ** 31)
        return timedelta(minutes=time_sell_minutes)

    @staticmethod
    def get_offer_tax(template: ItemTemplate, requirements_cost: int, quantity: int) -> int:
        """
        Returns tax for selling specific item
        """
        # pylint: disable=invalid-name
        # Formula is taken from tarkov wiki
        # TODO: Players that have intel level 3 have their tax reduced by 30%
        tax_constant = 0.05
        base_price = template.props.CreditsPrice

        p0 = math.log10(base_price / requirements_cost)
        if requirements_cost < base_price:
            p0 = p0 ** 1.08

        pr = math.log10(requirements_cost / base_price)
        if requirements_cost >= base_price:
            pr = pr ** 1.08

        tax = round(
            base_price * tax_constant * 4 ** p0 * quantity
            + requirements_cost * tax_constant * 4 ** pr * quantity
        )
        return tax

    def __clear_expired_offers(self) -> None:
        """
        Deletes offers that are expired
        """
        now = datetime.now()
        now_timestamp = now.timestamp()
        expired_offers_keys = [key for key, offer in self.offers.items() if now_timestamp > offer.endTime]

        for key in expired_offers_keys:
            del self.offers[key]

    def __update_offers(self) -> None:
        """
        Clears expired offers and generates new ones until we have desired amount
        """
        self.__clear_expired_offers()

        now = datetime.now()
        time_elapsed = now - self.updated_at
        self.updated_at = now

        try:
            keys_to_delete = random.sample(list(self.offers.keys()), k=int(time_elapsed.total_seconds()))
        except ValueError:
            keys_to_delete = []

        for key in keys_to_delete:
            del self.offers[key]

        new_offers_amount: int = self.offers_amount - len(self.offers)
        new_offers = self.generator.generate_offers(new_offers_amount)
        logger.debug(f"Generated {len(new_offers)} items!")
        self.offers.update(new_offers)

    @property
    def view(self) -> FleaMarketView:
        self.__update_offers()
        return self._view


flea_market_instance = FleaMarket()
