from __future__ import annotations

import math
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, TYPE_CHECKING

import pydantic
from dependency_injector.wiring import Provide, inject

from server import db_dir
from tarkov.globals_ import globals_repository
from tarkov.inventory import generate_item_id, item_templates_repository
from tarkov.inventory.factories import item_factory
from tarkov.inventory.models import Item, ItemTemplate
from tarkov.inventory.prop_models import AmmoProps
from tarkov.inventory.types import TemplateId
from tarkov.repositories.categories import category_repository
from .models import FleaUser, Offer, OfferId, OfferRequirement
from ..containers import ConfigContainer

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .fleamarket import FleaMarket
    from tarkov.config import FleaMarketConfig


class OfferGenerator:
    flea_market: FleaMarket

    item_prices: Dict[TemplateId, int]
    item_templates: List[ItemTemplate]
    item_templates_weights: List[float]

    percentile_high: float
    percentile_low: float

    @inject
    def __init__(
        self,
        config: FleaMarketConfig = Provide[ConfigContainer.flea_market],
    ) -> None:
        self.config = config
        # Creates dictionary with item prices from templates and updates it with prices from flea_prices.json
        self.item_prices = {
            tpl.id: tpl.props.CreditsPrice
            for tpl in item_templates_repository.templates.values()
            if tpl.id in category_repository.item_categories and tpl.props.CreditsPrice
        }
        item_prices: Dict[TemplateId, int] = pydantic.parse_file_as(
            Dict[TemplateId, int], db_dir.joinpath("flea_prices.json")
        )
        self.item_prices.update({tpl: price for tpl, price in item_prices.items() if price > 0})

        # Load seller usernames.
        self.seller_names = pydantic.parse_file_as(
            List[str], db_dir.joinpath("traders", "ragfair", "sellers.json")
        )

        # All the item templates that we have prices for
        self.item_templates = [
            tpl for tpl in item_templates_repository.templates.values() if tpl.id in self.item_prices
        ]
        prices = list(self.item_prices.values())
        median_price = statistics.median(prices)
        prices_sorted = sorted(prices)
        # Calculates low/high percentile, they're used to weight too cheap/expensive items
        self.percentile_high: int = prices_sorted[int(len(prices) * self.config.percentile_high)]
        self.percentile_low: int = prices_sorted[int(len(prices) * self.config.percentile_low)]

        self.item_templates_weights = [
            self._get_item_template_weight(tpl, median_price) for tpl in self.item_templates
        ]

    def _get_item_template_weight(self, template: ItemTemplate, median_price: float) -> float:
        """
        Calculates item spawn chance on flea market
        """
        if not template.props.CanSellOnRagfair:
            return 0
        item_price = self.item_prices[template.id]
        if isinstance(template.props, AmmoProps):
            item_price *= template.props.StackMaxSize  # So we don't have so much ammo
        chance_modifier: float = 1

        if item_price < self.percentile_low:
            chance_modifier = item_price / self.percentile_low
        if item_price > self.percentile_high:
            chance_modifier = self.percentile_high / item_price

        return math.log(self.item_prices[template.id], median_price) * chance_modifier

    def generate_offers(self, amount: int) -> Dict[OfferId, Offer]:
        """
        Generates multiple offers
        """
        offers = {}
        templates = random.choices(self.item_templates, weights=self.item_templates_weights, k=amount)
        for template in templates:
            offer = self._generate_offer(template)
            offers[offer.id] = offer
        return offers

    def _generate_offer(self, item_template: ItemTemplate) -> Offer:
        """
        Generates single offer
        """
        offer_items: List[Item]
        offer_price: int
        root_item: Item
        sell_in_one_piece = False

        if globals_repository.has_preset(item_template):
            preset = globals_repository.item_preset(item_template)
            root_item, children = preset.get_items()
            offer_items = [root_item, *children]
            sell_in_one_piece = True

        elif isinstance(item_template.props, AmmoProps):
            ammo_count = int(
                random.gauss(
                    item_template.props.StackMaxSize * 0.75,
                    item_template.props.StackMaxSize * 1.25,
                )
            )
            ammo_count = max(1, abs(ammo_count))
            root_item, _ = item_factory.create_item(item_template, 1)
            offer_items = [root_item]
            root_item.upd.StackObjectsCount = ammo_count
        else:
            root_item, child_items = item_factory.create_item(item_template)
            offer_items = [root_item, *child_items]

        offer_price = sum(self.item_prices[i.tpl] for i in offer_items)
        offer_price = int(random.gauss(offer_price * 1.1, offer_price * 0.1))

        requirement = OfferRequirement(
            template_id=TemplateId("5449016a4bdc2d6f028b456f"),
            count=offer_price,
        )
        now = datetime.now()
        expiration_time = random.gauss(timedelta(hours=6).total_seconds(), timedelta(hours=6).total_seconds())
        expires_at = now + timedelta(seconds=abs(expiration_time))

        return Offer(
            id=OfferId(generate_item_id()),
            intId=random.randint(0, 999_999),
            user=self._make_random_user(),
            root=root_item.id,
            items=offer_items,
            itemsCost=offer_price,
            requirements=[requirement],
            requirementsCost=offer_price,
            summaryCost=offer_price,
            sellInOnePiece=sell_in_one_piece,
            startTime=0,
            endTime=int(expires_at.timestamp()),
        )

    def __get_random_username(self) -> str:
        try:
            return random.choice(self.seller_names)
        except IndexError:
            return "nickname"

    def _make_random_user(self) -> FleaUser:
        return FleaUser(
            id=generate_item_id(),
            nickname=self.__get_random_username(),
            avatar="/files/trader/avatar/unknown.jpg",
            memberType=0,
            rating=0.0,
            isRatingGrowing=True,
        )
