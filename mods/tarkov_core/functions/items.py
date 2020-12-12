from typing import Dict

import ujson

from server import db_dir
from server.utils import memoize_once


@memoize_once
def get_item_templates() -> Dict[str, Dict]:
    """
    Returns all the items templates from db/items in form of dict
    where key is item[_id] and value is item itself
    """
    items_dict = {}
    for item_file_path in db_dir.joinpath('items').glob('*'):
        items_data = ujson.load(item_file_path.open('r', encoding='utf8'))
        for item in items_data:
            items_dict[item['_id']] = item

    return items_dict
