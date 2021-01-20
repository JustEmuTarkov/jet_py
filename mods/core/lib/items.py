from __future__ import annotations

import copy
import enum
import uuid
from typing import TypedDict, Literal, Union, List, NewType, Dict, Iterable

import ujson

from mods.core.lib import SingletonMeta, NotFoundError
from server import db_dir


class Stash(TypedDict):
    equipment: str
    stash: ItemId
    questRaidItems: str
    questStashItems: str
    fastPanel: dict
    items: List[Item]


ItemId = NewType('ItemId', str)
TemplateId = NewType('TemplateId', str)

# Ammo stack position in magazine, 0 means it's at the bottom of magazine
AmmoStackPosition = NewType('AmmoStackPosition', int)


class ItemBase(TypedDict):
    _id: ItemId
    _tpl: TemplateId


class Item(ItemBase, total=False):
    slotId: str
    parentId: ItemId
    location: Union[ItemLocation, AmmoStackPosition]
    upd: ItemUpd


class ItemUpd(TypedDict, total=False):
    StackObjectsCount: int
    SpawnedInSession: bool
    Repairable: ItemUpdRepairable
    Foldable: ItemUpdFoldable
    FireMode: ItemUpdFireMode
    Resource: ItemUpdResource
    FoodDrink: ItemUpdFoodDrink
    Key: ItemUpdKey
    MedKit: ItemUpdMedKit


class ItemUpdRepairable(TypedDict):
    MaxDurability: int
    Durability: int


class ItemUpdFoldable(TypedDict):
    Folded: bool


class ItemUpdFireMode(TypedDict):
    FireMode: Literal['single', 'fullauto']


class ItemUpdResource(TypedDict):
    Value: int


class ItemUpdFoodDrink(TypedDict):
    HpPercent: int


class ItemUpdKey(TypedDict):
    NumberOfUsages: int


class ItemUpdMedKit(TypedDict):
    HpResource: int


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


class MoveLocationBase(TypedDict):
    id: ItemId
    container: str


class MoveLocation(MoveLocationBase, total=False):
    location: ItemLocation


def generate_item_id() -> ItemId:
    unique_id = str(uuid.uuid4())
    unique_id = ''.join(unique_id.split('-')[1:])

    return ItemId(unique_id)


def regenerate_items_ids(items: List[Item]):
    id_map = {
        item['_id']: generate_item_id() for item in items
    }

    for item in items:
        item['_id'] = id_map[item['_id']]
        try:
            item['parentId'] = id_map[item['parentId']]
        except KeyError:
            pass


class ItemTemplatesRepository(metaclass=SingletonMeta):
    def __init__(self):
        self.__item_templates = self.__read_item_templates()
        self.__item_categories = self.__read_item_categories()

        self.globals = ujson.load(db_dir.joinpath('base', 'globals.json').open(encoding='utf8'))

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

    def get_template(self, item: Union[Item, TemplateId]):
        if isinstance(item, dict):
            item = item['_tpl']

        try:
            return self.__item_templates[item]
        except KeyError as error:
            raise ItemNotFoundError() from error

    def iter_template_children(self, template_id: TemplateId) -> Iterable[Dict]:
        templates = [self.get_template(template_id)]
        while templates:
            template = templates.pop()
            yield template

            for child in self.__item_templates.values():
                if child['_parent'] == template['_id']:
                    templates.append(child)

    def get_template_items(self, template_id: TemplateId) -> List[dict]:
        template: dict = self.get_template(template_id)
        if template['_type'] == 'Item':
            return [template]
        return [tpl for tpl in self.iter_template_children(template_id) if tpl['_type'] == 'Item']

    def get_category(self, item: Item):
        return self.__item_categories[item['_tpl']]['ParentId']

    def get_preset(self, template_id: TemplateId) -> List[Item]:
        item_presets = self.globals['ItemPresets']
        try:
            items = copy.deepcopy(item_presets[template_id]['_items'])
            regenerate_items_ids(items)
            return items
        except KeyError as e:
            raise NotFoundError() from e

    @staticmethod
    def __create_item(item_template: dict, count: int = 1) -> Item:
        item = Item(
            _id=generate_item_id(),
            _tpl=item_template['_id'],
        )

        if count > 1:
            item['upd'] = ItemUpd(StackObjectsCount=count)

        #  Item is either medkit or a painkiller
        if item_template['_parent'] in ('5448f39d4bdc2d0a728b4568', '5448f3a14bdc2d27728b4569'):
            if 'upd' not in item:
                item['upd'] = {}
            item['upd']['MedKit'] = ItemUpdMedKit(HpResource=item_template['_props']['MaxHpResource'])

        return item

    @staticmethod
    def create_item(template_id: TemplateId, count: int = 1) -> List[Item]:
        if count == 0:
            raise ValueError('Cannot create 0 items')

        repository = ItemTemplatesRepository()
        try:
            return repository.get_preset(template_id)
        except NotFoundError:
            pass

        item_template = repository.get_template(template_id)
        if count == 1:
            return [ItemTemplatesRepository.__create_item(item_template)]

        items: List[Item] = []
        stack_size = item_template['_props']['StackMaxSize']

        for _ in range(count, stack_size, count):
            items.append(ItemTemplatesRepository.__create_item(item_template, count))

        if stack_size % count:
            items.append(ItemTemplatesRepository.__create_item(item_template, stack_size % count))

        return items
