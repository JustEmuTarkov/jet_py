from functools import lru_cache

import ujson
from fastapi import APIRouter

from server import db_dir
from server.utils import tarkov_response, zlib_middleware
from tarkov.library import load_locale

router = APIRouter(prefix='', tags=['Locale'])


@router.post('/client/menu/locale/{locale_type}')  # TODO Change to dynamic
@lru_cache(8)
def client_menu_locale_en(locale_type: str):
    locale_path = db_dir / 'locales' / locale_type / 'menu.json'
    locale = ujson.load(locale_path.open('r', encoding='utf8'))['data']
    return locale


@router.post('/client/languages')
def client_languages():
    languages_data_list = []
    languages_dir = db_dir / 'locales'
    for dir_ in languages_dir.glob('*'):
        language_file = dir_ / f'{dir_.stem}.json'
        languages_data_list.append(ujson.load(language_file.open('r', encoding='utf8')))

    return languages_data_list


@router.post('/client/locale/{locale_name}')
@lru_cache(8)
def client_locale(locale_name: str):
    return load_locale(locale_name)
