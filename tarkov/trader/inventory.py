from typing import Dict, List

import pydantic

from tarkov.inventory.inventory import ImmutableInventory
from tarkov.inventory.models import Item
from tarkov.inventory.types import ItemId
from tarkov.trader.trader import Trader


class TraderInventory(ImmutableInventory):
    def __init__(self, trader: Trader):
        super().__init__()
        self.trader = trader
        self.__items = {
            item.id: item
            for item in pydantic.parse_file_as(
                List[Item],
                self.trader.path.joinpath("items.json"),
            )
        }

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self.__items
