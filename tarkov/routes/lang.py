from functools import lru_cache

import ujson
from flask import Blueprint

from server import db_dir
from server.utils import tarkov_response, zlib_middleware
from tarkov.library import load_locale

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/menu/locale/<locale_type>', methods=['POST', 'GET'])  # TODO Change to dynamic
@zlib_middleware
@tarkov_response
@lru_cache(8)
def client_menu_locale_en(locale_type: str):
    locale_path = db_dir / 'locales' / locale_type / 'menu.json'
    locale = ujson.load(locale_path.open('r', encoding='utf8'))['data']
    return locale


@blueprint.route('/client/languages', methods=['GET', 'POST'])
@zlib_middleware
@tarkov_response
def client_languages():
    languages_data_list = []
    languages_dir = db_dir / 'locales'
    for dir_ in languages_dir.glob('*'):
        language_file = dir_ / f'{dir_.stem}.json'
        languages_data_list.append(ujson.load(language_file.open('r', encoding='utf8')))

    return languages_data_list


@blueprint.route('/client/locale/<locale_name>', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
@lru_cache(8)
def client_locale(locale_name: str):
    return load_locale(locale_name)
