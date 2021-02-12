import ujson
from flask import Blueprint, request

from server import db_dir, root_dir
from server.utils import TarkovError, tarkov_response, zlib_middleware
from tarkov.profile import Profile
from tarkov.trader import TraderInventory, TraderType, get_trader_base, get_trader_bases

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/trading/customization/storage', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def customization_storage():
    if 'PHPSESSID' not in request.cookies:
        raise TarkovError(1, "No Session")
    session_id = request.cookies['PHPSESSID']
    return ujson.load(
        root_dir.joinpath('resources', 'profiles', session_id, 'storage.json').open('r', encoding='utf8'))


@blueprint.route('/client/trading/customization/<string:trader_id>', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def customization(trader_id):
    suits_path = db_dir.joinpath('assort', trader_id, 'suits.json')
    if not suits_path.exists():
        return TarkovError(600, "This Trader Doesn't have any suits for sale")

    # profile_data = {"Info": {"Side": "Bear"}}  # TODO: After making profile handler load profile here
    # suits_data = ujson.load(suits_path.open('r', encoding='utf8'))
    # for suit in suits_data:
    #     is_suit = suit_side for suit_side in suits_data[suit]['_props']['Side']
    #       if suit_side == profile_data['Info']['Side']:

    # output is { "item._id": [[{ "_tpl": "", "count": 0 }]] }
    return []


@blueprint.route('/client/trading/api/getUserAssortPrice/trader/<string:trader_id>', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def get_user_assort_price(trader_id):
    with Profile.from_request(request) as player_profile:
        trader_inventory = TraderInventory(TraderType(trader_id), profile=player_profile)
        items = {}
        for item in player_profile.inventory.items:
            if not trader_inventory.can_sell(item):
                continue

            price = trader_inventory.get_sell_price(item)
            items[item.id] = [[{'_tpl': '5449016a4bdc2d6f028b456f', 'count': price}]]

        # TODO: Calculate price for items to sell in specified trader
        # output is { "item._id": [[{ "_tpl": "", "count": 0 }]] }
    return items


@blueprint.route('/client/trading/api/getTradersList', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def get_trader_list():
    return get_trader_bases()


@blueprint.route('/client/trading/api/getTraderAssort/<string:trader_id>', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def get_trader_assort(trader_id):
    with Profile.from_request(request) as profile:
        trader_inventory = TraderInventory(TraderType(trader_id), profile=profile)

        return {
            'barter_scheme': trader_inventory.barter_scheme.dict()['__root__'],
            'items': [item.dict() for item in trader_inventory.assort],
            'loyal_level_items': trader_inventory.loyal_level_items,
        }


@blueprint.route('/client/trading/api/getTrader/<string:trader_id>', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def trader_base(trader_id):
    return get_trader_base(trader_id=trader_id)
