import datetime
import random
from typing import Dict, Optional, Type, Union

import ujson
from fastapi import APIRouter
from fastapi.params import Cookie
from flask import Blueprint, request
from starlette.requests import Request

from server import app, db_dir, start_time
from server.utils import get_request_url_root, tarkov_response, zlib_middleware
from tarkov.inventory import item_templates_repository
from tarkov.inventory.models import TemplateId
from tarkov.inventory.repositories import AnyTemplate
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse

blueprint = Blueprint(__name__, __name__)
router = APIRouter(prefix='', tags=['Misc/Bootstrap'])


@app.route('/client/locations', methods=['GET', 'POST'])
@zlib_middleware
@tarkov_response
def client_locations():
    locations_base = db_dir / 'base' / 'locations.json'
    locations_base = ujson.load(locations_base.open('r'))

    for file in (db_dir / 'locations').glob('*.json'):
        map_data = ujson.load(file.open('r'))
        map_id = map_data['base']['_Id']
        locations_base['locations'][map_id] = map_data['base']

    return locations_base


@router.post('/client/game/start')
def client_game_start() -> TarkovSuccessResponse[Type[None]]:
    return TarkovSuccessResponse(data=None)  # TODO Add account data, check if character exists


@router.post('/client/game/version/validate')
def client_game_version_validate() -> TarkovSuccessResponse[Type[None]]:
    return TarkovSuccessResponse(data=None)


@router.post('/client/game/config')
def client_game_config(
        request: Request,
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    url_root = get_request_url_root(request)

    if profile_id is None:
        return TarkovErrorResponse.profile_id_is_none()

    return TarkovSuccessResponse(data={
        "queued": False,
        "banTime": 0,
        "hash": "BAN0",
        "lang": "en",
        "aid": profile_id,
        "token": "token_" + profile_id,
        "taxonomy": "341",
        "activeProfileId":
            "user" + profile_id + "pmc",
        "nickname": "user",
        "backend": {
            "Trading": url_root,
            "Messaging": url_root,
            "Main": url_root,
            "RagFair": url_root
        },
        "totalInGame": 0
    })


@router.post('/client/game/keepalive')
def client_game_keepalive(
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if not profile_id:
        return TarkovErrorResponse(err=True, errmsg='No Session', data=None)

    return TarkovSuccessResponse(data={'msg': 'ok'})


@router.post(
    '/client/items',
    response_model=TarkovSuccessResponse[Dict[TemplateId, AnyTemplate]]
)
def client_items() -> TarkovSuccessResponse[Dict[TemplateId, AnyTemplate]]:
    return TarkovSuccessResponse(data=item_templates_repository.templates)


@router.post('/client/customization')
def client_customization() -> TarkovSuccessResponse[dict]:
    customization = {}
    for customization_file_path in (db_dir / 'customization').glob('*'):
        customization_data = ujson.load(customization_file_path.open('r', encoding='utf8'))
        customization_id = customization_data['_id']
        customization[customization_id] = customization_data

    return TarkovSuccessResponse(data=customization)


@router.post('/client/globals')
def client_globals() -> TarkovSuccessResponse[dict]:
    globals_path = db_dir.joinpath('base', 'globals.json')
    globals_base = ujson.load(globals_path.open(encoding='utf8'))
    return TarkovSuccessResponse(data=globals_base)


@app.route('/client/weather', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_weather():
    weather_dir = db_dir / 'weather'
    weather_files = list(weather_dir.glob('*'))
    weather_data = ujson.load(random.choice(weather_files).open('r', encoding='utf8'))

    current_datetime = datetime.datetime.now()
    delta = current_datetime - start_time
    current_datetime = current_datetime + delta * weather_data['acceleration']

    timestamp = int(current_datetime.timestamp())
    date_str = current_datetime.strftime('%Y-%m-%d')
    time_str = current_datetime.strftime('%H:%M:%S')

    weather_data['weather']['timestamp'] = timestamp
    weather_data['weather']['date'] = date_str
    weather_data['weather']['time'] = f'{date_str} {time_str}'
    weather_data['date'] = date_str
    weather_data['time'] = time_str

    return weather_data


@app.route('/client/handbook/templates', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_handbook_templates():
    data = {}
    for template_path in db_dir.joinpath('templates').glob('*.json'):
        data[template_path.stem] = ujson.load(template_path.open('r', encoding='utf8'))

    return data


@app.route('/client/handbook/builds/my/list', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_handbook_builds_my_list():
    return []  # TODO load user builds


@app.route('/client/quest/list', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_quest_list():
    return ujson.load(db_dir.joinpath('quests', 'all.json').open('r', encoding='utf8'))


@app.route('/client/server/list', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_server_list():
    return [
        {
            'ip': request.url_root,
            'port': 5000
        }
    ]


@app.route('/client/checkVersion', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_check_version():
    return {
        'isvalid': True,
        'latestVersion': ''
    }


@app.route('/client/game/logout', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_game_logout():
    return {
        "status": "ok"
    }
