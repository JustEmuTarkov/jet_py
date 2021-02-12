from typing import Dict, List, Optional

from fastapi import APIRouter
from fastapi.params import Cookie
from flask import request

from tarkov.inventory.models import ItemId, TemplateId
from tarkov.models import TarkovSuccessResponse
from tarkov.profile import Profile
from tarkov.trader import TraderInventory, TraderType

router = APIRouter(prefix='', tags=['Insurance'])

INSURANCE_PRICE_MODIFIER = 0.1


@router.post('/client/insurance/items/list/cost')
def items_list_cost(
        traders: List[str],
        items: List[ItemId],
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None),

) -> TarkovSuccessResponse[Dict[str, dict]]:
    insurance_data: Dict[str, dict] = {}

    with Profile.from_request(request=request) as profile:
        for trader_id in traders:
            trader_inventory = TraderInventory(TraderType(trader_id), profile=profile)
            trader_items: Dict[TemplateId, int] = {}

            for item_id in items:
                item = profile.inventory.get_item(item_id)
                trader_items[item.tpl] = trader_inventory.calculate_insurance_price(item)

            insurance_data[trader_id] = trader_items

    return TarkovSuccessResponse(data=insurance_data)
