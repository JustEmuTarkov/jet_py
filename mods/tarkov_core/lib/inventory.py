from __future__ import annotations

import abc
import copy
import random
import string
from traceback import TracebackException
from types import TracebackType
from typing import List, Tuple, Generator, Optional, Iterable

import ujson

from mods.tarkov_core.functions.items import item_templates_repository
from mods.tarkov_core.lib.items import Item, ItemExtraSize, ItemNotFoundError, MoveLocation, Stash, ItemLocation, \
    ItemOrientationEnum
from server import root_dir
from tarkov_core.lib.items import ItemId


class InventoryManager:
    def __init__(self, profile_id: str):
        self.__inventory: Inventory = Inventory(profile_id=profile_id)

    @property
    def inventory(self):
        return self.__inventory

    def __enter__(self) -> Inventory:
        self.inventory.sync()
        return self.inventory

    def __exit__(self, exc: Exception, exc_val: TracebackException, exc_tb: TracebackType):
        if exc_val:
            raise exc_val
        self.inventory.flush()


def merge_extra_size(first: ItemExtraSize, second: ItemExtraSize) -> ItemExtraSize:
    extra_size = copy.copy(first)
    extra_size['left'] = max(first['left'], second['left'])
    extra_size['right'] = max(first['right'], second['right'])
    extra_size['up'] = max(first['up'], second['up'])
    extra_size['down'] = max(first['down'], second['down'])
    return extra_size


def generate_item_id() -> ItemId:
    population = string.ascii_letters + string.digits
    return ''.join(random.choices(population, k=24))


InventoryItems = List[Item]


class ImmutableInventory(metaclass=abc.ABCMeta):
    """
    Implements inventory accessor methods like searching for item, getting it's children without mutating state
    """

    @property
    @abc.abstractmethod
    def items(self) -> InventoryItems:
        pass

    def get_item(self, item_id: str):
        """
        Retrieves item from inventory by it's id

        :param item_id: Item id
        :return: Item instance (dict)
        """
        try:
            return next(item for item in self.items if item['_id'] == item_id)
        except StopIteration as error:
            raise ItemNotFoundError from error

    def get_item_size(self, item: Item) -> Tuple[int, int]:
        """
        Return size of the item according to it's attachments, etc.

        :return: Tuple[width, height]
        """
        # TODO: item folding isn't taken into account
        template = item_templates_repository.get_template(item)
        props = template['_props']
        width = props['Width']
        height = props['Height']

        if not props['MergesWithChildren']:
            return width, height

        extra_size: ItemExtraSize = {
            'left': 0,
            'right': 0,
            'up': 0,
            'down': 0,
        }

        for child in self.iter_item_children_recursively(item):
            child_template = item_templates_repository.get_template(child)
            child_props = child_template['_props']
            child_extra_size: ItemExtraSize = {
                'left': child_template['_props']['ExtraSizeLeft'],
                'right': child_template['_props']['ExtraSizeRight'],
                'up': child_template['_props']['ExtraSizeUp'],
                'down': child_template['_props']['ExtraSizeDown'],
            }
            if child_props['ExtraSizeForceAdd']:
                extra_size['left'] += child_extra_size['left']
                extra_size['right'] += child_extra_size['right']
                extra_size['up'] += child_extra_size['up']
                extra_size['down'] += child_extra_size['down']
            else:
                extra_size = merge_extra_size(extra_size, child_extra_size)

        width = width + extra_size['left'] + extra_size['right']
        height = height + extra_size['up'] + extra_size['down']
        return width, height

    def iter_item_children(self, item: Item) -> Generator[Item, None, None]:
        """
        Iterates over item's children
        """
        for children in self.items:
            try:
                if children['parentId'] == item['_id']:
                    yield children
            except KeyError:
                pass

    def iter_item_children_recursively(self, item: Item) -> Generator[Item, None, None]:
        """
        Iterates over item's children recursively
        """
        items = list(self.iter_item_children(item))

        while items:
            item: Item = items.pop()
            items.extend(self.iter_item_children(item))
            yield item


class StashMap:
    def __init__(self, inventory: InventoryWithGrid):
        self.inventory = inventory
        self.width, self.height = inventory.grid_size
        self.map = [[False for _ in range(self.height)] for _ in range(self.width)]
        inventory_root = inventory.get_item(inventory.stash_id)

        for item in (i for i in inventory.iter_item_children(inventory_root) if i['slotId'] == 'hideout'):
            item_x, item_y = item['location']['x'], item['location']['y']
            width, height = self.inventory.get_item_size(item)

            if item['location']['r'] == 'Vertical':
                width, height = height, width

            for x in range(item_x, item_x + width):
                for y in range(item_y, item_y + height):
                    self.map[x][y] = True

    def iter_cells(self) -> Generator[Tuple[int, int], None, None]:
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def __can_place(self, item: Item, x: int, y: int, orientation: ItemOrientationEnum) -> bool:
        width, height = self.inventory.get_item_size(item)
        if orientation == ItemOrientationEnum.Vertical:
            width, height = height, width

        for x_ in range(x, x + width):
            for y_ in range(y, y + height):
                try:
                    if self.map[x_][y_]:
                        return False
                except IndexError:
                    return False
        return True

    def find_location_for_item(self, item: Item, *, auto_fill=False) -> ItemLocation:
        for x, y in self.iter_cells():
            for orientation in ItemOrientationEnum:
                if self.__can_place(item, x, y, orientation):
                    if auto_fill:
                        self.fill(item, x, y, orientation)
                    return ItemLocation(x=x, y=y, r=orientation.value, isSearched=True)
        raise Exception('Cannot place item')

    def fill(self, item: Item, x: int, y: int, orientation: ItemOrientationEnum):
        width, height = self.inventory.get_item_size(item)
        if orientation == ItemOrientationEnum.Vertical:
            width, height = height, width

        for x_ in range(x, x + width):
            for y_ in range(y, y + height):
                self.map[x_][y_] = True


class MutableInventory(ImmutableInventory, metaclass=abc.ABCMeta):

    def remove_item(self, item: Item):
        """
        Removes item from inventory
        """
        self.items.remove(item)
        for child in self.iter_item_children_recursively(item):
            self.items.remove(child)

    def add_item(self, item: Item):
        """
        Adds item into inventory
        """
        self.items.append(item)

    def add_items(self, items: Iterable[Item]):
        """
        Adds multiple items into inventory
        """

        self.items.extend(items)

    def merge(self, item: Item, with_: Item):
        """
        Merges item with target item, item template ids should be same

        :param item: Item that will be merged and removed
        :param with_: Target item
        """
        if not item['_tpl'] == with_['_tpl']:
            raise ValueError('Item templates don\'t match')

        self.remove_item(item)
        with_['upd']['StackObjectsCount'] += item['upd']['StackObjectsCount']

    @staticmethod
    def transfer(item: Item, with_: Item, count: int):
        """
        :param item: Donor item
        :param with_: Target item
        :param count: Amount to transfer
        """
        item['upd']['StackObjectsCount'] -= count
        with_['upd']['StackObjectsCount'] += count

    @staticmethod
    def fold(item: Item, folded: bool):
        """
        Folds item
        """
        item['upd']['Foldable']['Folded'] = folded


class InventoryWithGrid(MutableInventory, metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def grid_size(self) -> Tuple[int, int]:
        """
        :return: Grid size: Tuple[width, height] of inventory
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def stash_id(self) -> str:
        """
        :return: Id of stash item
        """
        raise NotImplementedError()

    def move_item(self, item: Item, location: MoveLocation):
        """
        Moves item to location
        """
        raise NotImplementedError()

    def split_item(self, item: Item, location: MoveLocation, count: int) -> Item:
        """
        Splits count from item into location

        :return: New item
        """
        raise NotImplementedError()


class Inventory(InventoryWithGrid):
    @property
    def grid_size(self) -> Tuple[int, int]:
        stash_item = self.get_item(self.stash_id)
        stash_template = item_templates_repository.get_template(stash_item)
        grids_props = stash_template['_props']['Grids'][0]['_props']
        width, height = grids_props['cellsH'], grids_props['cellsV']
        return width, height

    def __init__(self, profile_id: str):
        self.__path = root_dir.joinpath('resources', 'profiles', profile_id, 'pmc_inventory.json')
        self.stash: Optional[Stash] = None

    @property
    def items(self):
        return self.stash['items']

    @property
    def stash_id(self) -> str:
        return self.stash['stash']

    @property
    def equipment_id(self) -> str:
        return self.stash['equipment']

    def sync(self):
        """
        Reads inventory file from disk
        """
        self.stash = ujson.load(self.__path.open('r', encoding='utf8'))

    def flush(self):
        """
        Writes inventory file to disk
        """
        ujson.dump(self.stash, self.__path.open('w', encoding='utf8'), indent=4)

    @staticmethod
    def examine(item: Item):
        if 'location' in item:
            location: ItemLocation = item['location']
            location['isSearched'] = True
