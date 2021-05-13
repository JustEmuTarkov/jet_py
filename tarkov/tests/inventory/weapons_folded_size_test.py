import pytest

from tarkov.inventory.inventory import PlayerInventory
from .conftest import TEST_RESOURCES_PATH

test_inventories = TEST_RESOURCES_PATH.joinpath("folding").rglob("*.json")


@pytest.mark.parametrize(
    "inventory_path",
    test_inventories,
)
def test_folding_calculation(make_inventory, inventory_path) \
:
    inventory: PlayerInventory = make_inventory(inventory_path)
    weapon = inventory.get("test_weapon")
    weapon_mods = list(inventory.iter_item_children_recursively(weapon))

    width, height, *_ = inventory_path.stem.split("_")
    width, height = int(width), int(height)

    assert inventory.get_item_size(weapon, weapon_mods) == (width, height)
