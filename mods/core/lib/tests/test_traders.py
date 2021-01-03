from mods.core.lib.trader import Traders
from pytest import mark


class TestTradersEnum:
    def test_is_fence_true(self):
        assert Traders.is_fence(Traders.Fence) is True

    @mark.parametrize(
        "trader_id",
        [
            Traders.Mechanic,
            Traders.Ragman,
            Traders.Jaeger,
            Traders.Prapor,
            Traders.Therapist,
            Traders.Peacekeeper,
            Traders.Skier,
        ],
    )
    def test_is_fence_false(self, trader_id):
        assert Traders.is_fence(trader_id) is False
