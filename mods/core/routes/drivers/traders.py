from random import choices
from time import time
from typing import Dict
from typing import List

from mods.core.lib.trader import Traders
from server import db_dir
from ujson import load

SESSION_CACHE: Dict[Traders, Dict] = {}
FENCE_CACHE_EXPIRATION = 60 * 10  # in seconds
FENCE_ASSORT_AMOUNT = 100


def _get_trader_file(trader_id, name):
    traders_path = db_dir.joinpath("assort", trader_id)
    file = traders_path.joinpath(f"{name}.json")
    return load(file.open("r", encoding="utf8"))


def get_barter_scheme(trader_id):
    return _get_trader_file(trader_id, "barter_scheme")


def get_items(trader_id):
    return _get_trader_file(trader_id, "items")


def get_loyal_level_items(trader_id):
    return _get_trader_file(trader_id, "loyal_level_items")


def _is_fence_cache_expired(cache):
    return cache == {} or time() - cache["time"] > FENCE_CACHE_EXPIRATION


def _create_new_items_for_fence():
    items = get_items(Traders.Fence.value)
    return dict(
        items=choices(items, k=FENCE_ASSORT_AMOUNT),
        time=time(),
    )


def get_items_for_fence() -> List[Dict]:
    """
    Get list of items for fence and cache it.
    """
    cache = SESSION_CACHE.get(Traders.Fence, {})
    if _is_fence_cache_expired(cache):
        cache = _create_new_items_for_fence()
        SESSION_CACHE[Traders.Fence] = cache
    return cache["items"]
