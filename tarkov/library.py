from functools import lru_cache
from pathlib import Path

import ujson

from server import db_dir


def load_locale(locale_name: str) -> dict:
    locale_data = {}
    excluded_files = ("menu", locale_name)
    locale_dir = db_dir.joinpath("locales", locale_name)
    for file in (
        path for path in locale_dir.glob("*.json") if path.stem not in excluded_files
    ):
        locale_data[file.stem] = ujson.load(file.open("r", encoding="utf8"))
    return locale_data


@lru_cache()
def concat_items_files_into_array(path: Path) -> list:
    data = []
    for file in path.glob("*.json"):
        data.append(ujson.load(file.open("r", encoding="utf8")))
    return data
