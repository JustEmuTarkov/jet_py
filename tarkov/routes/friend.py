from flask import Blueprint

from server.utils import tarkov_response, zlib_middleware

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/friend/list', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_friend_list():
    return {
        'Friends': [],
        'Ignore': [],
        'InIgnoreList': []
    }


@blueprint.route('/client/friend/request/list/inbox', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_friend_request_list_inbox():
    return []


@blueprint.route('/client/friend/request/list/outbox', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_friend_request_list_outbox():
    return []
