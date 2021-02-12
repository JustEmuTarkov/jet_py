from functools import lru_cache

import ujson
from fastapi import APIRouter

from server import db_dir
from tarkov.library import load_locale
from tarkov.models import TarkovSuccessResponse

router = APIRouter(prefix='', tags=['Locale'])


@lru_cache(8)
def _client_menu_locale(locale_type: str) -> dict:
    locale_path = db_dir / 'locales' / locale_type / 'menu.json'
    return ujson.load(locale_path.open('r', encoding='utf8'))['data']


@router.post('/client/menu/locale/{locale_type}')
def client_menu_locale(locale_type: str) -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=_client_menu_locale(locale_type)
    )


@router.post('/client/languages')
def client_languages() -> TarkovSuccessResponse[list]:
    languages_data_list = []
    languages_dir = db_dir / 'locales'
    for dir_ in languages_dir.glob('*'):
        language_file = dir_ / f'{dir_.stem}.json'
        languages_data_list.append(ujson.load(language_file.open('r', encoding='utf8')))

    return TarkovSuccessResponse(data=languages_data_list)


@lru_cache(8)
def _client_locale(locale_name: str) -> dict:
    return load_locale(locale_name)


@router.post('/client/locale/{locale_name}')
def client_locale(locale_name: str) -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(data=_client_locale(locale_name))
