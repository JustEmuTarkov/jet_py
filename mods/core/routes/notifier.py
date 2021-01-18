from flask import request, Blueprint

from server.utils import game_response_middleware, TarkovError

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/notifierServer/get/<string:profile_pk>', methods=['POST', 'GET'])
@game_response_middleware()
# pylint: disable=unused-argument
def notifierserver_get(profile_pk: str):
    #  ?last_id=default_id
    return {"type": "ping", "eventId": "ping"}


@blueprint.route('/client/notifier/channel/create', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def client_notifier_channel_create():
    session_id = request.cookies.get('PHPSESSID', None)
    if session_id is None:
        raise TarkovError(err=1, errmsg='No session')
    root_url = request.url_root
    notifier_server_url = f'{root_url}/notifierServer/get/{session_id}'
    response = {
        'notifier': {
            'server': f'{root_url}/',
            'channel_id': 'testChannel',
            'url': notifier_server_url,
        },
        "notifierServer": notifier_server_url
    }
    return response
