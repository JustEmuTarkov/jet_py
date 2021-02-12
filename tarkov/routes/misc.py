import datetime
import random
from typing import Type

import ujson
from fastapi import APIRouter
from flask import Blueprint, request

from server import app, db_dir, start_time
from server.utils import tarkov_response, zlib_middleware
from tarkov.inventory import item_templates_repository
from tarkov.models import TarkovSuccessResponse

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
def client_game_start() -> str:

    return TarkovSuccessResponse(data=None).json()  # TODO Add account data, check if character exists


@app.route('/client/game/version/validate', methods=['POST'])
@zlib_middleware
@tarkov_response
def client_game_version_validate():
    return None


@app.route('/client/game/config', methods=['GET', 'POST'])
@zlib_middleware
@tarkov_response
def client_game_config():
    url_root = request.url_root
    session_id = request.cookies['PHPSESSID']

    return {
        "queued": False,
        "banTime": 0,
        "hash": "BAN0",
        "lang": "en",
        "aid": session_id,
        "token": "token_" + session_id,
        "taxonomy": "341",
        "activeProfileId":
            "user" + session_id + "pmc",
        "nickname": "user",
        "backend": {
            "Trading": url_root,
            "Messaging": url_root,
            "Main": url_root,
            "RagFair": url_root
        },
        "totalInGame": 0
    }


@app.route('/client/game/keepalive', methods=['GET', 'POST'])
@zlib_middleware
@tarkov_response
def client_game_keepalive():
    if 'PHPSESSID' in request.cookies:
        return {"msg": "OK"}
    return {"msg": "No Session"}


@app.route('/client/items', methods=['GET', 'POST'])
@zlib_middleware
@tarkov_response
def client_items():
    return {
        template.id: template.dict()
        for template in item_templates_repository.templates.values()
    }


@app.route('/client/customization', methods=['GET', 'POST'])
@zlib_middleware
@tarkov_response
def client_customization():
    customization = {}
    for customization_file_path in (db_dir / 'customization').glob('*'):
        customization_data = ujson.load(customization_file_path.open('r', encoding='utf8'))
        customization_id = customization_data['_id']
        customization[customization_id] = customization_data

    return customization


@app.route('/client/globals', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def client_globals():
    globals_base = db_dir / 'base' / 'globals.json'
    globals_base = ujson.load(globals_base.open('r', encoding='utf8'))
    return globals_base


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
