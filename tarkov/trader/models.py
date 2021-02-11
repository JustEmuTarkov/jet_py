from enum import Enum
from typing import List, NamedTuple, TypedDict

from tarkov.inventory.models import Item, TemplateId


class TraderType(Enum):
    Mechanic = '5a7c2eca46aef81a7ca2145d'
    Ragman = '5ac3b934156ae10c4430e83c'
    Jaeger = '5c0647fdd443bc2504c2d371'
    Prapor = '54cb50c76803fa8b248b4571'
    Therapist = '54cb57776803fa99248b456e'
    Fence = '579dc571d53a0658a154fbec'
    Peacekeeper = '5935c25fb3acc3127c3d8cd9'
    Skier = '58330581ace78e27b8b10cee'


class TraderBase(TypedDict):
    sell_category: List[TemplateId]


class BoughtItems(NamedTuple):
    item: Item
    children_items: List[Item]
