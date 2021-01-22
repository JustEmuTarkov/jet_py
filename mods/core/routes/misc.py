import datetime
import random

import ujson
from flask import Blueprint, request, send_file

from mods.core.lib.items import ItemTemplatesRepository
from server import app, db_dir, start_time, root_dir
from server.utils import game_response_middleware

blueprint = Blueprint(__name__, __name__)


@app.route('/client/locations', methods=['GET', 'POST'])
@game_response_middleware(is_static=True)
def client_locations():
    locations_base = db_dir / 'base' / 'locations.json'
    locations_base = ujson.load(locations_base.open('r'))

    for file in (db_dir / 'locations').glob('*.json'):
        map_data = ujson.load(file.open('r'))
        map_id = map_data['base']['_Id']
        locations_base['locations'][map_id] = map_data['base']

    return locations_base


@app.route('/client/game/start', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def client_game_start():
    return None  # TODO Add account data, check if character exists


@app.route('/client/game/version/validate', methods=['POST'])
@game_response_middleware(is_static=True)
def client_game_version_validate():
    return None


@app.route('/client/game/config', methods=['GET', 'POST'])
@game_response_middleware()
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
@game_response_middleware()
def client_game_keepalive():
    if 'PHPSESSID' in request.cookies:
        return {"msg": "OK"}
    return {"msg": "No Session"}


@app.route('/client/items', methods=['GET', 'POST'])
@game_response_middleware(is_static=True)
def client_items():
    return {
        template.id: template.dict()
        for template in ItemTemplatesRepository().templates.values()
    }


@app.route('/client/customization', methods=['GET', 'POST'])
@game_response_middleware(is_static=True)
def client_customization():
    customization = {}
    for customization_file_path in (db_dir / 'customization').glob('*'):
        customization_data = ujson.load(customization_file_path.open('r', encoding='utf8'))
        customization_id = customization_data['_id']
        customization[customization_id] = customization_data

    return customization


@app.route('/client/globals', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def client_globals():
    globals_base = db_dir / 'base' / 'globals.json'
    globals_base = ujson.load(globals_base.open('r', encoding='utf8'))
    return globals_base


@app.route('/client/weather', methods=['POST', 'GET'])
@game_response_middleware()
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
@game_response_middleware(is_static=True)
def client_handbook_templates():
    data = {}
    for template_path in db_dir.joinpath('templates').glob('*.json'):
        data[template_path.stem] = ujson.load(template_path.open('r', encoding='utf8'))

    return data


@app.route('/client/handbook/builds/my/list', methods=['POST', 'GET'])
@game_response_middleware()
def client_handbook_builds_my_list():
    return []  # TODO load user builds


@app.route('/client/quest/list', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def client_quest_list():
    return ujson.load(db_dir.joinpath('quests', 'all.json').open('r', encoding='utf8'))


@app.route('/client/mail/dialog/list', methods=['POST', 'GET'])
@game_response_middleware()
def mail_dialog_list():
    return {}  # TODO create dialogue wrapper


@app.route('/client/server/list', methods=['POST', 'GET'])
@game_response_middleware()
def client_server_list():
    return [
        {
            'ip': request.url_root,
            'port': 5000
        }
    ]


@app.route('/client/checkVersion', methods=['POST', 'GET'])
@game_response_middleware()
def client_check_version():
    return {
        'isvalid': True,
        'latestVersion': ''
    }


@app.route('/client/game/logout', methods=['POST', 'GET'])
@game_response_middleware()
def client_game_logout():
    return {
        "status": "ok"
    }


@app.route('/files/<path:file_path>', methods=['POST', 'GET'])
def static_files(file_path):
    print(file_path)
    file = root_dir.joinpath('static', file_path)
    if file.exists():
        return send_file(file)
    return '', 404
