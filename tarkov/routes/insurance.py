from typing import Dict, List

from flask import Blueprint, request

from server.utils import game_response_middleware
from tarkov.inventory import TemplateId
from tarkov.profile import Profile
from tarkov.lib.trader import TraderInventory, Traders

blueprint = Blueprint(__name__, __name__)

INSURANCE_PRICE_MODIFIER = 0.1


@blueprint.route('/client/insurance/items/list/cost', methods=['POST', 'GET'])
@game_response_middleware()
def items_list_cost():
    traders_list: List[str] = request.data['traders']
    item_ids: List[str] = request.data['items']

    response: Dict[str, dict] = {}

    with Profile(request.cookies['PHPSESSID']) as profile:
        for trader_id in traders_list:
            trader_inventory = TraderInventory(Traders(trader_id), player_inventory=profile.inventory)
            trader_items: Dict[TemplateId, int] = {}

            for item_id in item_ids:
                item = profile.inventory.get_item(item_id)
                trader_items[item.tpl] = trader_inventory.calculate_insurance_price(item)

            response[trader_id] = trader_items

        return response