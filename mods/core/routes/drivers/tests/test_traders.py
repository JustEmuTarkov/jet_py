from time import time
from unittest.mock import sentinel
from mods.core.lib.trader import Traders
from mods.core.routes.drivers.traders import FENCE_ASSORT_AMOUNT
from mods.core.routes.drivers.traders import FENCE_CACHE_EXPIRATION
from mods.core.routes.drivers.traders import SESSION_CACHE
from mods.core.routes.drivers.traders import _create_new_items_for_fence
from mods.core.routes.drivers.traders import _is_fence_cache_expired
from mods.core.routes.drivers.traders import get_items_for_fence
from pytest import fixture


class TestIsFenceCacheExpired:
    @fixture(autouse=True)
    def empty_cache_after_test(self):
        yield
        SESSION_CACHE.clear()

    @fixture
    def mchoices(self, mocker):
        return mocker.patch("mods.core.routes.drivers.traders.choices")

    @fixture
    def mget_items(self, mocker):
        return mocker.patch("mods.core.routes.drivers.traders.get_items")

    @fixture
    def mis_fence_cache_expired(self, mocker):
        return mocker.patch("mods.core.routes.drivers.traders._is_fence_cache_expired")

    @fixture
    def mcreate_new_items_for_fence(self, mocker):
        return mocker.patch("mods.core.routes.drivers.traders._create_new_items_for_fence")

    def test_when_cache_is_empty(self):
        """
        _is_fence_cache_expired should return True if cache is empty
        """
        cache = {}
        assert _is_fence_cache_expired(cache) is True

    def test_when_cache_is_expired(self):
        """
        _is_fence_cache_expired should return True if cache is expired
        """
        cache = {"time": time() - FENCE_CACHE_EXPIRATION - 1}
        assert _is_fence_cache_expired(cache) is True

    def test_when_cache_is_not_expired(self):
        """
        _is_fence_cache_expired should return False if cache is not expired
        """
        cache = {"time": time()}
        assert _is_fence_cache_expired(cache) is False

    def test_create_new_items_for_fence(self, mchoices, mget_items):
        """
        _create_new_items_for_fence should choose random FENCE_ASSORT_AMOUNT
        items and set the time of the cache.
        """
        result = _create_new_items_for_fence()
        assert result["items"] == mchoices.return_value
        assert int(result["time"]) == int(time())  # TODO: maybe use freezegun ?
        mchoices.assert_called_once_with(mget_items.return_value, k=FENCE_ASSORT_AMOUNT)
        mget_items.assert_called_once_with(Traders.Fence.value)

    def test_get_items_for_fence_when_cache_is_not_expired(
        self, mis_fence_cache_expired, mcreate_new_items_for_fence
    ):
        """
        get_items_for_fence_when_cache should get the items from the cache if
        the cache is not expired
        """
        SESSION_CACHE[Traders.Fence] = {"items": sentinel.items}
        mis_fence_cache_expired.return_value = False

        assert get_items_for_fence() == sentinel.items
        assert not mcreate_new_items_for_fence.called

    def test_get_items_for_fence_when_cache_is_expired(
        self, mis_fence_cache_expired, mcreate_new_items_for_fence
    ):
        """
        get_items_for_fence_when_cache should create new items list for Fence
        if the cache is expired.
        """
        mis_fence_cache_expired.return_value = True
        mcreate_new_items_for_fence.return_value = {"items": sentinel.items}

        assert get_items_for_fence() == sentinel.items
        mcreate_new_items_for_fence.assert_called_once_with()
