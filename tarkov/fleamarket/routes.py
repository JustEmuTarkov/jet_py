import collections
import pprint
from typing import List

import pydantic
from fastapi import Request

from server import db_dir
from server.utils import make_router
from tarkov._repositories.categories import category_repository
from tarkov.fleamarket.models import FleaMarketRequest, FleaMarketResponse, Offer
from tarkov.models import TarkovSuccessResponse

flea_market_router = make_router(tags=["FleaMarket"])


@flea_market_router.post(
    "/client/ragfair/find",
    response_model_exclude_none=True,
    response_model=TarkovSuccessResponse[FleaMarketResponse],
)
async def find(req: Request) -> TarkovSuccessResponse[FleaMarketResponse]:
    request = FleaMarketRequest.parse_obj(await req.json())
    pprint.pprint(request.dict(), indent=4)
    offers = pydantic.parse_file_as(List[Offer], db_dir.joinpath("test_offer.json"))

    categories_counter = collections.Counter(
        category_repository.get_category(offer.root_item).Id for offer in offers
    )
    offers = [
        offer
        for offer in offers
        if category_repository.has_parent_category(
            category_repository.get_category(offer.root_item), request.handbookId
        )
    ]
    response = TarkovSuccessResponse(
        data=FleaMarketResponse(
            offers=offers,
            categories=categories_counter,
            offersCount=len(offers),
            selectedCategory="5b5f78dc86f77409407a7f8e",
        )
    )
    print(response.json())
    return response
