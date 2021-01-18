from functools import lru_cache

import ujson
from flask import Blueprint, request

import mods.core.lib.profile as lib_profile
from mods.core.lib.profile import Profile
from mods.core.lib.trader import TraderInventory, Traders
from server import root_dir, db_dir
from server.utils import game_response_middleware, TarkovError

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/trading/customization/storage', methods=['POST', 'GET'])
@game_response_middleware()
def client_trading_customization_storage():
    if 'PHPSESSID' not in request.cookies:
        raise TarkovError(1, "No Session")
    session_id = request.cookies['PHPSESSID']
    return ujson.load(
        root_dir.joinpath('resources', 'profiles', session_id, 'storage.json').open('r', encoding='utf8'))


@blueprint.route('/client/trading/customization/<string:trader_id>', methods=['POST', 'GET'])
@game_response_middleware()
def client_trading_customization(trader_id):
    suits_path = db_dir.joinpath('assort', trader_id, 'suits.json')
    if not suits_path.exists():
        return TarkovError(600, "This Trader Doesn't have any suits for sale")

    # profile_data = {"Info": {"Side": "Bear"}}  # TODO: After making profile handler load profile here
    # suits_data = ujson.load(suits_path.open('r', encoding='utf8'))
    # for suit in suits_data:
    #     is_suit = suit_side for suit_side in suits_data[suit]['_props']['Side']
    #       if suit_side == profile_data['Info']['Side']:

    # output is { "item._id": [[{ "_tpl": "", "count": 0 }]] }
    output = []
    return output


@blueprint.route('/client/trading/api/getUserAssortPrice/trader/<string:trader_id>', methods=['POST', 'GET'])
@game_response_middleware()
def client_trading_api_get_user_assort_price(trader_id):
    profile_id = request.cookies['PHPSESSID']
    player_profile = lib_profile.Profile(profile_id)

    with player_profile:
        trader_inventory = TraderInventory(Traders(trader_id), player_inventory=player_profile.inventory)
        items = {}
        for item in player_profile.inventory.items:
            if not trader_inventory.can_sell(item):
                continue

            price = trader_inventory.get_sell_price(item)
            items[item['_id']] = [[{'_tpl': '5449016a4bdc2d6f028b456f', 'count': price}]]

        # TODO: Calculate price for items to sell in specified trader
        # output is { "item._id": [[{ "_tpl": "", "count": 0 }]] }
    return items


@blueprint.route('/client/trading/api/getTradersList', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def client_trading_api_get_trader_list():
    traders_path = db_dir.joinpath('base', 'traders')

    paths = set(traders_path.rglob('*/base.json')) - set(traders_path.rglob('ragfair/base.json'))

    traders_data = [ujson.load(file.open('r', encoding='utf8')) for file in paths]
    traders_data = sorted(traders_data, key=lambda trader: trader['_id'])

    return traders_data


@blueprint.route('/client/trading/api/getTraderAssort/<string:trader_id>', methods=['POST', 'GET'])
# @lru_cache(8)
@game_response_middleware()
def client_trading_api_get_trader_assort(trader_id):
    with Profile(request.cookies['PHPSESSID']) as profile:
        trader_inventory = TraderInventory(Traders(trader_id), player_inventory=profile.inventory)
        return {
            'barter_scheme': trader_inventory.barter_scheme,
            'items': trader_inventory.assort,
            'loyal_level_items': trader_inventory.loyal_level_items,
        }


@blueprint.route('/client/trading/api/getTrader/<string:trader_id>', methods=['POST', 'GET'])
@lru_cache(8)
@game_response_middleware()
def client_trading_api_get_trader(trader_id):
    trader_path = db_dir.joinpath('base', 'traders', trader_id, 'base.json')

    traders_data = ujson.load(trader_path.open('r', encoding='utf8'))
    return traders_data
