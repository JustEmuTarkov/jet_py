from typing import List, Dict

from flask import Blueprint, request

from mods.core.lib.items import TemplateId
from mods.core.lib.profile import Profile
from mods.core.lib.trader import TraderInventory, Traders
from server.utils import game_response_middleware

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
                item_template_id = item['_tpl']

                trader_items[item_template_id] = trader_inventory.calculate_insurance_price(item)

            response[trader_id] = trader_items

        return response
