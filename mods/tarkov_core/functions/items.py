from typing import Dict, Union

import ujson

from mods.tarkov_core.lib.items import Item, ItemNotFoundError
from server import db_dir


class ItemTemplatesRepository:
    def __init__(self):
        self.__item_templates = self.__read_item_templates()

    @staticmethod
    def __read_item_templates():
        item_templates = {}
        for item_file_path in db_dir.joinpath('items').glob('*'):
            items_data = ujson.load(item_file_path.open('r', encoding='utf8'))
            for item in items_data:
                item_templates[item['_id']] = item
        return item_templates

    @property
    def templates(self) -> Dict[str, Dict]:
        return self.__item_templates

    def get_template(self, item: Union[Item, str]):
        if isinstance(item, dict):
            item = item['_tpl']

        try:
            return self.__item_templates[item]
        except KeyError:
            raise ItemNotFoundError()


item_templates_repository = ItemTemplatesRepository()
