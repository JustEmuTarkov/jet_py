from typing import Dict, List

from tarkov.inventory import MutableInventory
from tarkov.inventory.models import Item
from tarkov.inventory.types import ItemId


class SimpleInventory(MutableInventory):
    def __init__(self, items: List[Item]):
        self.__items: Dict[ItemId, Item] = {i.id: i for i in items}

        for item in self.__items.values():
            item.__inventory__ = self

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self.__items
