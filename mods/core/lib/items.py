from __future__ import annotations

import copy
import enum
import uuid
from typing import TypedDict, Literal, Union, List, NewType, Dict, Iterable, cast

import ujson

from mods.core.lib import SingletonMeta, NotFoundError
from mods.core.models import ItemTemplate, NodeTemplate
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
    """
    Generates new item id

    :return: Generated item id
    """
    unique_id = str(uuid.uuid4())
    unique_id = ''.join(unique_id.split('-')[1:])

    return ItemId(unique_id)


def regenerate_items_ids(items: List[Item]):
    """
    Generates new ids for all items in list (mutates the list)

    :param items: List[Item]
    :return: None
    """
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
    __item_templates: Dict[TemplateId, Union[ItemTemplate, NodeTemplate]]

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
                if item['_type'] == 'Item':
                    item_templates[item['_id']] = ItemTemplate(**item)
                elif item['_type'] == 'Node':
                    item_templates[item['_id']] = NodeTemplate(**item)

        return item_templates

    @staticmethod
    def __read_item_categories():
        items = ujson.load(db_dir.joinpath('templates', 'items.json').open('r', encoding='utf8'))
        items = {item['Id']: item for item in items}
        return items

    @property
    def templates(self):
        return self.__item_templates

    def get_template(self, item_id: Union[Item, TemplateId]) -> ItemTemplate:
        """
        Returns template of item

        :param item_id: Item or TemplateId
        :return: Item Template
        """
        if isinstance(item_id, dict):
            item_id = item_id['_tpl']

        try:
            item_template = self.__item_templates[item_id]
        except KeyError as error:
            raise ItemNotFoundError(f'Can not found ItemTemplate with id {item_id}') from error

        if item_template.type == 'Node':
            raise NotFoundError(f'Can not found ItemTemplate with id {item_id}, however node was found.')

        return cast(ItemTemplate, item_template)

    def iter_template_children(self, template_id: TemplateId) -> Iterable[Union[NodeTemplate, ItemTemplate]]:
        templates: List[Union[NodeTemplate, ItemTemplate]] = [self.get_template(template_id)]
        while templates:
            template = templates.pop()
            yield template

            for child in self.__item_templates.values():
                if child.parent == template.id:
                    templates.append(child)

    def get_template_items(self, template_id: TemplateId) -> List[ItemTemplate]:
        """
        Returns all items of given category (all barter items for example)

        :param template_id:
        :return: All items of a category
        """
        template = self.get_template(template_id)
        if template.type == 'Item':
            return [template]
        return cast(List[ItemTemplate], [tpl for tpl in self.iter_template_children(template_id) if tpl.type == 'Item'])

    def get_category(self, item: Item):
        return self.__item_categories[item['_tpl']]['ParentId']

    def get_preset(self, template_id: TemplateId) -> List[Item]:
        """
        :param template_id:
        :return: Preset of an item from globals
        """
        item_presets = self.globals['ItemPresets']
        try:
            items = copy.deepcopy(item_presets[template_id]['_items'])
            regenerate_items_ids(items)
            return items
        except KeyError as e:
            raise NotFoundError() from e

    @staticmethod
    def __create_item(item_template: ItemTemplate, count: int = 1) -> Item:
        """
        Creates new item stack with size of :count:

        :param item_template: Item template to create item from
        :param count: Amount of items in stack
        :return: new Item
        """
        item = Item(
            _id=generate_item_id(),
            _tpl=TemplateId(item_template.id),
        )

        if count > 1:
            item['upd'] = ItemUpd(StackObjectsCount=count)

        #  Item is either medkit or a painkiller
        if item_template.parent in ('5448f39d4bdc2d0a728b4568', '5448f3a14bdc2d27728b4569'):
            if 'upd' not in item:
                item['upd'] = {}

            medkit_max_hp = item_template.props.MaxHpResource
            assert medkit_max_hp is not None

            item['upd']['MedKit'] = ItemUpdMedKit(HpResource=medkit_max_hp)

        return item

    @staticmethod
    def create_item(template_id: TemplateId, count: int = 1) -> List[Item]:
        if count == 0:
            raise ValueError('Cannot create 0 items')

        repository = ItemTemplatesRepository()

        #  Try to return a preset if it exists
        try:
            return repository.get_preset(template_id)
        except NotFoundError:
            pass

        item_template = repository.get_template(template_id)

        #  If we need only one item them we will just return it
        if count == 1:
            return [ItemTemplatesRepository.__create_item(item_template)]

        items: List[Item] = []
        stack_size = item_template.props.StackMaxSize

        #  Create multiple stacks of items (Say 80 rounds of 5.45 ammo it will create two stacks (60 and 20))
        for _ in range(count, stack_size, count):
            items.append(ItemTemplatesRepository.__create_item(item_template, count))

        if stack_size % count:
            items.append(ItemTemplatesRepository.__create_item(item_template, stack_size % count))

        return items
