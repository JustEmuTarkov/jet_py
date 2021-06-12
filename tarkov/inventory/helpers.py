from __future__ import annotations

import uuid
from typing import Dict, List, TYPE_CHECKING, cast

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory.models import Item
    from tarkov.inventory.types import ItemId


def generate_item_id() -> ItemId:
    """
    Generates new item id.

    :return: Generated item id
    """
    unique_id = str(uuid.uuid4())
    unique_id = "".join(unique_id.split("-")[1:])

    return cast("ItemId", unique_id)


def regenerate_items_ids(items: List[Item]) -> None:
    """
    Generates new ids for all items in list (mutates the list).

    :param items: The list of items to edit.
    """
    id_map: Dict[ItemId, ItemId] = {item.id: generate_item_id() for item in items}

    for item in items:
        item.id = id_map[item.id]

        if item.parent_id in id_map:
            item.parent_id = id_map[item.parent_id]


def regenerate_item_ids_dict(items: List[Dict]) -> None:
    id_map: Dict[ItemId, ItemId] = {
        item["_id"]: generate_item_id() for item in items
    }

    for item in items:
        item["_id"] = id_map[item["_id"]]

        if "parentId" in item and item["parentId"] in id_map:
            item["parentId"] = id_map[item["parentId"]]


def clean_items_relationships(items: List[Item]) -> List[Item]:
    """Cleans Item.slot_id and Item.parent_id if parent is not present in given list"""

    for item in items:
        if not any(item.parent_id == parent.id for parent in items):
            item.slot_id = None
            item.parent_id = None
    return items
