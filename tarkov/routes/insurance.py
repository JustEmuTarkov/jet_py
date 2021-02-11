from typing import Dict, List

from flask import Blueprint, request

from server.utils import tarkov_response, zlib_middleware
from tarkov.inventory.models import TemplateId
from tarkov.lib.trader import TraderInventory, Traders
from tarkov.profile import Profile

blueprint = Blueprint(__name__, __name__)

INSURANCE_PRICE_MODIFIER = 0.1


@blueprint.route('/client/insurance/items/list/cost', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def items_list_cost():
    traders_list: List[str] = request.data['traders']
    item_ids: List[str] = request.data['items']

    response: Dict[str, dict] = {}

    with Profile.from_request(request=request) as profile:
        for trader_id in traders_list:
            trader_inventory = TraderInventory(Traders(trader_id), profile=profile)
            trader_items: Dict[TemplateId, int] = {}

            for item_id in item_ids:
                item = profile.inventory.get_item(item_id)
                trader_items[item.tpl] = trader_inventory.calculate_insurance_price(item)

            response[trader_id] = trader_items

        return response
