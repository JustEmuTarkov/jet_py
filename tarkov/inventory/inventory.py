from __future__ import annotations

import abc
import copy
import itertools
from typing import Dict, Iterable, List, Optional, TYPE_CHECKING, Tuple, Union

import ujson

from server import logger, root_dir
from server.utils import atomic_write
from tarkov.exceptions import NoSpaceError, NotFoundError
from tarkov.models import Base
from .dict_models import ItemExtraSize
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
    ModMoveLocation,
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
            raise NotFoundError(f"Item with id {item_id} was not found in {self.__class__.__name__}") from error

    def get_item_by_template(self, template_id: TemplateId) -> Item:
        try:
            return next(item for item in self.items if item.tpl == template_id)
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
            if item_template.props.FoldedSlot == stock.slotId:
                item_or_stock_folded = stock.upd.folded() or item.upd.folded()
                item_or_item_foldable = stock_template.props.Foldable or item_template.props.Foldable
                if item_or_item_foldable and item_or_stock_folded:
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


class GridInventoryStashMap:
    class StashMapWarning(Warning):
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
        inventory_root = inventory.get_item(inventory.root_id)

        self.footprints = {}
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

    def remove(self, item: Item, child_items: List[Item]) -> None:
        parent_item = item
        while not self._is_item_in_root(parent_item) and parent_item.parent_id is not None:
            parent_item = self.inventory.get_item(parent_item.parent_id)

        # Recalculate parent item footprint, needed for disassembling
        try:
            del self.footprints[parent_item.id]
        except KeyError:
            pass

        if parent_item != item:
            self.add(parent_item, child_items)
            if self._is_item_in_root(item) and parent_item != item:
                del self.footprints[item.id]

    def add(self, item: Item, child_items: List[Item]) -> None:
        if self._is_item_in_root(item):
            if item.location is None:
                return

            if not isinstance(item.location, ItemInventoryLocation):
                raise ValueError("Item has no location")

            if isinstance(item.location, int):  # ItemAmmoStackPosition
                return

            if not self.can_place(item, child_items, item.location):
                logger.debug(item)
                raise ValueError("Item location is taken")

            if item.id in self.footprints:
                raise ValueError

            self.footprints[item.id] = self._calculate_item_footprint(item, child_items, item.location)

    def can_place(self, item: Item, child_items: List[Item], location: ItemInventoryLocation) -> bool:
        """
        Checks if item can be placed into location
        """
        item_footprint = self._calculate_item_footprint(item, child_items, location)
        if item_footprint.is_out_of_bounds(inventory_width=self.width, inventory_height=self.height):
            raise GridInventoryStashMap.OutOfBoundsError

        for other_footprint in self.footprints.values():
            if item_footprint.overlaps(other_footprint):
                print(item_footprint, other_footprint, sep="\n")
                return False
        return True

    @staticmethod
    def can_place_fast(x: int, y: int, width: int, height: int, stash_map: List[List[bool]]) -> bool:
        for item_x in range(x, x + width):
            for item_y in range(y, y + height):
                # TODO: Possible IndexError here
                if stash_map[item_x][item_y] is True:
                    return False
        return True

    def _construct_map(self) -> List[List[bool]]:
        stash_map: List[List[bool]] = [[False for _ in range(self.height)] for _ in range(self.width)]
        for footprint in self.footprints.values():
            for x in range(footprint.x, footprint.x + footprint.width):
                for y in range(footprint.y, footprint.y + footprint.height):
                    stash_map[x][y] = True
        return stash_map

    def find_location_for_item(
        self,
        item: Item,
        *,
        child_items: List[Item] = None,
    ) -> ItemInventoryLocation:
        """
        Finds location for an item or raises NoSpaceError if there's not space in inventory
        """
        if child_items is None:
            child_items = []
        stash_map = self._construct_map()

        for x, y in self._iter_cells():
            for orientation in ItemOrientationEnum:
                location = ItemInventoryLocation(x=x, y=y, r=orientation.value)
                width, height = self._get_item_size_in_stash(item, child_items, location=location)
                if x + width > self.width or y + height > self.height:
                    continue
                # if self.can_place_fast(x, y, width, height, stash_map):
                #     return location
                if self.can_place_fast(x, y, width, height, stash_map):
                    return location

        raise NoSpaceError("Cannot place item into inventory")

    def debug_print(self) -> None:
        stash_map = self._construct_map()
        lines = []
        for y in range(self.height):
            line = " ".join("■" if stash_map[x][y] else "□" for x in range(self.width))
            lines.append(line)

        print(*lines, sep="\n")


class MutableInventory(ImmutableInventory, metaclass=abc.ABCMeta):
    def remove_item(self, item: Item, remove_children: bool = True) -> None:
        """
        Removes item from inventory
        """
        self.items.remove(item)
        if not remove_children:
            return

        for child in self.iter_item_children_recursively(item):
            self.items.remove(child)

    def remove_items(self, items: Iterable[Item], remove_children: bool = True) -> None:
        for item in items:
            try:
                self.remove_item(item, remove_children=remove_children)
            except ValueError as e:
                raise ValueError(f"Item with id {item.id} is not present in {self.__class__.__name__}") from e

    def add_item(self, item: Item, child_items: List[Item]) -> None:
        """
        Adds item into inventory
        """
        for item_to_add in itertools.chain([item], child_items):
            if item_to_add in self.items:
                raise ValueError(f"Item is already present in {self.__class__.__name__}")
            self.items.append(item_to_add)
            item_to_add.__inventory__ = self

    def add_items(self, items: Iterable[Item]) -> None:
        """
        Adds multiple items into inventory
        """

        self.items.extend(items)
        for item in items:
            item.__inventory__ = self

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
    def transfer(item: Item, with_: Item, count: int) -> None:
        """
        :param item: Donor item
        :param with_: Target item
        :param count: Amount to transfer
        """
        item.upd.StackObjectsCount -= count
        with_.upd.StackObjectsCount += count

        if item.upd.StackObjectsCount < 0:
            raise ValueError("item.upd.StackObjectsCount < 0")

        if item.upd.StackObjectsCount == 0:
            item.get_inventory().remove_item(item)

    @staticmethod
    def fold(item: Item, folded: bool) -> None:
        """
        Folds item
        """
        item_template = item_templates_repository.get_template(item)

        assert isinstance(item_template.props, (WeaponProps, StockProps))
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
            raise ValueError("Not enough items in inventory")

        return affected_items, deleted_items

    @staticmethod
    def can_split(item: Item) -> bool:
        return item.upd.StackObjectsCount > 1


class GridInventory(MutableInventory):
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

    def add_item(self, item: Item, child_items: List[Item]) -> None:
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
        item.slotId = "hideout"
        item.parent_id = self.root_id

        if location is None:
            item.location = self.stash_map.find_location_for_item(item, child_items=child_items)

        elif isinstance(location, ItemInventoryLocation):
            if not self.stash_map.can_place(item, child_items, location):
                raise ValueError("Cannot place item into location since it is taken")

        self.add_item(item, child_items)

    def move_item(
        self,
        item: Item,
        move_location: AnyMoveLocation,
    ) -> None:
        """
        Moves item to location
        """

        item_inventory = item.get_inventory()

        children_items = list(item_inventory.iter_item_children_recursively(item))
        item_inventory.remove_item(item, remove_children=True)

        if isinstance(move_location, InventoryMoveLocation):
            self._move_item(item=item, child_items=children_items, move_location=move_location)
            # self.place_item(item=item, children_items=children_items, location=move_location.location)

        elif isinstance(move_location, CartridgesMoveLocation):
            self.__place_ammo_into_magazine(ammo=item, move_location=move_location)

        elif isinstance(move_location, PatronInWeaponMoveLocation):
            self.__place_ammo_into_weapon(ammo=item, move_location=move_location)

        elif isinstance(move_location, ModMoveLocation):
            self._move_item(item=item, child_items=children_items, move_location=move_location)

        else:
            raise ValueError(f"Unknown item location: {move_location}")

    def _move_item(
        self,
        item: Item,
        child_items: List[Item],
        move_location: Union[InventoryMoveLocation, ModMoveLocation],
    ) -> None:
        if isinstance(move_location, InventoryMoveLocation) and move_location.container == "hideout":
            if not self.stash_map.can_place(item, child_items, move_location.location):
                raise ValueError("Cannot place item into location since it is taken")

        # self.stash_map.add(item, children_items)
        item.slotId = move_location.container
        item.parent_id = move_location.id
        if isinstance(move_location, ModMoveLocation):
            item.location = None
        else:
            item.location = move_location.location

        self.add_item(item, child_items)

    def __place_ammo_into_magazine(self, ammo: Item, move_location: CartridgesMoveLocation) -> Optional[Item]:
        magazine = self.get_item(move_location.id)
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
        ammo.slotId = "cartridges"

        return ammo

    def __place_ammo_into_weapon(
        self,
        ammo: Item,
        move_location: PatronInWeaponMoveLocation,
    ) -> Item:
        weapon = self.get_item(move_location.id)

        ammo.slotId = "patron_in_weapon"
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

            new_item.location = split_location.location
            new_item.parent_id = split_location.id
            new_item.slotId = split_location.container

            self.add_item(new_item, child_items=[])
            return new_item

        if isinstance(split_location, CartridgesMoveLocation):
            magazine = self.get_item(split_location.id)
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
        # TODO: I'm not checking for ModMoveLocation there since i don't know if it might cause any problems

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


class PlayerInventoryStashMap(GridInventoryStashMap):
    inventory: PlayerInventory

    def _is_item_in_root(self, item: Item) -> bool:
        return item.parent_id in {self.inventory.root_id, self.inventory.equipment_id}


class PlayerInventory(GridInventory):
    inventory: InventoryModel

    def __init__(self, profile: "Profile"):
        super().__init__()
        profile_id = profile.profile_id
        self._path = root_dir.joinpath("resources", "profiles", profile_id, "pmc_inventory.json")

    @property
    def grid_size(self) -> Tuple[int, int]:
        stash_item = self.get_item(self.root_id)
        stash_template = item_templates_repository.get_template(stash_item)
        assert isinstance(stash_template.props, CompoundProps)
        stash_grids = stash_template.props.Grids
        grids_props = stash_grids[0].props
        return grids_props.width, grids_props.height

    @property
    def items(self) -> List[Item]:
        return self.inventory.items

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
        """
        Reads inventory file from disk
        """
        self.inventory = InventoryModel(**ujson.load(self._path.open("r", encoding="utf8")))
        for item in self.items:
            item.__inventory__ = self

        self.stash_map = PlayerInventoryStashMap(inventory=self)

    def write(self) -> None:
        atomic_write(self.inventory.json(exclude_none=True, exclude_defaults=True), self._path)


def merge_extra_size(first: ItemExtraSize, second: ItemExtraSize) -> ItemExtraSize:
    extra_size = copy.deepcopy(first)
    extra_size["left"] = max(first["left"], second["left"])
    extra_size["right"] = max(first["right"], second["right"])
    extra_size["up"] = max(first["up"], second["up"])
    extra_size["down"] = max(first["down"], second["down"])
    return extra_size
