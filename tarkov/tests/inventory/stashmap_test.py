from typing import List

from tarkov.inventory import PlayerInventory
from tarkov.inventory.models import Item


def test_can_place_multiple_items(
    inventory: PlayerInventory, random_items: List[Item]
) -> None:
    items = random_items

    for item in items:
        inventory.place_item(item=item)

    assert len(inventory.stash_map.footprints) == len(items)
