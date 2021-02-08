from flask import Blueprint, request

from server.utils import zlib_middleware

blueprint = Blueprint(__name__, __name__)


# Launcher doesn't work atm


@blueprint.route('/launcher/server/connect', methods=['POST', 'GET'])
@zlib_middleware
def connect():
    response = {
        'backendUrl': request.host_url.rstrip('/'),
        'name': 'Jet Py',
        'editions': ['Edge Of Darkness']
    }
    return response


def server_info():
    response = {
        'ServerName': 'Jet Py',
        'Editions': ['Edge Of Darkness']
    }
    return response
