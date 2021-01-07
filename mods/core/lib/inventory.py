from __future__ import annotations

import abc
import copy
import random
import string
from types import TracebackType
from typing import List, Tuple, Generator, Iterable, Type, Optional

import ujson

from mods.core.lib.items import Item, ItemExtraSize, ItemNotFoundError, Stash, ItemLocation, \
    ItemOrientationEnum
from mods.core.lib.items import ItemId
from mods.core.lib.items import ItemTemplatesRepository
from server import root_dir


class InventoryManager:
    def __init__(self, profile_id: str):
        self.__inventory: Inventory = Inventory(profile_id=profile_id)

    @property
    def inventory(self):
        return self.__inventory

    def __enter__(self) -> Inventory:
        self.inventory.sync()
        return self.inventory

    def __exit__(
            self,
            exc: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType]
    ):
        if exc and exc_val:
            raise exc() from exc_val
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
    return ItemId(''.join(random.choices(population, k=24)))


InventoryItems = List[Item]


class ImmutableInventory(metaclass=abc.ABCMeta):
    """
    Implements inventory_manager accessor methods like searching for item, getting it's children without mutating state
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
        template = ItemTemplatesRepository().get_template(item)
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
            child_template = ItemTemplatesRepository().get_template(child)
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

    def iter_item_children(self, item: Item) -> Iterable[Item]:
        """
        Iterates over item's children
        """
        for children in self.items:
            try:
                if children['parentId'] == item['_id']:
                    yield children
            except KeyError:
                pass

    def iter_item_children_recursively(self, item: Item) -> Iterable[Item]:
        """
        Iterates over item's children recursively
        """
        items = list(self.iter_item_children(item))

        while items:
            child: Item = items.pop()
            items.extend(self.iter_item_children(child))
            yield child


class NoSpaceError(Exception):
    pass


class StashMap:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory
        self.width, self.height = inventory.grid_size
        self.map = [[False for _ in range(self.height)] for _ in range(self.width)]
        inventory_root = inventory.get_item(inventory.stash_id)

        for item in (i for i in inventory.iter_item_children(inventory_root) if i['slotId'] == 'hideout'):
            if not isinstance(item['location'], dict):
                continue

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

    def can_place(self, item: Item, location: ItemLocation) -> bool:
        x, y = location['x'], location['y']
        width, height = self.inventory.get_item_size(item)
        if location['r'] == ItemOrientationEnum.Vertical:
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
                location = ItemLocation(x=x, y=y, r=orientation.value)
                if self.can_place(item, location):
                    if auto_fill:
                        self.fill(item, x, y, orientation)
                    return location
        raise NoSpaceError('Cannot place item into inventory')

    def fill(self, item: Item, x: int, y: int, orientation: ItemOrientationEnum):
        width, height = self.inventory.get_item_size(item)
        if orientation == ItemOrientationEnum.Vertical:
            width, height = height, width

        for x_ in range(x, x + width):
            for y_ in range(y, y + height):
                self.map[x_][y_] = True

    def remove(self, item: Item):
        self.__fill_item(item, False)

    def add(self, item: Item):
        self.__fill_item(item, True)

    def __fill_item(self, item: Item, with_: bool):
        if not isinstance(item['location'], dict):
            return

        location: ItemLocation = item['location']
        if item['slotId'] != 'hideout':
            return
        width, height = self.inventory.get_item_size(item)

        if location['r'] == 'Vertical':
            width, height = height, width

        for x in range(location['x'], location['x'] + width):
            for y in range(location['y'], location['y'] + height):
                self.map[x][y] = with_


class MutableInventory(ImmutableInventory, metaclass=abc.ABCMeta):

    def remove_item(self, item: Item):
        """
        Removes item from inventory
        """
        self.items.remove(item)
        for child in self.iter_item_children_recursively(item):
            self.items.remove(child)

    def remove_items(self, items: List[Item]):
        for item in items:
            self.remove_item(item)

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


class Inventory(MutableInventory):
    def __init__(self, profile_id: str):
        super().__init__()
        self.__path = root_dir.joinpath('resources', 'profiles', profile_id, 'pmc_inventory.json')

        self.stash: Stash
        self.stash_map: StashMap

    @property
    def grid_size(self) -> Tuple[int, int]:
        stash_item = self.get_item(self.stash_id)
        stash_template = ItemTemplatesRepository().get_template(stash_item)
        grids_props = stash_template['_props']['Grids'][0]['_props']
        width, height = grids_props['cellsH'], grids_props['cellsV']
        return width, height

    @property
    def items(self):
        return self.stash['items']

    @property
    def stash_id(self):
        return self.stash['stash']

    @property
    def equipment_id(self) -> str:
        return self.stash['equipment']

    def sync(self):
        """
        Reads inventory file from disk
        """
        self.stash = ujson.load(self.__path.open('r', encoding='utf8'))
        self.stash_map = StashMap(self)

    def flush(self):
        """
        Writes inventory file to disk
        """
        ujson.dump(self.stash, self.__path.open('w', encoding='utf8'), indent=4)

    def add_item(self, item: Item, *, location: ItemLocation = None):

        if location is None:
            location = self.stash_map.find_location_for_item(item, auto_fill=True)
        elif not self.stash_map.can_place(item, location):
            raise ValueError('Cannot place item into location since it is taken')

        self.items.append(item)
        item['location'] = location
        item['slotId'] = 'hideout'
        item['parentId'] = self.stash_id

    def move_item(self, item: Item, location: ItemLocation):
        """
        Moves item to location
        """
        self.stash_map.remove(item)
        item['location'] = location
        item['slotId'] = 'hideout'
        item['parentId'] = self.stash_id
        self.stash_map.add(item)

    def split_item(self, item: Item, count: int) -> Item:
        """
        Splits count from item and returns new item
        :return: New item
        """
        if item['upd']['StackObjectsCount'] < count:
            raise ValueError("Can't split from item since stack amount < count")
        item_copy = copy.deepcopy(item)
        item_copy['upd']['StackObjectsCount'] = count

        del item_copy['slotId']
        del item_copy['parentId']
        del item_copy['location']

        item['upd']['StackObjectsCount'] -= count
        if item['upd']['StackObjectsCount'] == 0:
            self.remove_item(item)

        return item_copy

    @staticmethod
    def examine(item: Item):
        if 'location' in item and isinstance(item['location'], dict):
            location: ItemLocation = item['location']
            location['isSearched'] = True
