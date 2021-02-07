from __future__ import annotations

import abc
import copy
from typing import Generator, Iterable, List, Tuple, cast

import ujson

import tarkov.profile
from server import root_dir
from tarkov.exceptions import NoSpaceError, NotFoundError
from .dict_models import ItemExtraSize
from .helpers import generate_item_id
from .models import InventoryModel, Item, ItemId, ItemLocation, ItemOrientationEnum, ItemUpdFoldable, TemplateId
from .repositories import item_templates_repository


class ImmutableInventory(metaclass=abc.ABCMeta):
    """
    Implements inventory_manager access methods like searching for item, getting it's children without mutating state
    """

    @property
    @abc.abstractmethod
    def items(self) -> List[Item]:
        pass

    def get_item(self, item_id: str) -> Item:
        """
        Retrieves item from inventory by it's id

        :param item_id: Item id
        :return: Item instance (dict)
        """
        try:
            return next(item for item in self.items if item.id == item_id)
        except StopIteration as error:
            raise NotFoundError from error

    def get_item_by_template(self, template_id: TemplateId) -> Item:
        try:
            return next(item for item in self.items if item.tpl == template_id)
        except StopIteration as error:
            raise NotFoundError from error

    def get_item_size(self, item: Item) -> Tuple[int, int]:
        """
        Return size of the item according to it's attachments, etc.

        :return: Tuple[width, height]
        """
        # TODO: item folding isn't taken into account
        template = item_templates_repository.get_template(item)
        if not template.props.MergesWithChildren:
            return template.props.Width, template.props.Height

        extra_size: ItemExtraSize = {
            'left': 0,
            'right': 0,
            'up': 0,
            'down': 0,
        }

        for child in self.iter_item_children_recursively(item):
            child_template = item_templates_repository.get_template(child)

            child_props = child_template.props
            child_extra_size: ItemExtraSize = {
                'left': child_props.ExtraSizeLeft,
                'right': child_props.ExtraSizeRight,
                'up': child_props.ExtraSizeUp,
                'down': child_props.ExtraSizeDown,
            }
            if child_props.ExtraSizeForceAdd:
                extra_size['left'] += child_extra_size['left']
                extra_size['right'] += child_extra_size['right']
                extra_size['up'] += child_extra_size['up']
                extra_size['down'] += child_extra_size['down']
            else:
                extra_size = merge_extra_size(extra_size, child_extra_size)

        width: int = template.props.Width + extra_size['left'] + extra_size['right']
        height: int = template.props.Height + extra_size['up'] + extra_size['down']

        if not item.upd.Foldable:
            return width, height

        folded = item.upd.Foldable.Folded
        has_stock = any(c.slotId == 'mod_stock' for c in self.iter_item_children_recursively(item))
        if folded and has_stock:
            width -= 1

        return width, height

    def iter_item_children(self, item: Item) -> Iterable[Item]:
        """
        Iterates over item's children
        """
        for children in self.items:
            try:
                if children.parent_id == item.id:
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


class StashMap:
    inventory: GridInventory
    width: int
    height: int
    map: List[List[bool]]

    def __init__(self, inventory: GridInventory):
        self.inventory = inventory
        self.width, self.height = inventory.grid_size
        self.map = [[False for _ in range(self.height)] for _ in range(self.width)]
        inventory_root = inventory.get_item(inventory.root_id)

        for item in (i for i in inventory.iter_item_children(inventory_root) if i.slotId == 'hideout'):
            if not item.slotId:
                continue

            if not isinstance(item.location, ItemLocation):
                continue

            item_x, item_y = item.location.x, item.location.y
            width, height = self.inventory.get_item_size(item)

            if item.location.r == 'Vertical':
                width, height = height, width

            for x in range(item_x, item_x + width):
                for y in range(item_y, item_y + height):
                    self.map[x][y] = True

    def iter_cells(self) -> Generator[Tuple[int, int], None, None]:
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def can_place(self, item: Item, location: ItemLocation) -> bool:
        x, y = location.x, location.y
        width, height = self.inventory.get_item_size(item)

        if location.r == ItemOrientationEnum.Vertical.value:
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
        if not item.location:
            return

        if item.slotId != 'hideout':
            return

        location: ItemLocation = cast(ItemLocation, item.location)
        width, height = self.inventory.get_item_size(item)

        if location.r == ItemOrientationEnum.Vertical.value:
            width, height = height, width

        for x in range(location.x, location.x + width):
            for y in range(location.y, location.y + height):
                self.map[x][y] = with_


class MutableInventory(ImmutableInventory, metaclass=abc.ABCMeta):
    def remove_item(self, item: Item, remove_children=True):
        """
        Removes item from inventory
        """
        self.items.remove(item)
        if not remove_children:
            return

        for child in self.iter_item_children_recursively(item):
            self.items.remove(child)

    def remove_items(self, items: Iterable[Item]):
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
        if not item.tpl == with_.tpl:
            raise ValueError('Item templates don\'t match')

        with_.upd.StackObjectsCount += item.upd.StackObjectsCount

    @staticmethod
    def transfer(item: Item, with_: Item, count: int):
        """
        :param item: Donor item
        :param with_: Target item
        :param count: Amount to transfer
        """
        item.upd.StackObjectsCount -= count
        with_.upd.StackObjectsCount += count

    @staticmethod
    def fold(item: Item, folded: bool):
        """
        Folds item
        """
        item_template = item_templates_repository.get_template(item)

        foldable = item_template.props.Foldable

        if not foldable:
            raise ValueError('Item is not foldable')

        item.upd.Foldable = ItemUpdFoldable(Folded=folded)

    def take_item(self, template_id: TemplateId, amount: int) -> Tuple[List[Item], List[Item]]:
        """
        Deletes amount of items with given template_id
        :returns Tuple[affected_items, deleted_items]
        """
        items = (item for item in self.items if item.tpl == template_id)
        amount_to_take = amount

        affected_items = []
        deleted_items = []

        for item in items:
            if item.upd.StackObjectsCount is not None:
                to_take = min(amount_to_take, item.upd.StackObjectsCount)
                item.upd.StackObjectsCount -= to_take
                amount_to_take -= to_take

                if item.upd.StackObjectsCount == 0:
                    self.remove_item(item)
                    deleted_items.append(item)
                else:
                    affected_items.append(item)
            else:
                self.remove_item(item)
                deleted_items.append(item)
                amount_to_take -= 1

            if amount_to_take == 0:
                break

        if amount_to_take > 0:
            raise ValueError('Not enough items in inventory')

        return affected_items, deleted_items


class GridInventory(MutableInventory):
    stash_map: StashMap

    @property
    @abc.abstractmethod
    def root_id(self) -> ItemId:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def grid_size(self) -> Tuple[int, int]:
        """
        :return: Tuple[width, height]
        """
        raise NotImplementedError

    def place_item(self, item: Item, *, children_items: List[Item] = None, location: ItemLocation = None):
        if children_items is None:
            children_items = []

        if location is None:
            location = self.stash_map.find_location_for_item(item, auto_fill=True)

        elif not self.stash_map.can_place(item, location):
            raise ValueError('Cannot place item into location since it is taken')

        self.items.append(item)  # TODO: Add children items
        item.location = location
        item.slotId = 'hideout'
        item.parent_id = self.root_id

    def move_item(self, item: Item, location: ItemLocation):
        """
        Moves item to location
        """
        self.stash_map.remove(item)
        item.location = location
        item.slotId = 'hideout'
        item.parent_id = self.root_id
        self.stash_map.add(item)

    @staticmethod
    def can_split(item: Item):
        return item.upd.StackObjectsCount is not None

    def split_item(self, item: Item, count: int) -> Item:
        """
        Splits count from item and returns new item
        :return: New item
        """
        if count == 1:
            self.remove_item(item)
            return item

        if item.upd.StackObjectsCount < count:
            raise ValueError("Can't split from item since stack amount < count")

        item_copy = copy.deepcopy(item)
        item_copy.upd.StackObjectsCount = count
        item_copy.id = generate_item_id()

        del item_copy.slotId
        del item_copy.parent_id
        del item_copy.location

        item.upd.StackObjectsCount -= count
        if item.upd.StackObjectsCount == 0:
            self.remove_item(item)

        return item_copy


class PlayerInventory(GridInventory):
    inventory: InventoryModel

    def __init__(self, profile: 'tarkov.profile.Profile'):
        super().__init__()
        profile_id = profile.profile_id
        self.__path = root_dir.joinpath('resources', 'profiles', profile_id, 'pmc_inventory.json')

    @property
    def grid_size(self) -> Tuple[int, int]:
        stash_item = self.get_item(self.root_id)
        stash_template = item_templates_repository.get_template(stash_item)
        stash_grids = stash_template.props.Grids
        assert stash_grids is not None
        grids_props = stash_grids[0].props
        return grids_props.width, grids_props.height

    @property
    def items(self) -> List[Item]:
        return self.inventory.items

    @property
    def root_id(self):
        return self.inventory.stash

    @property
    def stash_id(self):
        return self.root_id

    @property
    def equipment_id(self) -> str:
        return self.inventory.equipment

    def read(self):
        """
        Reads inventory file from disk
        """
        self.inventory = InventoryModel(**ujson.load(self.__path.open('r', encoding='utf8')))
        self.stash_map = StashMap(inventory=self)

    def write(self):
        """
        Writes inventory file to disk
        """
        ujson.dump(
            self.inventory.dict(exclude_unset=True, exclude_none=True),
            self.__path.open('w', encoding='utf8'),
            indent=4
        )


def merge_extra_size(first: ItemExtraSize, second: ItemExtraSize) -> ItemExtraSize:
    extra_size = copy.deepcopy(first)
    extra_size['left'] = max(first['left'], second['left'])
    extra_size['right'] = max(first['right'], second['right'])
    extra_size['up'] = max(first['up'], second['up'])
    extra_size['down'] = max(first['down'], second['down'])
    return extra_size
