from fastapi import Request

from server.utils import make_router
from tarkov.fleamarket.fleamarket import flea_market_instance
from tarkov.fleamarket.models import FleaMarketRequest, FleaMarketResponse
from tarkov.models import TarkovSuccessResponse

flea_market_router = make_router(tags=["FleaMarket"])


@flea_market_router.post(
    "/client/ragfair/find",
    response_model_exclude_none=True,
    response_model_exclude_unset=False,
    response_model=TarkovSuccessResponse[FleaMarketResponse],
)
async def find(req: Request) -> TarkovSuccessResponse[FleaMarketResponse]:
    request = FleaMarketRequest.parse_obj(await req.json())
    # pprint.pprint(request.dict(), indent=4)
    return TarkovSuccessResponse(data=flea_market_instance.view.get_response(request))
