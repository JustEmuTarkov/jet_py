from fastapi import Request
from fastapi.params import Body

from server.utils import make_router
from tarkov.fleamarket.fleamarket import flea_market_instance
from tarkov.fleamarket.models import FleaMarketRequest, FleaMarketResponse
from tarkov.inventory.types import TemplateId
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
    return TarkovSuccessResponse(data=flea_market_instance.view.get_response(request))


@flea_market_router.post("/client/items/prices")
def client_items_prices() -> TarkovSuccessResponse:
    return TarkovSuccessResponse(data=None)


@flea_market_router.post("/client/ragfair/itemMarketPrice")
async def client_ragfair_item_market_price(
    template_id: TemplateId = Body(..., alias="templateId", embed=True),  # type: ignore
) -> TarkovSuccessResponse:
    return TarkovSuccessResponse(data=flea_market_instance.item_price(template_id))
