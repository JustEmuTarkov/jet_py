from typing import List

from tarkov.inventory import PlayerInventory
from tarkov.inventory.models import Item


def test_adds_items(empty_inventory: PlayerInventory, random_items: List[Item]):
    for item in random_items:
        empty_inventory.add_item(item, [])

    assert all(item in empty_inventory.inventory.items for item in random_items)
