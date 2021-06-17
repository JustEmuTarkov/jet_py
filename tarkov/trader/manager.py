from __future__ import annotations

from typing import Callable, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.trader.models import TraderType
    from tarkov.trader.trader import Trader


class TraderManager:
    def __init__(self, trader_factory: Callable[..., Trader]) -> None:
        self.__trader_factory = trader_factory
        self.__traders: Dict[TraderType, Trader] = {}

    def get_trader(self, trader_type: TraderType) -> Trader:
        if trader_type not in self.__traders:
            self.__traders[trader_type] = self.__trader_factory(trader_type)

        return self.__traders[trader_type]
