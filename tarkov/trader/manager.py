from typing import Dict

from tarkov.trader.models import TraderType
from tarkov.trader.trader import Trader


class TraderManager:
    def __init__(self) -> None:
        self.__traders: Dict[TraderType, Trader] = {}

    def get_trader(self, trader_type: TraderType) -> Trader:
        if trader_type not in self.__traders:
            self.__traders[trader_type] = Trader(trader_type)

        return self.__traders[trader_type]
