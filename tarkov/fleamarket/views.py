from __future__ import annotations

import collections
from typing import Dict, Iterable, List, TYPE_CHECKING, Union

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
        offers_iterable: Iterable[Offer] = self.flea_market.offers.values()

        # Apply linked search filter
        if request.linkedSearchId:
            offers_iterable = self.__filter_linked_search(offers_iterable, request)

        # Apply category filter
        if request.handbookId:
            offers_iterable = self.__filter_category_search(offers_iterable, request)

        offers: List[Offer] = list(offers_iterable)

        # Categories is a dict with CategoryId or TemplateId and amount of that item/category on flea
        categories: Dict[Union[TemplateId, CategoryId], int]
        if request.linkedSearchId:
            # If it's linked search then we have to return categories for linked items
            categories = collections.Counter(
                offer.root_item.tpl
                for offer in self.__filter_linked_search(self.flea_market.offers.values(), request)
            )
        else:
            # Else we just return categories for all items
            categories = collections.Counter(offer.root_item.tpl for offer in self.flea_market.offers.values())

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
    def __filter_linked_search(offers: Iterable[Offer], request: FleaMarketRequest) -> Iterable[Offer]:
        return (
            offer
            for offer in offers
            if any(
                (
                    FleaMarketView.__slot_filter(offer, "Slots", request.linkedSearchId),
                    FleaMarketView.__slot_filter(offer, "Chambers", request.linkedSearchId),
                    # FleaMarketView.__slot_filter(offer, "Cartridges", request.linkedSearchId),
                )
            )
        )

    @staticmethod
    def __slot_filter(offer: Offer, slot_filter: str, linked_search_id: TemplateId) -> bool:
        template = item_templates_repository.get_template(linked_search_id)
        props = template.props
        if not hasattr(props, slot_filter):
            return False

        for slot in getattr(props, slot_filter):
            for filter_group in slot["_props"]["filters"]:
                if offer.root_item.tpl in filter_group["Filter"]:
                    return True
        return False

    @staticmethod
    def __filter_category_search(offers: Iterable[Offer], request: FleaMarketRequest) -> Iterable[Offer]:
        return (
            offer
            for offer in offers
            if category_repository.has_parent_category(
                category_repository.get_category(offer.root_item.tpl),
                request.handbookId,
            )
            or offer.root_item.tpl == request.handbookId
        )

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
