from typing import Dict, List, Union

from dependency_injector.wiring import Provide, inject
from fastapi.params import Depends
from pydantic import BaseModel

from server.container import AppContainer
from server.utils import make_router
from tarkov.profile.dependencies import with_profile
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile.profile import Profile
from tarkov.trader.manager import TraderManager
from tarkov.trader.models import TraderType

insurance_router = make_router(tags=["Insurance"])


class InsuranceListCostRequest(BaseModel):
    traders: List[str]
    items: List[ItemId]


@insurance_router.post("/client/insurance/items/list/cost")
@inject
async def items_list_cost(
    request: InsuranceListCostRequest,
    profile: Profile = Depends(with_profile),
    trader_manager: TraderManager = Depends(Provide[AppContainer.trader.manager]),
) -> Union[TarkovSuccessResponse[Dict[str, dict]], TarkovErrorResponse]:
    insurance_data: Dict[str, dict] = {}

    for trader_id in request.traders:
        trader = trader_manager.get_trader(TraderType(trader_id))
        trader_view = trader.view(player_profile=profile)
        trader_items: Dict[TemplateId, int] = {}

        for item_id in request.items:
            item = profile.inventory.get(item_id)
            trader_items[item.tpl] = trader_view.insurance_price([item])

        insurance_data[trader_id] = trader_items

    return TarkovSuccessResponse(data=insurance_data)
