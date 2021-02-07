import time
from typing import Dict, List, Union

import orjson
from flask import Blueprint, request

import tarkov.profile
from server.utils import TarkovError, game_response_middleware
from tarkov import notifier

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/mail/dialog/list', methods=['POST'])
@game_response_middleware()
def mail_dialog_list() -> List[Dict]:
    with tarkov.profile.Profile.from_request(request) as profile:
        return profile.notifier.view_dialog_list()


@blueprint.route('/client/mail/dialog/view', methods=['POST'])
@game_response_middleware()
def mail_dialog_view() -> Dict:
    request_data: dict = request.data  # type: ignore

    # type_: int = request_data['type']
    dialogue_id: str = request_data['dialogId']
    # limit: int = request_data['limit']
    time_: float = request_data['time']

    with tarkov.profile.Profile.from_request(request) as profile:
        return profile.notifier.view_dialog(dialogue_id=dialogue_id, time_=time_)


@blueprint.route('/client/mail/dialog/getAllAttachments', methods=['POST'])
@game_response_middleware()
def mail_dialog_all_attachments() -> Dict:
    request_data: dict = request.data  # type: ignore
    dialogue_id = request_data['dialogId']

    with tarkov.profile.Profile.from_request(request) as profile:
        return profile.notifier.all_attachments_view(dialogue_id=dialogue_id)


@blueprint.route('/notifierServer/get/<profile_id>', methods=['GET'])
def notifierserver_get(profile_id: str) -> Union[dict, str]:
    for _ in range(15):  # Poll for 15 seconds
        if notifier.notifier_instance.has_notifications(profile_id):
            notifications = notifier.notifier_instance.get_notifications(profile_id)
            response = '\n'.join([orjson.dumps(notification).decode('utf8') for notification in notifications])
            return response

        time.sleep(1)

    return notifier.notifier_instance.get_empty_notification()


@blueprint.route('/client/notifier/channel/create', methods=['POST'])
@game_response_middleware()
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
        'notifierServer': notifier_server_url
    }
    return response
