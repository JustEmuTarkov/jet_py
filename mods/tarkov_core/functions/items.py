from typing import Dict, Union, Optional

import ujson

from mods.tarkov_core.lib.items import Item, ItemNotFoundError
from server import db_dir


class ItemTemplatesRepository:
    def __init__(self):
        self.__item_templates = self.__read_item_templates()
        self.__item_categories = self.__read_item_categories()

    @staticmethod
    def __read_item_templates():
        item_templates = {}
        for item_file_path in db_dir.joinpath('items').glob('*'):
            items_data = ujson.load(item_file_path.open('r', encoding='utf8'))
            for item in items_data:
                item_templates[item['_id']] = item
        return item_templates

    @staticmethod
    def __read_item_categories():
        items = ujson.load(db_dir.joinpath('templates', 'items.json').open('r', encoding='utf8'))
        items = {item['Id']: item for item in items}
        return items

    @property
    def templates(self) -> Dict[str, Dict]:
        return self.__item_templates

    def get_template(self, item: Union[Item, str]):
        if isinstance(item, dict):
            item = item['_tpl']

        try:
            return self.__item_templates[item]
        except KeyError as error:
            raise ItemNotFoundError() from error

    def get_category(self, item: Item) -> Optional[str]:
        try:
            return self.__item_categories[item['_tpl']]['ParentId']
        except KeyError:
            return None


item_templates_repository = ItemTemplatesRepository()
