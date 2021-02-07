from __future__ import annotations

import ujson
from flask import Blueprint, request

from server import root_dir
from server.utils import game_response_middleware
from tarkov.inventory_dispatcher import DispatcherManager
from tarkov.profile import Profile

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/game/profile/items/moving', methods=['POST', 'GET'])
@game_response_middleware()
def client_game_profile_item_move():
    dispatcher = DispatcherManager(request.cookies['PHPSESSID'])
    response = dispatcher.dispatch()
    print(ujson.dumps(response.dict(exclude_defaults=False, exclude_none=True, exclude_unset=False), indent=4))
    return response.dict(exclude_defaults=False, exclude_none=True, exclude_unset=False)


@blueprint.route('/client/game/profile/list', methods=['POST', 'GET'])
@game_response_middleware()
def client_game_profile_list():
    session_id = request.cookies['PHPSESSID']

    with Profile(session_id) as profile:
        pmc_profile = profile.get_profile()

        profile_dir = root_dir.joinpath('resources', 'profiles', session_id)
        scav_profile = ujson.load((profile_dir / 'character_scav.json').open('r'))

        return [
            pmc_profile,
            scav_profile,
        ]


@blueprint.route('/client/game/profile/select', methods=['POST', 'GET'])
@game_response_middleware()
def client_game_profile_list_select():
    return {
        'status': 'ok',
        'notifier': {
            'server': f'{request.url_root}/',
            'channel_id': 'testChannel',
        },
    }


@blueprint.route('/client/profile/status', methods=['POST', 'GET'])
@game_response_middleware()
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