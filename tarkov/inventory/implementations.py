from typing import List

from tarkov.inventory import MutableInventory
from tarkov.inventory.models import Item


class SimpleInventory(MutableInventory):
    __items: List[Item]

    def __init__(self, items: List[Item]):
        self.__items = items

        for item in self.__items:
            item.__inventory__ = self

    @property
    def items(self) -> List[Item]:
        return self.__items
