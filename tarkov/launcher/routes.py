from fastapi import APIRouter
from starlette.requests import Request

from server.utils import get_request_url_root

launcher_router = APIRouter(tags=['Launcher'])


@launcher_router.post('/launcher/server/connect')
def connect(request: Request) -> dict:
    return {
        'backendUrl': get_request_url_root(request).rstrip('/'),
        'name': 'Jet Py',
        'editions': ['Edge Of Darkness']
    }


def server_info():
    response = {
        'ServerName': 'Jet Py',
        'Editions': ['Edge Of Darkness']
    }
    return response
