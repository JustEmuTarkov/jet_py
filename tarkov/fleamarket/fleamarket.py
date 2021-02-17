from __future__ import annotations

import collections
import math
import random
import statistics
from builtins import property
from datetime import datetime, timedelta
from typing import Dict, List, Union

import pydantic

from server import db_dir
from tarkov.exceptions import NotFoundError
from .models import (
    FleaMarketRequest,
    FleaMarketResponse,
    FleaUser,
    Offer,
    OfferId,
    OfferRequirement,
    SortType,
)
from tarkov.repositories.categories import CategoryId, category_repository
from tarkov.inventory import generate_item_id, item_templates_repository
from tarkov.inventory.models import ItemTemplate
from tarkov.inventory.prop_models import AmmoProps
from tarkov.inventory.types import TemplateId
from tarkov import config


class OfferGenerator:
    def __init__(self, flea_market: FleaMarket):
        self.flea_market = flea_market

        self.item_prices = {
            tpl.id: tpl.props.CreditsPrice
            for tpl in item_templates_repository.templates.values()
            if tpl.id in category_repository.item_categories and tpl.props.CreditsPrice
        }
        item_prices = pydantic.parse_file_as(
            Dict[TemplateId, int], db_dir.joinpath("flea_prices.json")
        )
        self.item_prices.update(
            {tpl: price for tpl, price in item_prices.items() if price > 0}
        )
        self.item_templates = [
            tpl
            for tpl in item_templates_repository.templates.values()
            if tpl.id in self.item_prices
        ]
        prices = list(self.item_prices.values())
        median_price = statistics.median(prices)
        prices_sorted = sorted(prices)
        self.percentile_high: int = prices_sorted[
            int(len(prices) * config.flea_market.percentile_high)
        ]
        self.percentile_low: int = prices_sorted[
            int(len(prices) * config.flea_market.percentile_low)
        ]
        self.item_templates_weights = [
            self._get_item_template_weight(tpl, median_price)
            for tpl in self.item_templates
        ]

    def _get_item_template_weight(
        self, template: ItemTemplate, median_price: float
    ) -> float:
        if not template.props.CanSellOnRagfair:
            return 0
        item_price = self.item_prices[template.id]
        if isinstance(template.props, AmmoProps):
            item_price *= template.props.StackMaxSize  # So we don't have so much ammo
        chance_modifier = 1

        if item_price < self.percentile_low:
            chance_modifier = item_price / self.percentile_low
        if item_price > self.percentile_high:
            chance_modifier = self.percentile_high / item_price

        return math.log(self.item_prices[template.id], median_price) * chance_modifier

    def generate_offers(self, amount) -> Dict[OfferId, Offer]:
        offers = {}
        templates = random.choices(
            self.item_templates, weights=self.item_templates_weights, k=amount
        )
        for template in templates:
            offer = self._generate_offer(template)
            offers[offer.id] = offer
        return offers

    def _generate_offer(self, item_template: ItemTemplate) -> Offer:
        items = item_templates_repository.create_item(item_template.id)
        item_price = self.item_prices[item_template.id]
        item_price = int(random.gauss(item_price * 1.1, item_price * 0.1))
        assert len(items) == 1
        requirement = OfferRequirement(
            template_id=TemplateId("5449016a4bdc2d6f028b456f"),
            count=item_price,
        )
        now = datetime.now()
        expiration_time = random.gauss(
            timedelta(hours=6).total_seconds(), timedelta(hours=6).total_seconds()
        )
        expires_at = now + timedelta(seconds=abs(expiration_time))

        return Offer(
            id=OfferId(generate_item_id()),
            intId=random.randint(0, 999_999),
            user=self._make_random_user(),
            root=items[0].id,
            items=items,
            itemsCost=item_price,
            requirements=[requirement],
            requirementsCost=item_price,
            summaryCost=item_price,
            sellInOnePiece=True,
            startTime=0,
            endTime=int(expires_at.timestamp()),
        )

    @staticmethod
    def _make_random_user() -> FleaUser:
        return FleaUser(
            id=generate_item_id(),
            nickname="nickname",
            avatar="/files/trader/avatar/unknown.jpg",
            memberType=0,
            rating=0.0,
            isRatingGrowing=True,
        )


class FleaMarketView:
    def __init__(self, flea_market: FleaMarket):
        self.flea_market = flea_market

    def get_response(self, request: FleaMarketRequest) -> FleaMarketResponse:
        templates_counter: Dict[
            Union[TemplateId, CategoryId], int
        ] = collections.Counter(
            offer.root_item.tpl for offer in self.flea_market.offers.values()
        )
        offers = [
            offer
            for offer in self.flea_market.offers.values()
            if category_repository.has_parent_category(
                category_repository.get_category(offer.root_item), request.handbookId
            )
            or offer.root_item.tpl == request.handbookId
        ]
        page_size = request.limit
        offers = self._sorted_offers(
            offers, request.sortType, reverse=request.sortDirection == 1
        )
        offers_view = offers[request.page * page_size : (request.page + 1) * page_size]

        return FleaMarketResponse(
            offers=offers_view,
            categories=templates_counter,
            offersCount=len(offers),
            selectedCategory=request.handbookId,
        )

    @staticmethod
    def _sorted_offers(
        offers: List[Offer], sort_type: SortType, reverse: bool = False
    ) -> List[Offer]:
        """Sorts offers in place"""

        def sort_by_title(offer):
            item_tpl = item_templates_repository.get_template(offer.root_item)
            return item_tpl.name  # Swap to localization later

        sort_map = {
            SortType.Id: lambda offer: offer.intId,
            SortType.MerchantRating: lambda offer: offer.user.rating,
            SortType.OfferTitle: sort_by_title,
            SortType.Price: lambda offer: offer.itemsCost,
            SortType.ExpiresIn: lambda offer: offer.endTime,
        }
        return sorted(offers, key=sort_map[sort_type], reverse=reverse)


class FleaMarket:
    def __init__(self):
        self.offers_amount: int = config.flea_market.offers_amount

        self.updated_at = datetime.fromtimestamp(0)

        self.generator: OfferGenerator = OfferGenerator(self)
        self._view: FleaMarketView = FleaMarketView(self)
        self.offers: Dict[OfferId, Offer] = {}

    def get_offer(self, offer_id: OfferId) -> Offer:
        try:
            return self.offers[offer_id]
        except KeyError as error:
            raise NotFoundError from error

    def buy_offer(self, offer: Offer) -> None:
        del self.offers[offer.id]
        self.offers.update(self.generator.generate_offers(1))

    def __clear_expired_offers(self):
        now = datetime.now()
        now_timestamp = now.timestamp()
        expired_offers_keys = [
            key for key, offer in self.offers.items() if now_timestamp > offer.endTime
        ]

        for key in expired_offers_keys:
            del self.offers[key]

    def __update_offers(self):
        self.__clear_expired_offers()

        now = datetime.now()
        time_elapsed = now - self.updated_at
        self.updated_at = now
        new_offers_amount: int = min(
            self.offers_amount,
            int(time_elapsed.total_seconds()),
        )
        offers_to_full = self.offers_amount - len(self.offers)
        if new_offers_amount < offers_to_full:
            new_offers_amount = offers_to_full
        try:
            keys_to_delete = random.sample(
                list(self.offers.keys()), k=new_offers_amount
            )
        except ValueError:
            keys_to_delete = []

        for key in keys_to_delete:
            del self.offers[key]

        new_offers = self.generator.generate_offers(new_offers_amount)
        print(f"Generated {len(new_offers)} items!")
        self.offers.update(new_offers)

    @property
    def view(self) -> FleaMarketView:
        self.__update_offers()
        return self._view


flea_market_instance = FleaMarket()
