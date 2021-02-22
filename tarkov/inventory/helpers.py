import uuid
from typing import Dict, List, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from tarkov.inventory.models import Item
    from tarkov.inventory.types import ItemId


def generate_item_id() -> "ItemId":
    """
    Generates new item id

    :return: Generated item id
    """
    unique_id = str(uuid.uuid4())
    unique_id = "".join(unique_id.split("-")[1:])

    return cast("ItemId", unique_id)


def regenerate_items_ids(items: List["Item"]) -> None:
    """
    Generates new ids for all items in list (mutates the list)
    """
    id_map: Dict["ItemId", "ItemId"] = {item.id: generate_item_id() for item in items}

    for item in items:
        item.id = id_map[item.id]
        if item.parent_id in id_map:
            item.parent_id = id_map[item.parent_id]


def regenerate_item_ids_dict(items: List[Dict]) -> None:
    items: List[Dict] = [item for item in items if "parentId" in item]

    id_map: Dict["ItemId", "ItemId"] = {item["_id"]: generate_item_id() for item in items}

    for item in items:
        item["_id"] = id_map[item["_id"]]
        if item["parentId"] in id_map:
            item["parentId"] = id_map[item["parentId"]]
