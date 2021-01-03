from __future__ import annotations

import enum
from typing import TypedDict, Literal, Union, List, NewType, Dict

import ujson

from mods.core.lib import SingletonMeta
from server import db_dir


class Stash(TypedDict):
    equipment: str
    stash: str
    questRaidItems: str
    questStashItems: str
    fastPanel: dict
    items: List[Item]


ItemId = NewType('ItemId', str)
TemplateId = NewType('TemplateId', str)


class ItemBase(TypedDict):
    _id: ItemId
    _tpl: TemplateId


class Item(ItemBase, total=False):
    slotId: str
    parentId: ItemId
    location: Union[ItemLocation, int]
    upd: ItemUpd


class ItemUpd(TypedDict, total=False):
    StackObjectsCount: int
    SpawnedInSession: bool
    Repairable: ItemUpdRepairable
    Foldable: ItemUpdFoldable
    FireMode: ItemUpdFireMode


class ItemUpdRepairable(TypedDict):
    MaxDurability: int
    Durability: int


class ItemUpdFoldable(TypedDict):
    Folded: bool


class ItemUpdFireMode(TypedDict):
    FireMode: Literal['single']


class ItemLocation(TypedDict, total=False):
    x: int
    y: int
    r: ItemOrientation
    isSearched: bool


class ItemExtraSize(TypedDict):
    up: int
    down: int
    left: int
    right: int


class ItemNotFoundError(Exception):
    pass


ItemOrientation = Literal['Horizontal', 'Vertical']


class ItemOrientationEnum(enum.Enum):
    Horizontal = 'Horizontal'
    Vertical = 'Vertical'


class MoveLocation(TypedDict):
    id: str
    container: str
    location: ItemLocation


class ItemTemplatesRepository(metaclass=SingletonMeta):
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

    def get_category(self, item: Item):
        return self.__item_categories[item['_tpl']]['ParentId']