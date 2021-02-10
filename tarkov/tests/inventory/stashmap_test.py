from typing import List

from tarkov.inventory.models import Item, ItemInventoryLocation, ItemOrientationEnum


def test_can_place_multiple_items(inventory, random_items: List[Item]):
    items = random_items

    for item in items:
        inventory.place_item(item=item)

    assert len(inventory.stash_map.footprints) == len(items)


def test_weapon_folding(make_inventory):
    inventory = make_inventory('weapon_toz_inventory.json')
    toz = inventory.get_item('d1024bc3af40f3634e30f98d')
    toz_mods = list(inventory.iter_item_children_recursively(toz))
    assert (3, 1) == inventory.stash_map._get_item_size_in_stash(toz, toz_mods, toz.location)

    inventory.remove_item(toz)
    inventory.place_item(
        toz,
        child_items=toz_mods,
        location=ItemInventoryLocation(
            x=7,
            y=0,
            r=ItemOrientationEnum.Horizontal.value
        )
    )
