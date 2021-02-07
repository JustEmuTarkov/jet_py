from typing import List

from tarkov.inventory import Item, MutableInventory


class SimpleInventory(MutableInventory):
    __items: List[Item]

    def __init__(self, items: List[Item]):
        self.__items = items

    @property
    def items(self) -> List[Item]:
        return self.__items
