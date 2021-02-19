from typing import List, Tuple

import pytest

from tarkov.exceptions import NoSpaceError
from tarkov.inventory import (
    GridInventoryStashMap,
    PlayerInventory,
    item_templates_repository,
)
from tarkov.inventory.models import Item, ItemInventoryLocation, ItemOrientationEnum
from tarkov.inventory.types import TemplateId


def test_adds_items(inventory: PlayerInventory, random_items: List[Item]) -> None:
    for item in random_items:
        inventory.add_item(item, [])

    assert all(item in inventory.inventory.items for item in random_items)


# EOD stash should be 10x68
@pytest.mark.parametrize(
    "test_coords",
    [(-1, 0), (0, -1), (0, 67), (8, 0), (40, 0), (-2, -12), (9, 0), (10, 0)],
)
def test_should_not_be_able_to_place_items_out_of_bounds(
    inventory: PlayerInventory, test_coords: Tuple[int, int]
) -> None:
    magbox = item_templates_repository.create_item(
        item_templates_repository.get_template(TemplateId("5c127c4486f7745625356c13"))
    )[0]
    x, y = test_coords
    with pytest.raises(GridInventoryStashMap.OutOfBoundsError):
        inventory.place_item(
            item=magbox,
            location=ItemInventoryLocation(x=x, y=y, r=ItemOrientationEnum.Horizontal.value),
        )


def test_finds_locations(inventory) -> None:  # type: ignore
    # Should be able to completely fill EOD stash with PSUs
    width, height = inventory.grid_size
    psu_template = item_templates_repository.get_template(TemplateId("57347c2e24597744902c94a1"))
    for i in range((width * height) // (2 * 2)):
        psu, _ = item_templates_repository.create_item(psu_template)
        inventory.place_item(psu)

    with pytest.raises(NoSpaceError):
        psu, _ = item_templates_repository.create_item(psu_template)
        inventory.place_item(psu)
