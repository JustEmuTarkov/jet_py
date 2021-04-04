from dependency_injector.wiring import Provide, inject
from fastapi import Request
from fastapi.params import Body, Depends

from server.container import AppContainer
from server.utils import make_router
from tarkov.fleamarket.fleamarket import FleaMarket
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
@inject
async def find(
    req: Request,
    flea_market: FleaMarket = Depends(Provide[AppContainer.flea.market]),  # type: ignore
) -> TarkovSuccessResponse[FleaMarketResponse]:
    request = FleaMarketRequest.parse_obj(await req.json())
    return TarkovSuccessResponse(data=flea_market.view.get_response(request))


@flea_market_router.post("/client/items/prices")
def client_items_prices() -> TarkovSuccessResponse:
    return TarkovSuccessResponse(data=None)


@flea_market_router.post("/client/ragfair/itemMarketPrice")
@inject
def client_ragfair_item_market_price(
    template_id: TemplateId = Body(..., alias="templateId", embed=True),  # type: ignore
    flea_market: FleaMarket = Depends(Provide[AppContainer.flea.market]),  # type: ignore
) -> TarkovSuccessResponse:
    return TarkovSuccessResponse(data=flea_market.item_price_view(template_id))
