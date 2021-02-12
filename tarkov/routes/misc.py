import datetime
import random
from typing import Dict, Optional, Type, Union

import ujson
from fastapi import APIRouter
from fastapi.params import Cookie
from starlette.requests import Request

from server import db_dir, start_time
from server.utils import get_request_url_root
from tarkov.inventory import item_templates_repository
from tarkov.inventory.models import TemplateId
from tarkov.inventory.repositories import AnyTemplate
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse

misc_router = APIRouter(prefix='', tags=['Misc/Bootstrap'])


@misc_router.post('/client/locations')
def client_locations() -> TarkovSuccessResponse[dict]:
    locations_base_path = db_dir.joinpath('base', 'locations.json')
    locations_base: dict = ujson.load(locations_base_path.open())

    for file in (db_dir / 'locations').glob('*.json'):
        map_data = ujson.load(file.open('r'))
        map_id = map_data['base']['_Id']
        locations_base['locations'][map_id] = map_data['base']

    return TarkovSuccessResponse(data=locations_base)


@misc_router.post('/client/game/start')
def client_game_start() -> TarkovSuccessResponse[Type[None]]:
    return TarkovSuccessResponse(data=None)  # TODO Add account data, check if character exists


@misc_router.post('/client/game/version/validate')
def client_game_version_validate() -> TarkovSuccessResponse[Type[None]]:
    return TarkovSuccessResponse(data=None)


@misc_router.post('/client/game/config')
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


@misc_router.post('/client/game/keepalive')
def client_game_keepalive(
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if not profile_id:
        return TarkovErrorResponse(err=True, errmsg='No Session', data=None)

    return TarkovSuccessResponse(data={'msg': 'ok'})


@misc_router.post(
    '/client/items',
    response_model=TarkovSuccessResponse[Dict[TemplateId, Union[AnyTemplate]]],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
def client_items() -> TarkovSuccessResponse[Dict[TemplateId, Union[AnyTemplate]]]:
    return TarkovSuccessResponse(data=item_templates_repository.templates)


@misc_router.post('/client/customization')
def client_customization() -> TarkovSuccessResponse[dict]:
    customization = {}
    for customization_file_path in (db_dir / 'customization').glob('*'):
        customization_data = ujson.load(customization_file_path.open('r', encoding='utf8'))
        customization_id = customization_data['_id']
        customization[customization_id] = customization_data

    return TarkovSuccessResponse(data=customization)


@misc_router.post('/client/globals')
def client_globals() -> TarkovSuccessResponse[dict]:
    globals_path = db_dir.joinpath('base', 'globals.json')
    globals_base = ujson.load(globals_path.open(encoding='utf8'))
    return TarkovSuccessResponse(data=globals_base)


@misc_router.post('/client/weather')
def client_weather() -> TarkovSuccessResponse[dict]:
    weather_dir = db_dir.joinpath('weather')
    weather_files = list(weather_dir.glob('*'))
    weather_data: dict = ujson.load(random.choice(weather_files).open('r', encoding='utf8'))

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

    return TarkovSuccessResponse(data=weather_data)


@misc_router.post('/client/handbook/templates')
def client_handbook_templates() -> TarkovSuccessResponse[dict]:
    data: dict = {}
    for template_path in db_dir.joinpath('templates').glob('*.json'):
        data[template_path.stem] = ujson.load(template_path.open('r', encoding='utf8'))

    return TarkovSuccessResponse(data=data)


@misc_router.post('/client/handbook/builds/my/list')
def client_handbook_builds_my_list() -> TarkovSuccessResponse:
    return TarkovSuccessResponse(data=[])  # TODO load user builds


@misc_router.post('/client/quest/list')
def client_quest_list() -> TarkovSuccessResponse[list]:
    all_quests: list = ujson.load(db_dir.joinpath('quests', 'all.json').open('r', encoding='utf8'))
    return TarkovSuccessResponse(data=all_quests)


@misc_router.post('/client/server/list')
def client_server_list(request: Request) -> TarkovSuccessResponse[list]:
    return TarkovSuccessResponse(data=[
        {
            'ip': get_request_url_root(request),
            'port': 5000
        }
    ])


@misc_router.post('/client/checkVersion')
def client_check_version() -> TarkovSuccessResponse:
    return TarkovSuccessResponse(data={
        'isvalid': True,
        'latestVersion': ''
    })


@misc_router.post('/client/game/logout')
def client_game_logout() -> TarkovSuccessResponse:
    return TarkovSuccessResponse(data={
        "status": "ok"
    })
