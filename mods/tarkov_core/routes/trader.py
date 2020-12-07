from functools import lru_cache

import ujson
from flask import Blueprint, request

from core.main import db_dir, root_dir
from core.utils import route_decorator

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/trading/customization/storage', methods=['POST', 'GET'])
@route_decorator()
def client_trading_customization_storage():
    php_session_id = request.cookies['PHPSESSID']
    return ujson.load(root_dir.joinpath('resources', 'profiles', php_session_id, 'storage.json').open('r', encoding='utf8'))


@blueprint.route('/client/trading/api/getTradersList', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def client_trading_api_getTraderlist():
    traders_path = db_dir.joinpath('base', 'traders')
    paths = set(traders_path.rglob('*/base.json')) - set(traders_path.rglob('ragfair/base.json'))

    traders_data = [ujson.load(file.open('r', encoding='utf8')) for file in paths]
    return traders_data


@blueprint.route('/client/trading/api/getTraderAssort/<string:trader_id>', methods=['POST', 'GET'])
@lru_cache(8)
@route_decorator()
def client_trading_api_getTraderAssort(trader_id):
    traders_path = db_dir.joinpath('assort', trader_id)
    paths = set(traders_path.rglob('*.json')) - set(traders_path.rglob('questassort.json'))

    traders_data = {file.stem: ujson.load(file.open('r', encoding='utf8')) for file in paths}
    return traders_data
