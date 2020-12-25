from typing import Dict, Union

import ujson

from mods.tarkov_core.lib.items import Item, ItemNotFoundError
from server import db_dir
from server.utils import memoize_once


class ItemTemplatesRepository:
    def __init__(self):
        self.item_templates = self.__read_item_templates()

    @staticmethod
    def __read_item_templates():
        item_templates = {}
        for item_file_path in db_dir.joinpath('items').glob('*'):
            items_data = ujson.load(item_file_path.open('r', encoding='utf8'))
            for item in items_data:
                item_templates[item['_id']] = item
        return item_templates

    def get_templates(self) -> Dict[str, Dict]:
        return self.item_templates

    def get_item_template(self, item: Union[Item, str]):
        if isinstance(item, dict):
            item = item['_tpl']

        try:
            return self.item_templates[item]
        except KeyError:
            raise ItemNotFoundError()


item_templates = {}
for __item_file_path in db_dir.joinpath('items').glob('*'):
    __items_data = ujson.load(__item_file_path.open('r', encoding='utf8'))
    for __item in __items_data:
        item_templates[__item['_id']] = __item


@memoize_once
def get_item_templates() -> Dict[str, Dict]:
    """
    Returns all the items templates from db/items in form of dict
    where key is item[_id] and value is item itself
    """
    return item_templates


def get_item_template(item: Union[Item, str]):
    if isinstance(item, dict):
        item = item['_tpl']

    try:
        return item_templates[item]
    except KeyError:
        raise ItemNotFoundError()
