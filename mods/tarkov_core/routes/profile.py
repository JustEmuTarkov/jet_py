import ujson
from flask import request, Blueprint

from core.main import root_dir
from core.utils import route_decorator

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/game/profile/items/moving', methods=['POST', 'GET'])
@route_decorator()
def client_game_profile_item_move():
    # we are grabbing body decompressed then we loop through variable body.data as []
    # then we switch() by Action key and checking what game want us to do
    pass


@blueprint.route('/client/game/profile/list', methods=['POST', 'GET'])
@route_decorator()
def client_game_profile_list():
    session_id = request.cookies['PHPSESSID']
    profile_dir = root_dir.joinpath('resources', 'profiles', session_id)
    pmc_profile = ujson.load((profile_dir / 'character.json').open('r'))
    scav_profile = ujson.load((profile_dir / 'character_scav.json').open('r'))
    return [
        pmc_profile,
        scav_profile,
    ]


@blueprint.route('/client/game/profile/select', methods=['POST', 'GET'])
@route_decorator()
def client_game_profile_list_select():
    return {
        'status': 'ok',
        'notifier': {
            'server': f'{request.url_root}/',
            'channel_id': 'testChannel',
        },
    }


@blueprint.route('/client/profile/status', methods=['POST', 'GET'])
@route_decorator()
def client_profile_status():
    session_id = request.cookies['PHPSESSID']
    response = []
    for profile_type in ('scav', 'pmc'):
        response.append({
            'profileid': f'{profile_type}{session_id}',
            'status': 'Free',
            'sid': '',
            'ip': '',
            'port': 0
        })

    return response
