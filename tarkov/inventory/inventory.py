from __future__ import annotations

import abc
import itertools
from typing import Dict, Iterable, List, Optional, TYPE_CHECKING, Tuple

from tarkov.exceptions import NoSpaceError, NotFoundError
from tarkov.models import Base
from .helpers import generate_item_id
from .models import (
    AnyItemLocation,
    AnyMoveLocation,
    CartridgesMoveLocation,
    InventoryModel,
    InventoryMoveLocation,
    Item,
    ItemAmmoStackPosition,
    ItemInventoryLocation,
    ItemOrientationEnum,
    ItemUpdFoldable,
    PatronInWeaponMoveLocation,
)
from .prop_models import CompoundProps, MagazineProps, ModProps, StockProps, WeaponProps
from .repositories import item_templates_repository
from .types import ItemId, TemplateId

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile import Profile


class ImmutableInventory(metaclass=abc.ABCMeta):
    """
    Implements inventory_manager access methods like searching for item, getting it's children without mutating state
    """

    @property
    @abc.abstractmethod
    def items(self) -> Dict[ItemId, Item]:
        pass

    def get(self, item_id: ItemId) -> Item:
        """
        Retrieves item from inventory by it's id
        """
        try:
            return self.items[item_id]
        except KeyError as error:
            raise NotFoundError(f"Item with id {item_id} was not found in {self.__class__.__name__}") from error

    def get_by_template(self, template_id: TemplateId) -> Item:
        try:
            return next(item for item in self.items.values() if item.tpl == template_id)
        except StopIteration as error:
            raise NotFoundError from error

    @staticmethod
    def __get_item_size_without_folding(item: Item, child_items: List[Item]) -> Tuple[int, int]:
        item_template = item_templates_repository.get_template(item)
        if not isinstance(item_template.props, (WeaponProps, ModProps)):
            return item_template.props.Width, item_template.props.Height

        size_left: int = 0
        size_right: int = 0
        size_up: int = 0
        size_down: int = 0

        width = item_template.props.Width
        height = item_template.props.Height

        for child in child_items:
            child_template = item_templates_repository.get_template(child)
            if child_template.props.ExtraSizeForceAdd:
                width += child_template.props.ExtraSizeLeft + child_template.props.ExtraSizeRight
                height += child_template.props.ExtraSizeUp + child_template.props.ExtraSizeDown
            else:
                size_left = max(size_left, child_template.props.ExtraSizeLeft)
                size_right = max(size_right, child_template.props.ExtraSizeRight)
                size_up = max(size_up, child_template.props.ExtraSizeUp)
                size_down = max(size_down, child_template.props.ExtraSizeDown)

        width += size_left + size_right
        height += size_up + size_down

        return width, height

    @staticmethod
    def get_item_size(  # noqa: C901 - Guess there's nothing i can do about this function complexity
        item: Item, child_items: List[Item] = None
    ) -> Tuple[int, int]:
        """
        Return size of the item according to it's attachments, etc.

        :return: Tuple[width, height]
        """
        item_template = item_templates_repository.get_template(item)
        child_items = child_items or []
        width, height = ImmutableInventory.__get_item_size_without_folding(item, child_items)

        if isinstance(item_template.props, StockProps) and item.upd.folded():
            width -= item_template.props.SizeReduceRight

        if not isinstance(item_template.props, WeaponProps):
            return width, height

        if item_template.props.Foldable and item_template.props.FoldedSlot == "":
            if item.upd.folded():
                width -= item_template.props.SizeReduceRight
            return width, height

        for stock in child_items:
            stock_template = item_templates_repository.get_template(stock)
            if not isinstance(stock_template.props, StockProps):
                continue
            if item_template.props.FoldedSlot == stock.slot_id:
                item_or_stock_folded = stock.upd.folded() or item.upd.folded()
                item_or_stock_foldable = stock_template.props.Foldable or item_template.props.Foldable
                if item_or_stock_foldable and item_or_stock_folded:
                    width -= max(
                        stock_template.props.SizeReduceRight,
                        stock_template.props.ExtraSizeRight,
                        1,
                    )
                    break

            if item_template.props.FoldedSlot == "":
                if stock_template.props.Foldable and stock.upd.folded():
                    width -= stock_template.props.SizeReduceRight

        if item_template.props.Foldable and item.upd.folded():
            return width, height

        return max(item_template.props.Width, width), max(item_template.props.Height, height)

    def iter_item_children(self, item: Item) -> Iterable[Item]:
        """
        Iterates over item's children
        """
        for children in self.items.values():
            if children.parent_id == item.id:
                yield children

    def iter_item_children_recursively(self, item: Item) -> Iterable[Item]:
        """
        Iterates over item's children recursively
        """
        stack = list(self.iter_item_children(item))

        while stack:
            child: Item = stack.pop()
            stack.extend(self.iter_item_children(child))
            yield child


class MutableInventory(ImmutableInventory, metaclass=abc.ABCMeta):
    def remove_item(self, item: Item, remove_children: bool = True) -> None:
        """
        Removes item from inventory
        """
        del self.items[item.id]
        if not remove_children:
            return

        children = list(self.iter_item_children_recursively(item))
        for child in children:
            del self.items[child.id]

    def remove_items(self, items: Iterable[Item], remove_children: bool = True) -> None:
        for item in items:
            self.remove_item(item, remove_children=remove_children)

    def add_item(self, item: Item, child_items: List[Item] = None) -> None:
        """
        Adds item into inventory
        """
        child_items = child_items or []

        for item_to_add in itertools.chain([item], child_items):
            if item_to_add.id in self.items:
                raise ValueError(f"Item is already present in {self.__class__.__name__}")

            self.items[item_to_add.id] = item_to_add
            item_to_add.__inventory__ = self

    @staticmethod
    def merge(item: Item, with_: Item) -> None:
        """
        Merges item with target item, item template ids should be same

        :param item: Item that will be merged and removed
        :param with_: Target item
        """
        if not item.tpl == with_.tpl:
            raise ValueError("Item templates don't match")

        item.get_inventory().remove_item(item)
        with_.upd.StackObjectsCount += item.upd.StackObjectsCount

    @staticmethod
    def transfer(item: Item, to: Item, count: int) -> None:
        """
        :param item: Donor item
        :param to: Target item
        :param count: Amount to transfer
        """
        item.upd.StackObjectsCount -= count
        to.upd.StackObjectsCount += count

        if item.upd.StackObjectsCount < 0:
            raise ValueError("item.upd.StackObjectsCount < 0")

        if item.upd.StackObjectsCount == 0:
            item.get_inventory().remove_item(item)

    def fold(self, item: Item, folded: bool) -> None:
        """
        Folds item
        """
        item_template = item_templates_repository.get_template(item)

        assert isinstance(item_template.props, (WeaponProps, StockProps))
        children = list(self.iter_item_children_recursively(item))
        # Remove and add item to update stash map
        self.remove_item(item)
        item.upd.Foldable = ItemUpdFoldable(Folded=folded)
        self.add_item(item, children)

    def take_item(self, template_id: TemplateId, amount: int) -> Tuple[List[Item], List[Item]]:
        """
        Deletes amount of items with given template_id
        :returns Tuple[affected_items, deleted_items]
        """
        items = (item for item in self.items.values() if item.tpl == template_id)
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
            raise ValueError("Not enough items in inventory")

        return affected_items, deleted_items

    @staticmethod
    def can_split(item: Item) -> bool:
        return item.upd.StackObjectsCount > 1


class StashMapItemFootprint(Base):
    """Basically a rectangle"""

    x: int
    y: int
    width: int
    height: int

    @property
    def x_high(self) -> int:
        return self.x + self.width

    @property
    def y_high(self) -> int:
        return self.y + self.height

    def overlaps(self, other: "StashMapItemFootprint") -> bool:
        if self == other:
            return True

        if self.y >= other.y_high or self.y_high <= other.y:
            return False
        if self.x >= other.x_high or self.x_high <= other.x:
            return False

        return True

    def is_out_of_bounds(self, inventory_width: int, inventory_height: int) -> bool:
        if self.x < 0 or inventory_width < self.x_high:
            return True

        if self.y < 0 or inventory_height < self.y_high:
            return True

        return False

    def iter_cells(self) -> Iterable[Tuple[int, int]]:
        for x in range(self.x, self.x_high):
            for y in range(self.y, self.y_high):
                yield x, y


class GridInventoryStashMap:
    class InvalidCellStateError(Exception):
        pass

    class OutOfBoundsError(Exception):
        pass

    inventory: GridInventory
    width: int
    height: int

    footprints: Dict[ItemId, StashMapItemFootprint]

    def __init__(self, inventory: GridInventory):
        self.inventory = inventory
        self.width, self.height = inventory.grid_size
        inventory_root = inventory.get(inventory.root_id)

        self.map: List[List[bool]] = [[False for y in range(self.height)] for x in range(self.width)]
        for item in inventory.iter_item_children(inventory_root):
            if self._is_item_in_root(item):
                children_items = list(self.inventory.iter_item_children_recursively(item=item))
                self.add(item, children_items)

    def _get_item_size_in_stash(
        self, item: Item, children_items: List[Item], location: ItemInventoryLocation
    ) -> Tuple[int, int]:
        """
        Returns footprint (width, height) that item takes in inventory, takes rotation into account
        """
        width, height = self.inventory.get_item_size(item=item, child_items=children_items)
        if location.r == ItemOrientationEnum.Vertical.value:
            width, height = height, width

        return width, height

    def _calculate_item_footprint(
        self, item: Item, child_items: List[Item], location: ItemInventoryLocation
    ) -> StashMapItemFootprint:
        width, height = self._get_item_size_in_stash(item, child_items, location)
        return StashMapItemFootprint(
            x=location.x,
            y=location.y,
            width=width,
            height=height,
        )

    def _iter_cells(self) -> Iterable[Tuple[int, int]]:
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def _is_item_in_root(self, item: Item) -> bool:
        """
        Determines if item is in inventory root
        """
        return isinstance(item.location, ItemInventoryLocation) and item.parent_id == self.inventory.root_id

    def get(self, x: int, y: int) -> bool:
        if not 0 <= x < self.width:
            raise IndexError
        if not 0 <= y < self.height:
            raise IndexError

        return self.map[x][y]

    def set(self, x: int, y: int, state: bool) -> None:
        if self.map[x][y] == state:
            raise self.InvalidCellStateError(f"Cell {x} {y} already has {state} state")
        self.map[x][y] = state

    def remove(self, item: Item, child_items: List[Item]) -> None:
        parent_item = item
        while not self._is_item_in_root(parent_item) and parent_item.parent_id is not None:
            parent_item = self.inventory.get(parent_item.parent_id)

        # Recalculate parent item footprint, needed for disassembling
        assert isinstance(item.location, ItemInventoryLocation)
        footprint = self._calculate_item_footprint(item, child_items, location=item.location)
        for x, y in footprint.iter_cells():
            self.set(x, y, False)

    def add(self, item: Item, child_items: List[Item]) -> None:
        if not self._is_item_in_root(item):
            return
        assert isinstance(item.location, ItemInventoryLocation)
        if not self.can_place(item, child_items, item.location):
            raise GridInventoryStashMap.OutOfBoundsError

        footprint = self._calculate_item_footprint(item, child_items, item.location)
        for x, y in footprint.iter_cells():
            self.set(x, y, True)

    def can_place(self, item: Item, child_items: List[Item], location: ItemInventoryLocation) -> bool:
        """
        Checks if item can be placed into location
        """
        item_footprint = self._calculate_item_footprint(item, child_items, location)
        for x, y in item_footprint.iter_cells():
            try:
                if self.get(x, y):
                    return False
            except IndexError:
                return False
        return True

    def find_location_for_item(
        self,
        item: Item,
        *,
        child_items: List[Item] = None,
    ) -> ItemInventoryLocation:
        """
        Finds location for an item or raises NoSpaceError if there's not space in inventory
        """
        child_items = child_items or []
        item_width, item_height = self.inventory.get_item_size(item, child_items)
        for x, y in self._iter_cells():
            for orientation in ItemOrientationEnum:
                location = ItemInventoryLocation(x=x, y=y, r=orientation.value)
                width, height = item_width, item_height
                if location.r == ItemOrientationEnum.Vertical.value:
                    width, height = height, width

                if x + width > self.width or y + height > self.height:
                    continue

                if self.can_place(item, child_items, location):
                    return location

        raise NoSpaceError("Cannot place item into inventory")


class GridInventory(MutableInventory):
    class InvalidItemLocation(Exception):
        pass

    stash_map: GridInventoryStashMap

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

    def remove_item(self, item: Item, remove_children: bool = True) -> None:
        self.stash_map.remove(item, list(self.iter_item_children_recursively(item)))
        super().remove_item(item, remove_children=remove_children)

    def add_item(self, item: Item, child_items: List[Item] = None) -> None:
        child_items = child_items or []
        self.stash_map.add(item, child_items)
        super().add_item(item=item, child_items=child_items)

    def place_item(
        self,
        item: Item,
        *,
        child_items: List[Item] = None,
        location: AnyItemLocation = None,
    ) -> None:
        if child_items is None:
            child_items = []
        #  This is kinda tricky but item given to StashMap should have
        #  slotId and parent_id otherwise it won't be considered as being in inventory
        item.location = location
        item.slot_id = "hideout"
        item.parent_id = self.root_id

        if item.location is None:
            item.location = self.stash_map.find_location_for_item(item, child_items=child_items)

        elif isinstance(location, ItemInventoryLocation):
            if not self.stash_map.can_place(item, child_items, location):
                raise self.InvalidItemLocation(
                    "Cannot place item into location since it is taken and/or out of bounds"
                )

        self.add_item(item, child_items)

    def move_item(
        self,
        item: Item,
        move_location: AnyMoveLocation,
    ) -> None:
        """
        Moves item to location
        """
        try:
            item_inventory = item.get_inventory()

            children_items = list(item_inventory.iter_item_children_recursively(item))
            item_inventory.remove_item(item, remove_children=True)
        except ValueError:
            children_items = []

        if isinstance(move_location, InventoryMoveLocation):
            self._move_item(item=item, child_items=children_items, move_location=move_location)
            # self.place_item(item=item, children_items=children_items, location=move_location.location)

        elif isinstance(move_location, CartridgesMoveLocation):
            self.__place_ammo_into_magazine(ammo=item, move_location=move_location)

        elif isinstance(move_location, PatronInWeaponMoveLocation):
            self.__place_ammo_into_weapon(ammo=item, move_location=move_location)

        else:
            raise ValueError(f"Unknown item location: {move_location}")

    def _move_item(
        self,
        item: Item,
        child_items: List[Item],
        move_location: InventoryMoveLocation,
    ) -> None:
        if move_location.id == self.root_id and move_location.location is not None:
            if not self.stash_map.can_place(item, child_items, move_location.location):
                raise ValueError("Cannot place item into location since it is taken")

        item.slot_id = move_location.container
        item.parent_id = move_location.id
        if move_location.location:
            item.location = move_location.location

        self.add_item(item, child_items)

    def __place_ammo_into_magazine(self, ammo: Item, move_location: CartridgesMoveLocation) -> Optional[Item]:
        magazine = self.get(move_location.id)
        ammo_inside_mag = list(self.iter_item_children(magazine))

        self.add_item(item=ammo, child_items=[])

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
        ammo.slot_id = "cartridges"

        return ammo

    def __place_ammo_into_weapon(
        self,
        ammo: Item,
        move_location: PatronInWeaponMoveLocation,
    ) -> Item:
        weapon = self.get(move_location.id)

        ammo.slot_id = "patron_in_weapon"
        ammo.location = None
        ammo.parent_id = weapon.id

        self.add_item(ammo, child_items=[])
        return ammo

    def split_item(self, item: Item, split_location: AnyMoveLocation, count: int) -> Optional[Item]:
        """
        Splits count from item and returns new item
        :return: New item
        """

        if isinstance(split_location, InventoryMoveLocation):
            new_item = item.copy(deep=True)
            new_item.id = generate_item_id()
            new_item.upd.StackObjectsCount = count
            item.upd.StackObjectsCount -= count

            self.move_item(item, split_location)
            return new_item

        if isinstance(split_location, CartridgesMoveLocation):
            magazine = self.get(split_location.id)
            ammo = item

            magazine_template = item_templates_repository.get_template(magazine)
            assert isinstance(magazine_template.props, MagazineProps)

            magazine_capacity: int = magazine_template.props.Cartridges[0].max_count
            bullet_stacks_inside_mag = list(self.iter_item_children(magazine))
            ammo_to_full = magazine_capacity - sum(
                stack.upd.StackObjectsCount for stack in bullet_stacks_inside_mag
            )

            # Remove ammo from inventory if stack fully fits into magazine
            if ammo.upd.StackObjectsCount <= ammo_to_full:
                ammo_inventory = ammo.get_inventory()
                ammo_inventory.remove_item(ammo)
                return self.__place_ammo_into_magazine(ammo=ammo, move_location=split_location)

            # Else if stack is too big to fit into magazine copy ammo and assign it new id and proper stack count
            splitted_ammo = self.simple_split_item(ammo, count)

            self.__place_ammo_into_magazine(
                ammo=splitted_ammo,
                move_location=split_location,
            )

            return splitted_ammo

        if isinstance(split_location, PatronInWeaponMoveLocation):
            ammo = self.simple_split_item(item=item, count=1)
            return self.__place_ammo_into_weapon(ammo=ammo, move_location=split_location)

        raise ValueError(f"Unknown split location: {split_location}")

    @staticmethod
    def simple_split_item(item: Item, count: int) -> Item:

        if item.upd.StackObjectsCount < count:
            raise ValueError(
                f"Can not split {count} from item[{item.id}] since it only has {item.upd.StackObjectsCount} in stack"
            )

        item_copy = item.copy(deep=True)
        item_copy.id = generate_item_id()
        item_copy.upd.StackObjectsCount = count
        item.upd.StackObjectsCount -= count

        if item.upd.StackObjectsCount == 0:
            try:
                donor_inventory = item.get_inventory()
                donor_inventory.remove_item(item)
            except ValueError:
                pass

        item_copy.location = None

        return item_copy

    @staticmethod
    def split_into_stacks(item: Item) -> List[Item]:
        item_template = item_templates_repository.get_template(item)
        count = item.upd.StackObjectsCount

        items = []
        while count > 0:
            item_copy = item.copy(deep=True)
            item_copy.id = generate_item_id()
            items.append(item_copy)
            item_copy.upd.StackObjectsCount = min(item_template.props.StackMaxSize, count)
            item_copy.location = None
            count -= item_copy.upd.StackObjectsCount

        return items


class PlayerInventoryStashMap(GridInventoryStashMap):
    pass


class PlayerInventory(GridInventory):
    inventory: InventoryModel

    def __init__(self, profile: "Profile"):
        super().__init__()
        self.profile: "Profile" = profile
        self.inventory = profile.pmc.Inventory

        self.__items: Dict[ItemId, Item] = {}

    @property
    def grid_size(self) -> Tuple[int, int]:
        stash_item = self.get(self.root_id)
        stash_template = item_templates_repository.get_template(stash_item)
        assert isinstance(stash_template.props, CompoundProps)
        stash_grids = stash_template.props.Grids
        grids_props = stash_grids[0].props
        return grids_props.width, grids_props.height

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self.__items

    @property
    def root_id(self) -> ItemId:
        return self.inventory.stash

    @property
    def stash_id(self) -> ItemId:
        return self.root_id

    @property
    def equipment_id(self) -> str:
        return self.inventory.equipment

    def read(self) -> None:
        for item in self.inventory.items:
            item.__inventory__ = self
            self.__items[item.id] = item
        self.stash_map = PlayerInventoryStashMap(inventory=self)

    def write(self) -> None:
        self.inventory.items = list(self.items.values())
