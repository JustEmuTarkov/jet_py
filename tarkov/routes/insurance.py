from typing import Dict, List, Union

from fastapi.params import Depends
from pydantic import BaseModel

from server.utils import make_router
from tarkov.dependencies import profile_manager
from tarkov.inventory.types import ItemId, TemplateId
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile.profile import Profile
from tarkov.trader import TraderType
from tarkov.trader.trader import Trader

insurance_router = make_router(tags=["Insurance"])

INSURANCE_PRICE_MODIFIER = 0.1


class InsuranceListCostRequest(BaseModel):
    traders: List[str]
    items: List[ItemId]


@insurance_router.post("/client/insurance/items/list/cost")
async def items_list_cost(
    request: InsuranceListCostRequest,
    profile: Profile = Depends(profile_manager.with_profile),  # type: ignore
) -> Union[TarkovSuccessResponse[Dict[str, dict]], TarkovErrorResponse]:
    insurance_data: Dict[str, dict] = {}

    for trader_id in request.traders:
        trader = Trader(TraderType(trader_id), profile=profile)
        trader_items: Dict[TemplateId, int] = {}

        for item_id in request.items:
            item = profile.inventory.get(item_id)
            trader_items[item.tpl] = trader.calculate_insurance_price(item)

        insurance_data[trader_id] = trader_items

    return TarkovSuccessResponse(data=insurance_data)
