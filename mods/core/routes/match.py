import ujson
from flask import Blueprint, request

from mods.core.lib.profile import Profile
from server import db_dir
from server.utils import game_response_middleware

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/match/group/status', methods=['POST', 'GET'])
@game_response_middleware()
def group_status():
    return {
        'players': [],
        'invite': [],
        'group': [],
    }


@blueprint.route('/client/match/group/exit_from_menu', methods=['POST', 'GET'])
@game_response_middleware()
def exit_from_menu():
    return None


@blueprint.route('/client/match/available', methods=['POST', 'GET'])
@game_response_middleware()
def available():
    return True


# {
#     'location': 'Interchange',
#     'savage': False,
#     'entryPoint': 'MallNW',
#     'dt': 'PAST',
#     'servers': [
#         {
#             'ping': -1,
#             'ip': 'https://127.0.0.1:5000/',
#             'port': '5000'
#         }
#     ],
#     'keyId': ''
# }
@blueprint.route('/client/match/join', methods=['POST', 'GET'])
@game_response_middleware()
def join():
    session_id: str = request.cookies['PHPSESSID']
    with Profile(session_id) as profile:
        return [
            {
                'profileid': profile.pmc_profile['_id'],
                'status': 'busy',
                'sid': '',
                'ip': '127.0.0.1',
                'port': 9909,
                'version': 'live',
                'location': request.data['location'],
                'gamemode': 'deathmatch',
                'shortid': 'TEST',
            }
        ]


@blueprint.route('/client/match/exit', methods=['POST', 'GET'])
@game_response_middleware()
def exit_():
    return None


@blueprint.route('/client/getMetricsConfig', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def get_metrics_config():
    return ujson.load(db_dir.joinpath('base', 'matchMetrics.json').open(encoding='utf8'))
