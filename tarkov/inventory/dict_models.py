from __future__ import annotations

import enum
from typing import Literal, TypedDict

from .models import ItemId


class ItemLocation(TypedDict, total=False):
    x: int
    y: int
    r: ItemOrientation
    isSearched: bool


class ItemExtraSize(TypedDict):
    up: int
    down: int
    left: int
    right: int


ItemOrientation = Literal['Horizontal', 'Vertical']


class ItemOrientationEnum(enum.Enum):
    Horizontal = 'Horizontal'
    Vertical = 'Vertical'


class MoveLocationBase(TypedDict):
    id: ItemId
    container: str


class MoveLocation(MoveLocationBase, total=False):
    location: ItemLocation
