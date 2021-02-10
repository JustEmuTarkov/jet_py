from typing import List

from tarkov.inventory import PlayerInventory
from tarkov.inventory.models import Item


def test_can_place_multiple_items(empty_inventory: PlayerInventory, random_items: List[Item]):
    items = random_items

    for item in items:
        empty_inventory.place_item(item=item)

    assert len(empty_inventory.stash_map.footprints) == len(items)
