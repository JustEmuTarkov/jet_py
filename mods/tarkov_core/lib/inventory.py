from __future__ import annotations

import copy
from traceback import TracebackException
from types import TracebackType
from typing import List, Tuple, Generator, Union, Optional

import ujson

from mods.tarkov_core.functions.items import get_item_template
from mods.tarkov_core.lib.items import Item, ItemExtraSize, ItemNotFoundError, MoveLocation, Stash
from server import root_dir


class InventoryManager:
    def __init__(self, profile_id: str):
        self.inventory: Inventory = Inventory(profile_id=profile_id)

    def __enter__(self) -> Inventory:
        self.inventory.sync()
        return self.inventory

    def __exit__(self, exc: Exception, exc_val: TracebackException, exc_tb: TracebackType):
        if exc_val:
            raise exc_val
        self.inventory.save()


class Inventory:
    def __init__(self, profile_id: str):
        self.__path = root_dir.joinpath('resources', 'profiles', profile_id, 'pmc_inventory.json')
        self.stash: Optional[Stash] = None

    @property
    def items(self) -> List[Item]:
        return self.stash['items']

    @property
    def stash_id(self) -> str:
        return self.stash['stash']

    @property
    def equipment_id(self) -> str:
        return self.stash['equipment']

    def sync(self):
        self.stash = ujson.load(self.__path.open('r', encoding='utf8'))

    def save(self):
        ujson.dump(self.stash, self.__path.open('w', encoding='utf8'))

    def get_item(self, item_id: str):
        try:
            return next(item for item in self.items if item['_id'] == item_id)
        except StopIteration:
            raise ItemNotFoundError

    def get_item_size(self, item: Item) -> Tuple[int, int]:
        props = get_item_template(item)['_props']
        width = props['Width']
        height = props['Height']

        extra_size: ItemExtraSize = {
            'left': 0,
            'right': 0,
            'up': 0,
            'down': 0,
        }

        for child in self.iter_item_children(item):
            child_template = get_item_template(child)
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
                extra_size = self.__merge_extra_size(extra_size, child_extra_size)

        width = width + extra_size['left'] + extra_size['right']
        height = height + extra_size['up'] + extra_size['down']
        return width, height

    @staticmethod
    def __merge_extra_size(first: ItemExtraSize, second: ItemExtraSize) -> ItemExtraSize:
        extra_size = copy.copy(first)
        extra_size['left'] = max(first['left'], second['left'])
        extra_size['right'] = max(first['right'], second['right'])
        extra_size['up'] = max(first['up'], second['up'])
        extra_size['down'] = max(first['down'], second['down'])
        return extra_size

    def iter_item_children(self, item: Item) -> Generator[Item, None, None]:
        """
        Iterates over item's children
        """
        for stash_item in self.items:
            try:
                if stash_item['parentId'] == item['_id']:
                    yield stash_item
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

    def add_item(self, item):
        raise NotImplementedError()

    def get_stash_map(self) -> List[List[Union[bool]]]:
        stash_item = self.get_item(self.stash_id)
        stash_template = get_item_template(stash_item)
        grids_props = stash_template['_props']['Grids'][0]['_props']
        width = grids_props['cellsH']
        height = grids_props['cellsV']

        stash_map = [[False for _ in range(height)] for _ in range(width)]

        for item in (item for item in self.iter_item_children(stash_item) if item['slotId'] == 'hideout'):
            item_x, item_y = item['location']['x'], item['location']['y']
            width, height = self.get_item_size(item)

            for x in range(item_x, item_x + width):
                for y in (item_y, item_y + height):
                    stash_map[x][y] = True

        return stash_map

    def __can_place(self, item: Item, x, y, stash_map: List[List]) -> bool:
        item_x, item_y = self.get_item_size(item)
        for x_ in range(x, x + item_x):
            for y_ in range(y, y + item_x):
                if stash_map[x_][y_]:
                    return False
        return True

    def try_place(self, item: Item):
        stash_map = self.get_stash_map()
        stash_width, stash_height = len(stash_map), len(stash_map[0])

        for x in range(stash_width):
            for y in range(stash_height):
                if self.__can_place(item, x, y, stash_map):
                    return x, y

        raise Exception

    def move_item(self, item: Item, location: MoveLocation):
        if 'location' in location:
            item['location'] = location['location']
        else:
            del item['location']

        if location['container'] == 'cartridges':
            mag = self.get_item(location['id'])
            bullet_stack_count = len(list(self.iter_item_children(mag)))

            last_bullet_stack = max(self.iter_item_children(mag), key=lambda stack: stack['location'])
            # TODO bullet stacking
            if last_bullet_stack['_tpl'] == item['_tpl']:
                last_bullet_stack['upd']['StackObjectsCount'] += item['upd']['StackObjectsCount']
            item['location'] = bullet_stack_count

        item['parentId'] = location['id']
        item['slotId'] = location['container']
