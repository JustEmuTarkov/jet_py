from __future__ import annotations

import random
from typing import Dict, List, TYPE_CHECKING, Tuple

from dependency_injector.wiring import Provide, inject

from server.container import AppContainer
from tarkov.exceptions import NoSpaceError
from tarkov.inventory.inventory import (
    GridInventory,
    GridInventoryStashMap,
    MutableInventory,
)
from tarkov.inventory.models import (
    AnyItemLocation,
    Item,
    ItemInventoryLocation,
    ItemOrientationEnum,
    ItemTemplate,
)
from tarkov.inventory.prop_models import CompoundProps, Grid
from tarkov.inventory.repositories import ItemTemplatesRepository

if TYPE_CHECKING:
    from tarkov.inventory.types import ItemId


class SimpleInventory(MutableInventory):
    def __init__(self, items: List[Item]):
        super().__init__()
        self.__items: Dict[ItemId, Item] = {i.id: i for i in items}

        for item in self.__items.values():
            item.__inventory__ = self

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self.__items


class MultiGridSubInventory(GridInventory):
    def __init__(self, root_id: ItemId, grid: Grid):
        super().__init__()
        self._root_id = root_id
        self._slot_id = grid.name
        self._grid = grid
        self._items: Dict[ItemId, Item] = {}

        self.stash_map = GridInventoryStashMap(self)

    @property
    def root_id(self) -> ItemId:
        return self._root_id

    @property
    def grid_size(self) -> Tuple[int, int]:
        return self._grid.props.width, self._grid.props.height

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self._items

    def place_item(
        self,
        item: Item,
        *,
        child_items: List[Item] = None,
        location: AnyItemLocation = None,
    ) -> None:
        super().place_item(item, child_items=child_items, location=location)
        item.slot_id = self._slot_id


class MultiGridContainer:
    """
    Class representing container with multiple grids, like pockets or tactical rigs.
    """

    def __init__(self, item_template: ItemTemplate, root_id: ItemId, slot_id: str):
        if not isinstance(item_template.props, CompoundProps):
            raise ValueError("Props of item_template should be of type CompoundProps")

        self.root_id = root_id
        self.slot_id = slot_id
        self.template = item_template
        self.inventories: List[MultiGridSubInventory] = [
            MultiGridSubInventory(root_id, grid) for grid in item_template.props.Grids
        ]

    @classmethod
    @inject
    def from_item(
        cls,
        item: Item,
        slot_id: str,
        item_templates_repository: ItemTemplatesRepository = Provide[AppContainer.repos.templates],
    ) -> MultiGridContainer:
        return cls(item_templates_repository.get_template(item), item.id, slot_id)

    @property
    def size(self) -> int:
        assert isinstance(self.template.props, CompoundProps)
        return sum(grid.props.height * grid.props.width for grid in self.template.props.Grids)

    def place_randomly(self, item: Item, child_items: List[Item] = None) -> None:
        """
        Places item into random location

        :param item: Item to place
        :param child_items: Item's children
        :raises NoSpaceError: If there's no place for item in any of sub inventories
        """
        child_items = child_items or []

        # Check for every possible location combination in each sub inventory
        for inventory in random.sample(self.inventories, k=len(self.inventories)):
            # Checks each cell in random order
            cells = list(inventory.stash_map.iter_cells())
            for x, y in random.sample(cells, k=len(cells)):
                for orientation in ItemOrientationEnum:
                    location = ItemInventoryLocation(x=x, y=y, r=orientation.value)
                    if inventory.stash_map.can_place(item, child_items, location):
                        inventory.place_item(item, child_items=child_items, location=location)
                        return
        raise NoSpaceError
