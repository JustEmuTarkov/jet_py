import uuid
from typing import Dict, List

from .models import Item, ItemId


def generate_item_id() -> ItemId:
    """
    Generates new item id

    :return: Generated item id
    """
    unique_id = str(uuid.uuid4())
    unique_id = ''.join(unique_id.split('-')[1:])

    return ItemId(unique_id)


def regenerate_items_ids(items: List[Item]) -> None:
    """
    Generates new ids for all items in list (mutates the list)

    :param items: List[Item]
    :return: None
    """
    items = [item for item in items if item.parent_id is not None]

    id_map: Dict[ItemId, ItemId] = {
        item.id: generate_item_id() for item in items if item.parent_id
    }

    for item in items:
        item.id = id_map[item.id]
        if item.parent_id in id_map:
            item.parent_id = id_map[item.parent_id]
