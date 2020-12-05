import datetime
import random
from functools import lru_cache

import ujson
from flask import request

from core.app import app
from core.logger import logger
from core.main import db_dir, root_dir, start_time
from core.package_lib import PackageMeta, BasePackage
from core.utils import route_decorator, TarkovError
from mods.core.lib import load_locale, concat_items_files_into_array


class Package(BasePackage):
    class Meta(PackageMeta):
        name = 'core'
        version = '0.0.1'
        dependencies = []

    def __init__(self):
        super().__init__()
        logger.info('Tarkov core package is loading')

    def on_load(self):
        print("Loading Core Routes")

        @app.route('/', methods=['GET', 'POST'])
        @route_decorator()
        def index_test():
            return request.data

        @app.route('/client/locations', methods=['GET', 'POST'])
        @route_decorator(is_static=True)
        def client_locations():
            locations_base = db_dir / 'base' / 'locations.json'
            locations_base = ujson.load(locations_base.open('r'))

            for file in (db_dir / 'locations').glob('*.json'):
                map_name, map_contents = file.stem, ujson.load(file.open('r'))['base']
                locations_base['locations'][map_name] = map_contents

            return locations_base

        @app.route('/singleplayer/bundles')
        @route_decorator(is_static=True)
        def singleplayer_bundles():
            return {}

        @app.route('/mode/offline')
        @route_decorator(is_static=True)
        def mode_offline():
            return {
                "OfflineLootPatch": True,
                "InsuranceScreenPatch": True,
                "BossSpawnChancePatch": True,
                "BotTemplateLimitPatch": True,
                "RemoveUsedBotProfilePatch": True,
                "OfflineSaveProfilePatch": True,
                "OfflineSpawnPointPatch": True,
                "WeaponDurabilityPatch": True,
                "SingleModeJamPatch": True,
                "ExperienceGainPatch": True,
                "MainMenuControllerPatch": True,
                "PlayerPatch": True,
                "MatchmakerOfflineRaidPatch": True,
                "MatchMakerSelectionLocationScreenPatch": True,
                "GetNewBotTemplatesPatch": True,
                "SpawnPmcPatch": True,
                "CoreDifficultyPatch": True,
                "BotDifficultyPatch": True,
                "OnDeadPatch": True,
                "OnShellEjectEventPatch": True,
                "BotStationaryWeaponPatch": True,
                "BeaconPatch": True,
                "DogtagPatch": True,
                "LoadOfflineRaidScreenPatch": True,
                "ScavPrefabLoadPatch": True,
                "ScavProfileLoadPatch": True,
                "ScavSpawnPointPatch": False,
                "ScavExfilPatch": True,
                "EndByTimerPatch": True
            }

        @app.route('/client/game/start', methods=['POST'])
        @route_decorator(is_static=True)
        def client_game_start():
            return None  # TODO Add account data, check if character exists

        @app.route('/client/menu/locale/<locale_type>', methods=['POST', 'GET'])  # TODO Change to dynamic
        @lru_cache(8)
        @route_decorator(is_static=True)
        def client_menu_locale_en(locale_type: str):
            locale_path = db_dir / 'locales' / locale_type / 'menu.json'
            locale = ujson.load(locale_path.open('r', encoding='utf8'))['data']
            return locale

        @app.route('/client/game/version/validate', methods=['POST'])
        @route_decorator(is_static=True)
        def client_game_version_validate():
            return None

        @app.route('/client/languages', methods=['GET', 'POST'])
        @route_decorator(is_static=True)
        def client_languages():
            languages_data_list = []
            languages_dir = db_dir / 'locales'
            for dir_ in languages_dir.glob('*'):
                language_file = dir_ / f'{dir_.stem}.json'
                languages_data_list.append(ujson.load(language_file.open('r', encoding='utf8')))

            return languages_data_list

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
        @route_decorator(is_static=True)
        def client_items():
            items_dict = {}
            for item_file_path in (db_dir / 'items').glob('*'):
                items_data = ujson.load(item_file_path.open('r', encoding='utf8'))
                for item in items_data:
                    items_dict[item['_id']] = item

            return items_dict

        @app.route('/client/customization', methods=['GET', 'POST'])
        @route_decorator(is_static=True)
        def client_customization():
            customization = {}
            for customization_file_path in (db_dir / 'customization').glob('*'):
                customization_data = ujson.load(customization_file_path.open('r', encoding='utf8'))
                customization_id = customization_data['_id']
                customization[customization_id] = customization_data

            return customization

        @app.route('/client/globals', methods=['POST', 'GET'])
        @route_decorator(is_static=True)
        def client_globals():
            globals_base = db_dir / 'base' / 'globals.json'
            globals_base = ujson.load(globals_base.open('r', encoding='utf8'))
            return globals_base

        @app.route('/client/game/profile/list', methods=['POST', 'GET'])
        @route_decorator()
        def client_game_profile_list():
            profile_dir = root_dir.joinpath('resources', 'profiles')
            pmc_profile = ujson.load((profile_dir / 'character.json').open('r'))
            scav_profile = ujson.load((profile_dir / 'character_scav.json').open('r'))
            return [
                pmc_profile,
                scav_profile,
            ]

        @app.route('/client/game/profile/select', methods=['POST', 'GET'])
        @route_decorator()
        def client_game_profile_list_select():
            return {
                'status': 'ok',
                'notifier': {
                    'server': f'{request.url_root}/',
                    'channel_id': 'testChannel',
                },
            }

        @app.route('/client/profile/status', methods=['POST', 'GET'])
        @route_decorator()
        def client_profile_status():
            session_id = request.cookies['PHPSESSID']
            response = []
            for profile_type in ('scav', 'pmc'):
                response.append({
                    'profileid': f'{profile_type}{session_id}',
                    'status': 'Free',
                    'sid': '',
                    'ip': '',
                    'port': 0
                })

            return response

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

        @app.route('/client/locale/<locale_name>', methods=['POST', 'GET'])
        @lru_cache(8)
        @route_decorator()
        def client_locale(locale_name: str):
            return load_locale(locale_name)

        @app.route('/client/handbook/templates', methods=['POST', 'GET'])
        @route_decorator(is_static=True)
        def client_handbook_templates():
            data = {}
            for template_path in db_dir.joinpath('templates').glob('*.json'):
                data[template_path.stem] = ujson.load(template_path.open('r', encoding='utf8'))

            return data

        @app.route('/client/hideout/areas', methods=['POST', 'GET'])
        @route_decorator(is_static=True)
        def client_hideout_areas():
            hideout_areas_dir = db_dir.joinpath('hideout', 'areas')
            return concat_items_files_into_array(hideout_areas_dir)

        @app.route('/client/hideout/settings', methods=['POST', 'GET'])
        @route_decorator(is_static=True)
        def client_hideout_settings():
            setting_path = db_dir.joinpath('hideout', 'settings.json')
            return ujson.load(setting_path.open('r', encoding='utf8'))

        @app.route('/client/hideout/production/recipes', methods=['POST', 'GET'])
        @route_decorator(is_static=True)
        def client_hideout_production_recipes():
            production_dir = db_dir.joinpath('hideout', 'production')
            return concat_items_files_into_array(production_dir)

        @app.route('/client/hideout/production/scavcase/recipes', methods=['POST', 'GET'])
        @route_decorator(is_static=True)
        def client_hideout_production_scavcase_recipes():
            scavcase_dir = db_dir.joinpath('hideout', 'scavcase')
            return concat_items_files_into_array(scavcase_dir)

        @app.route('/client/handbook/builds/my/list', methods=['POST', 'GET'])
        @route_decorator()
        def client_handbook_builds_my_list():
            return []  # TODO load user builds

        @app.route('/client/quest/list', methods=['POST', 'GET'])
        @route_decorator(is_static=True)
        def client_quest_list():
            return ujson.load(db_dir.joinpath('quests', 'all.json').open('r', encoding='utf8'))

        @app.route('/client/notifier/channel/create', methods=['POST', 'GET'])
        @route_decorator(is_static=True)
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
                "notifierServer": notifier_server_url
            }
            return response

        @app.route('/client/mail/dialog/list', methods=['POST', 'GET'])
        @route_decorator()
        def mail_dialog_list():
            return {}  # TODO create dialogue wrapper

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

        @app.route('/client/trading/customization/storage', methods=['POST', 'GET'])
        @route_decorator()
        def client_trading_customization_storage():
            return ujson.load(root_dir.joinpath('resources', 'profiles', 'storage.json').open('r', encoding='utf8'))

        @app.route('/client/server/list', methods=['POST', 'GET'])
        @route_decorator()
        def client_server_list():
            return [
                {
                    'ip': request.url_root,
                    'port': 5000
                }
            ]

        @app.route('/client/trading/api/getTradersList', methods=['POST', 'GET'])
        @route_decorator(is_static=True)
        def client_trading_api_traderlist():
            traders_path = db_dir.joinpath('base', 'traders')
            paths = set(traders_path.rglob('*/base.json')) - set(traders_path.rglob('ragfair/base.json'))

            traders_data = [ujson.load(file.open('r', encoding='utf8')) for file in paths]
            return traders_data

        @app.route('/client/checkVersion', methods=['POST', 'GET'])
        @route_decorator()
        def client_check_version():
            return {
                'isvalid': True,
                'latestVersion': ''
            }

        @app.route('/notifierServer/get/<string:profile_pk>', methods=['POST', 'GET'])
        @route_decorator()
        def notifierserver_get(profile_pk: str):
            #  ?last_id=default_id
            return {"type": "ping", "eventId": "ping"}
