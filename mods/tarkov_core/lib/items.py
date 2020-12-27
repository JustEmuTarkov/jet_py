from __future__ import annotations

import enum
from typing import TypedDict, Literal, Union, List, NewType


class Stash(TypedDict):
    equipment: str
    stash: str
    questRaidItems: str
    questStashItems: str
    fastPanel: dict
    items: List[Item]


ItemId = NewType('ItemId', str)
TemplateId = NewType('ItemId', str)


class ItemBase(TypedDict):
    _id: ItemId
    _tpl: TemplateId


class Item(ItemBase, total=False):
    slotId: str
    parentId: ItemId
    location: Union[ItemLocation, int]
    upd: ItemUpd


class ItemUpd(TypedDict, total=False):
    StackObjectsCount: int
    SpawnedInSession: bool
    Repairable: ItemUpdRepairable
    Foldable: ItemUpdFoldable
    FireMode: ItemUpdFireMode


class ItemUpdRepairable(TypedDict):
    MaxDurability: int
    Durability: int


class ItemUpdFoldable(TypedDict):
    Folded: bool


class ItemUpdFireMode(TypedDict):
    FireMode: Literal['single']


class ItemLocation(TypedDict):
    x: int
    y: int
    r: ItemOrientation
    isSearched: bool


class ItemExtraSize(TypedDict):
    up: int
    down: int
    left: int
    right: int


class ItemNotFoundError(Exception):
    pass


ItemOrientation = Literal['Horizontal', 'Vertical']


class ItemOrientationEnum(enum.Enum):
    Horizontal = 'Horizontal'
    Vertical = 'Vertical'


class MoveLocation(TypedDict):
    id: str
    container: str
    location: ItemLocation
