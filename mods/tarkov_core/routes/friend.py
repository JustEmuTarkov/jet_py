import ujson
from flask import request

from core.app import app
from core.main import root_dir
from core.utils import route_decorator


@app.route('/client/friend/list', methods=['POST', 'GET'])
@route_decorator()
def client_friend_list():
    return {
        'Friends': [],
        'Ignore': [],
        'InIgnoreList': []
    }


@app.route('/client/friend/request/list/inbox', methods=['POST', 'GET'])
@route_decorator()
def client_friend_request_list_inbox():
    return []


@app.route('/client/friend/request/list/outbox', methods=['POST', 'GET'])
@route_decorator()
def client_friend_request_list_outbox():
    return []
