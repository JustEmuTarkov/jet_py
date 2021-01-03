from functools import lru_cache

import ujson
from flask import Blueprint

from mods.core.library import load_locale
from server import db_dir
from server.utils import route_decorator

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/menu/locale/<locale_type>', methods=['POST', 'GET'])  # TODO Change to dynamic
@lru_cache(8)
@route_decorator(is_static=True)
def client_menu_locale_en(locale_type: str):
    locale_path = db_dir / 'locales' / locale_type / 'menu.json'
    locale = ujson.load(locale_path.open('r', encoding='utf8'))['data']
    return locale


@blueprint.route('/client/languages', methods=['GET', 'POST'])
@route_decorator(is_static=True)
def client_languages():
    languages_data_list = []
    languages_dir = db_dir / 'locales'
    for dir_ in languages_dir.glob('*'):
        language_file = dir_ / f'{dir_.stem}.json'
        languages_data_list.append(ujson.load(language_file.open('r', encoding='utf8')))

    return languages_data_list


@blueprint.route('/client/locale/<locale_name>', methods=['POST', 'GET'])
@lru_cache(8)
@route_decorator()
def client_locale(locale_name: str):
    return load_locale(locale_name)
