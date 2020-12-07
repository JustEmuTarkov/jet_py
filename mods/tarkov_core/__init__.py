import datetime
import random

import ujson
from flask import request

from core.app import app
from core.logger import logger
from core.main import db_dir, start_time
from core.package_lib import PackageMeta, BasePackage
from core.utils import route_decorator
from mods.tarkov_core import routes
from mods.tarkov_core.library import load_locale
from mods.tarkov_core.routes import friend, hideout, lang, notifier, profile, single_player, trader


class Package(BasePackage):
    class Meta(PackageMeta):
        name = 'core'
        version = '0.0.1'
        dependencies = []

    def __init__(self):
        super().__init__()
        logger.info('Tarkov core package is loading')

    def on_load(self):
        app.register_blueprint(blueprint=friend.blueprint)
        app.register_blueprint(blueprint=hideout.blueprint)
        app.register_blueprint(blueprint=lang.blueprint)
        app.register_blueprint(blueprint=notifier.blueprint)
        app.register_blueprint(blueprint=profile.blueprint)
        app.register_blueprint(blueprint=single_player.blueprint)
        app.register_blueprint(trader.blueprint)

        @app.route('/client/locations', methods=['GET', 'POST'])
        @route_decorator(is_static=1)
        def client_locations():
            locations_base = db_dir / 'base' / 'locations.json'
            locations_base = ujson.load(locations_base.open('r'))

            for file in (db_dir / 'locations').glob('*.json'):
                map_name, map_contents = file.stem, ujson.load(file.open('r'))['base']
                locations_base['locations'][map_name] = map_contents

            return locations_base

        @app.route('/client/game/start', methods=['POST'])
        @route_decorator(is_static=1)
        def client_game_start():
            return None  # TODO Add account data, check if character exists

        @app.route('/client/game/version/validate', methods=['POST'])
        @route_decorator(is_static=1)
        def client_game_version_validate():
            return None

        @app.route('/client/game/config', methods=['GET', 'POST'])
        @route_decorator()
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
        @route_decorator()
        def client_game_keepalive():
            if 'PHPSESSID' in request.cookies:
                return {"msg": "OK"}
            return {"msg": "No Session"}

        @app.route('/client/items', methods=['GET', 'POST'])
        @route_decorator(is_static=1)
        def client_items():
            items_dict = {}
            for item_file_path in (db_dir / 'items').glob('*'):
                items_data = ujson.load(item_file_path.open('r', encoding='utf8'))
                for item in items_data:
                    items_dict[item['_id']] = item

            return items_dict

        @app.route('/client/customization', methods=['GET', 'POST'])
        @route_decorator(is_static=1)
        def client_customization():
            customization = {}
            for customization_file_path in (db_dir / 'customization').glob('*'):
                customization_data = ujson.load(customization_file_path.open('r', encoding='utf8'))
                customization_id = customization_data['_id']
                customization[customization_id] = customization_data

            return customization

        @app.route('/client/globals', methods=['POST', 'GET'])
        @route_decorator(is_static=1)
        def client_globals():
            globals_base = db_dir / 'base' / 'globals.json'
            globals_base = ujson.load(globals_base.open('r', encoding='utf8'))
            return globals_base

        @app.route('/client/weather', methods=['POST', 'GET'])
        @route_decorator()
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
        @route_decorator(is_static=1)
        def client_handbook_templates():
            data = {}
            for template_path in db_dir.joinpath('templates').glob('*.json'):
                data[template_path.stem] = ujson.load(template_path.open('r', encoding='utf8'))

            return data

        @app.route('/client/handbook/builds/my/list', methods=['POST', 'GET'])
        @route_decorator()
        def client_handbook_builds_my_list():
            return []  # TODO load user builds

        @app.route('/client/quest/list', methods=['POST', 'GET'])
        @route_decorator(is_static=1)
        def client_quest_list():
            return ujson.load(db_dir.joinpath('quests', 'all.json').open('r', encoding='utf8'))

        @app.route('/client/mail/dialog/list', methods=['POST', 'GET'])
        @route_decorator()
        def mail_dialog_list():
            return {}  # TODO create dialogue wrapper

        @app.route('/client/server/list', methods=['POST', 'GET'])
        @route_decorator()
        def client_server_list():
            return [
                {
                    'ip': request.url_root,
                    'port': 5000
                }
            ]

        @app.route('/client/checkVersion', methods=['POST', 'GET'])
        @route_decorator()
        def client_check_version():
            return {
                'isvalid': True,
                'latestVersion': ''
            }

        @app.route('/client/game/logout', methods=['POST', 'GET'])
        @route_decorator()
        def client_game_logout():
            return {
                "status": "ok"
            }
