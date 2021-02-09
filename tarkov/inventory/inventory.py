from __future__ import annotations

import abc
import copy
from typing import Iterable, List, Optional, Tuple, Union, cast

import ujson

import tarkov.profile
from server import root_dir
from tarkov.exceptions import NoSpaceError, NotFoundError
from .dict_models import ItemExtraSize
from .helpers import generate_item_id
from .models import (AnyItemLocation, AnyMoveLocation, CartridgesMoveLocation, InventoryModel, InventoryMoveLocation,
                     Item, ItemAmmoStackPosition, ItemId, ItemInventoryLocation, ItemOrientationEnum, ItemUpdFoldable,
                     ModMoveLocation, PatronInWeaponMoveLocation, TemplateId, )
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
            raise NotFoundError(f'Item with id {item_id} was not found in {self.__class__.__name__}') from error

    def get_item_by_template(self, template_id: TemplateId) -> Item:
        try:
            return next(item for item in self.items if item.tpl == template_id)
        except StopIteration as error:
            raise NotFoundError from error

    def get_item_size(self, item: Item, children_items: List[Item] = None) -> Tuple[int, int]:
        """
        Return size of the item according to it's attachments, etc.

        :return: Tuple[width, height]
        """
        children_items = [] if children_items is None else children_items

        template = item_templates_repository.get_template(item)
        if template.props.MergesWithChildren is False:
            return template.props.Width, template.props.Height

        extra_size: ItemExtraSize = {
            'left': 0,
            'right': 0,
            'up': 0,
            'down': 0,
        }

        for child in children_items:
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
    class StashMapWarning(Warning):
        pass

    inventory: GridInventory
    width: int
    height: int
    map: List[List[bool]]

    def __init__(self, inventory: GridInventory):
        self.inventory = inventory
        self.width, self.height = inventory.grid_size
        self.map = [[False for _ in range(self.height)] for _ in range(self.width)]
        inventory_root = inventory.get_item(inventory.root_id)

        for item in (i for i in inventory.iter_item_children(inventory_root)):

            children_items = list(self.inventory.iter_item_children_recursively(item=item))
            self.add(item, children_items)

    def iter_cells(self) -> Iterable[Tuple[int, int]]:
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def get_item_size_in_stash(
            self,
            item: Item,
            children_items: List[Item],
            location: ItemInventoryLocation
    ) -> Tuple[int, int]:
        """
        Returns footprint (width, height) that item takes in inventory, takes rotation into account
        """
        width, height = self.inventory.get_item_size(item=item, children_items=children_items)
        if location.r == ItemOrientationEnum.Vertical.value:
            width, height = height, width

        return width, height

    def _fill(
            self,
            item: Item,
            children_items: List[Item],
            item_location: ItemInventoryLocation,
            with_: bool
    ) -> None:
        """
        Fills item footprint with flag with_
        """
        children_items = [] if children_items is None else children_items
        width, height = self.get_item_size_in_stash(item, children_items, item_location)

        x, y = item_location.x, item_location.y
        for x_ in range(x, x + width):
            for y_ in range(y, y + height):
                if self.map[x_][y_] == with_:
                    raise StashMap.StashMapWarning(f'Cell [x={x_}, y={y_}] already has state {with_}')
                self.map[x_][y_] = with_

    def remove(self, item: Item, children_items: List[Item]) -> None:
        if self.is_item_in_root(item):
            # Using cast because item.location should be of type
            # ItemInventoryLocation since it's checked in __is_item_in_root
            self._fill(item, children_items, cast(ItemInventoryLocation, item.location), False)

    def add(self, item: Item, children_items: List[Item]) -> None:
        if self.is_item_in_root(item):
            self._fill(item, children_items, cast(ItemInventoryLocation, item.location), True)

    @staticmethod
    def is_item_in_root(item: Item) -> bool:
        """
        Determines if item is in inventory root
        """
        return isinstance(item.location, ItemInventoryLocation) and item.slotId == 'hideout'

    def can_place(self, item: Item, children_items: List[Item], location: ItemInventoryLocation) -> bool:
        """
        Checks if item can be placed into location
        """
        x, y = location.x, location.y
        width, height = self.get_item_size_in_stash(item, children_items, location)

        for x_ in range(x, x + width):
            for y_ in range(y, y + height):
                try:
                    if self.map[x_][y_]:
                        return False
                except IndexError:
                    return False
        return True

    def find_location_for_item(
            self,
            item: Item,
            *,
            children_items: List[Item] = None,
            auto_fill=False,
    ) -> ItemInventoryLocation:
        """
        Finds location for an item or raises NoSpaceError if there's not space in inventory
        """
        if children_items is None:
            children_items = []

        for x, y in self.iter_cells():
            for orientation in ItemOrientationEnum:
                location = ItemInventoryLocation(x=x, y=y, r=orientation.value)
                if self.can_place(item=item, children_items=children_items, location=location):
                    if auto_fill:
                        self._fill(item, children_items, location, True)
                    return location

        raise NoSpaceError('Cannot place item into inventory')


class MutableInventory(ImmutableInventory, metaclass=abc.ABCMeta):
    def remove_item(self, item: Item, remove_children=True) -> None:
        """
        Removes item from inventory
        """
        self.items.remove(item)
        if not remove_children:
            return

        for child in self.iter_item_children_recursively(item):
            self.items.remove(child)

    def remove_items(self, items: Iterable[Item], remove_children=True):
        for item in items:
            try:
                self.remove_item(item, remove_children=remove_children)
            except ValueError as e:
                raise ValueError(f'Item with id {item.id} is not present in {self.__class__.__name__}') from e

    def add_item(self, item: Item):
        """
        Adds item into inventory
        """
        if item in self.items:
            raise ValueError(f'Item is already present in {self.__class__.__name__}')
        self.items.append(item)
        item.__inventory__ = self

    def add_items(self, items: Iterable[Item]) -> None:
        """
        Adds multiple items into inventory
        """

        self.items.extend(items)
        for item in items:
            item.__inventory__ = self

    def merge(self, item: Item, with_: Item) -> None:
        """
        Merges item with target item, item template ids should be same

        :param item: Item that will be merged and removed
        :param with_: Target item
        """
        if not item.tpl == with_.tpl:
            raise ValueError('Item templates don\'t match')

        item.get_inventory().remove_item(item)

        with_.upd.StackObjectsCount += item.upd.StackObjectsCount

    @staticmethod
    def transfer(item: Item, with_: Item, count: int) -> None:
        """
        :param item: Donor item
        :param with_: Target item
        :param count: Amount to transfer
        """
        item.upd.StackObjectsCount -= count
        with_.upd.StackObjectsCount += count

        if item.upd.StackObjectsCount < 0:
            raise ValueError('item.upd.StackObjectsCount < 0')

        if item.upd.StackObjectsCount == 0:
            item.get_inventory().remove_item(item)

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
            to_take = min(amount_to_take, item.upd.StackObjectsCount)
            item.upd.StackObjectsCount -= to_take
            amount_to_take -= to_take

            if item.upd.StackObjectsCount == 0:
                self.remove_item(item)
                deleted_items.append(item)
            else:
                affected_items.append(item)

            if amount_to_take == 0:
                break

        if amount_to_take > 0:
            raise ValueError('Not enough items in inventory')

        return affected_items, deleted_items

    @staticmethod
    def can_split(item: Item):
        return item.upd.StackObjectsCount > 1


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

    def remove_item(self, item: Item, remove_children=True):
        self.stash_map.remove(item, list(self.iter_item_children_recursively(item)))
        super().remove_item(item, remove_children=remove_children)

    def place_item(self, item: Item, *, children_items: List[Item] = None, location: AnyItemLocation = None):
        if children_items is None:
            children_items = []

        if location is None:
            location = self.stash_map.find_location_for_item(item, children_items=children_items, auto_fill=True)

        elif isinstance(location, ItemInventoryLocation):
            if not self.stash_map.can_place(item, children_items, location):
                raise ValueError('Cannot place item into location since it is taken')

        # self.stash_map.add(item, children_items)
        self.add_item(item)
        self.add_items(children_items)
        item.location = location
        item.slotId = 'hideout'
        item.parent_id = self.root_id

    def move_item(
            self,
            item: Item,
            move_location: AnyMoveLocation,
    ):
        """
        Moves item to location
        """

        item_inventory = item.get_inventory()

        children_items = list(item_inventory.iter_item_children_recursively(item))
        item_inventory.remove_item(item, remove_children=True)

        if isinstance(move_location, InventoryMoveLocation):
            self._move_item(item=item, children_items=children_items, move_location=move_location)
            # self.place_item(item=item, children_items=children_items, location=move_location.location)

        elif isinstance(move_location, CartridgesMoveLocation):
            self.__place_ammo_into_magazine(ammo=item, move_location=move_location)

        elif isinstance(move_location, PatronInWeaponMoveLocation):
            self.__place_ammo_into_weapon(ammo=item, move_location=move_location)

        elif isinstance(move_location, ModMoveLocation):
            self._move_item(item=item, children_items=children_items, move_location=move_location)

        else:
            raise ValueError(f'Unknown item location: {move_location}')

    def _move_item(
            self,
            item: Item,
            children_items: List[Item],
            move_location: Union[InventoryMoveLocation, ModMoveLocation]
    ) -> None:
        if isinstance(move_location, InventoryMoveLocation) and move_location.container == 'hideout':
            if not self.stash_map.can_place(item, children_items, move_location.location):
                raise ValueError('Cannot place item into location since it is taken')

        # self.stash_map.add(item, children_items)
        self.add_item(item)
        self.add_items(children_items)
        item.slotId = move_location.container
        item.parent_id = move_location.id
        if isinstance(move_location, ModMoveLocation):
            item.location = None
        else:
            item.location = move_location.location

    def __place_ammo_into_magazine(
            self,
            ammo: Item,
            move_location: CartridgesMoveLocation
    ) -> Optional[Item]:
        magazine = self.get_item(move_location.id)
        ammo_inside_mag = list(self.iter_item_children(magazine))

        self.add_item(item=ammo)

        if ammo_inside_mag:
            def ammo_stack_position(item: Item) -> int:
                if isinstance(item.location, int):
                    return item.location
                return 0

            last_bullet_stack: Item = max(ammo_inside_mag, key=ammo_stack_position)

            # Stack ammo stack with last if possible and remove ammo
            if last_bullet_stack.tpl == ammo.tpl:
                last_bullet_stack.upd.StackObjectsCount += ammo.upd.StackObjectsCount
                self.remove_item(ammo)
                return None

            ammo.location = ItemAmmoStackPosition(len(ammo_inside_mag))

        # Add new ammo stack to magazine
        else:
            ammo.location = ItemAmmoStackPosition(0)

        ammo.parent_id = magazine.id
        ammo.slotId = 'cartridges'

        return ammo

    def __place_ammo_into_weapon(
            self,
            ammo: Item,
            move_location: PatronInWeaponMoveLocation,
    ) -> Item:
        weapon = self.get_item(move_location.id)

        ammo.slotId = 'patron_in_weapon'
        ammo.location = None
        ammo.parent_id = weapon.id

        self.add_item(ammo)
        return ammo

    def split_item(
            self,
            item: Item,
            split_location: AnyMoveLocation,
            count: int
    ) -> Optional[Item]:
        """
        Splits count from item and returns new item
        :return: New item
        """

        if isinstance(split_location, InventoryMoveLocation):
            new_item = item.copy(deep=True)
            new_item.id = generate_item_id()
            new_item.upd.StackObjectsCount = count
            item.upd.StackObjectsCount -= count

            new_item.location = split_location.location
            new_item.parent_id = split_location.id
            new_item.slotId = split_location.container

            self.add_item(new_item)
            return new_item

        elif isinstance(split_location, CartridgesMoveLocation):
            magazine = self.get_item(split_location.id)
            ammo = item

            magazine_template = item_templates_repository.get_template(magazine)
            assert magazine_template.props.Cartridges is not None

            magazine_capacity: int = magazine_template.props.Cartridges[0].max_count
            bullet_stacks_inside_mag = list(self.iter_item_children(magazine))
            ammo_to_full = magazine_capacity - sum(stack.upd.StackObjectsCount for stack in bullet_stacks_inside_mag)

            # Remove ammo from inventory if stack fully fits into magazine
            if ammo.upd.StackObjectsCount <= ammo_to_full:
                ammo_inventory = ammo.get_inventory()
                ammo_inventory.remove_item(ammo)
                return self.__place_ammo_into_magazine(ammo=ammo, move_location=split_location)

            # Else if stack is too big to fit into magazine copy ammo and assign it new id and proper stack count
            else:
                splitted_ammo = self.simple_split_item(ammo, count)

            self.__place_ammo_into_magazine(
                ammo=splitted_ammo,
                move_location=split_location,
            )

            return splitted_ammo

        elif isinstance(split_location, PatronInWeaponMoveLocation):
            ammo = self.simple_split_item(item=item, count=1)
            return self.__place_ammo_into_weapon(ammo=ammo, move_location=split_location)
        # TODO: I'm not checking for ModMoveLocation there since i don't know if it might cause any problems
        else:
            raise ValueError(f'Unknown split location: {split_location}')

    def simple_split_item(self, item: Item, count: int) -> Item:
        donor_inventory = item.get_inventory()

        if item.upd.StackObjectsCount < count:
            raise ValueError(
                f'Can not split {count} from item[{item.id}] since it only has {item.upd.StackObjectsCount} in stack')

        item_copy = item.copy(deep=True)
        item_copy.id = generate_item_id()
        item_copy.upd.StackObjectsCount = count
        item.upd.StackObjectsCount -= count

        if item.upd.StackObjectsCount == 0:
            donor_inventory.remove_item(item)

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
        for item in self.items:
            item.__inventory__ = self

        self.stash_map = StashMap(inventory=self)

    def write(self):
        """
        Writes inventory file to disk
        """
        ujson.dump(
            self.inventory.dict(exclude_defaults=True, exclude_none=False, exclude_unset=False),
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
