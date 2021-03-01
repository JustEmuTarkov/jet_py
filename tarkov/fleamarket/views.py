from __future__ import annotations

import collections
from typing import Dict, List, TYPE_CHECKING, Union

from tarkov.fleamarket.models import FleaMarketRequest, FleaMarketResponse, Offer, SortType
from tarkov.inventory import item_templates_repository
from tarkov.inventory.types import TemplateId
from tarkov.repositories.categories import CategoryId, category_repository

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .fleamarket import FleaMarket


class FleaMarketView:
    """
    Class to process requests from "/client/ragfair/find" route
    """

    def __init__(self, flea_market: FleaMarket):
        self.flea_market = flea_market

    def get_response(self, request: FleaMarketRequest) -> FleaMarketResponse:

        # Take all offers from current flea market
        offers: List[Offer] = list(self.flea_market.offers.values())

        # Apply linked search filter
        if request.linkedSearchId:
            linked_search_template = item_templates_repository.get_template(request.linkedSearchId)
            offers = [offer for offer in offers if linked_search_template.has_in_slots(offer.root_item.tpl)]

        # Else apply required search filter
        elif request.neededSearchId:
            offers = [
                offer
                for offer in offers
                if item_templates_repository.get_template(offer.root_item).has_in_slots(request.neededSearchId)
            ]

        categories: Dict[Union[TemplateId, CategoryId], int]
        if not request.linkedSearchId and not request.neededSearchId:
            # If it's not linked/required search then return categories for all offers
            categories = collections.Counter(offer.root_item.tpl for offer in self.flea_market.offers.values())
        else:
            # Else return categories for filtered offers
            categories = collections.Counter(offer.root_item.tpl for offer in offers)

        # Apply category filter to offers
        if request.handbookId:
            offers = list(self.__filter_category_search(offers, request))

        # Offers pagination/sorting
        page_size = request.limit
        offers = self._sorted_offers(offers, request.sortType, reverse=request.sortDirection == 1)
        offers_view = offers[request.page * page_size : (request.page + 1) * page_size]

        return FleaMarketResponse(
            offers=offers_view,
            categories=categories,
            offersCount=len(offers),
            selectedCategory=request.handbookId,
        )

    @staticmethod
    def __filter_category_search(offers: List[Offer], request: FleaMarketRequest) -> List[Offer]:
        return [
            offer
            for offer in offers
            if category_repository.has_parent_category(
                category_repository.get_category(offer.root_item.tpl),
                request.handbookId,
            )
            or offer.root_item.tpl == request.handbookId
        ]

    @staticmethod
    def _sorted_offers(offers: List[Offer], sort_type: SortType, reverse: bool = False) -> List[Offer]:
        """Sorts offers in place"""

        def sort_by_title(offer: Offer) -> str:
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
