from __future__ import annotations

import random
from typing import Dict, Generic, Optional, Sequence, TypeVar

from pydantic import BaseModel, Field, PrivateAttr
from pydantic.generics import GenericModel

from tarkov.bots.bots import BotInventory
from tarkov.exceptions import NotFoundError
from tarkov.inventory.implementations import MultiGridContainer

T = TypeVar("T")  # pylint: disable=invalid-name


class MinMax(GenericModel, Generic[T]):
    max: T
    min: T


class LootGenerationConfig(BaseModel):
    healing: MinMax[int]
    loose_loot: MinMax[int] = Field(alias="looseLoot")
    magazines: MinMax[int]
    grenades: MinMax[int]


class BotInventoryContainers(BaseModel):
    """
    Class to hold containers for backpack, rig and pockets
    """

    class Config:
        arbitrary_types_allowed = True

    __bot_inventory__: BotInventory = PrivateAttr()

    TacticalVest: Optional[MultiGridContainer]
    Pockets: MultiGridContainer
    Backpack: Optional[MultiGridContainer]

    def containers(self, include: Sequence[str] = None) -> Sequence[MultiGridContainer]:
        """
        :param include: List of slot ids to include, includes everything by default
        :return: Sequence of containers with slot_id that are present in include parameter
        """
        if not include:
            include = tuple(self.__fields__.keys())

        for slot_id in include:
            if slot_id not in self.__fields__:
                raise ValueError(
                    f"{slot_id} element of include argument is not present in fields of {self.__class__.__name__}"
                )

        containers = []

        for slot_id in self.__fields__:
            if slot_id not in include:
                continue
            container: Optional[MultiGridContainer] = self.__getattribute__(slot_id)
            if container is None:
                continue

            containers.append(container)

        return containers

    @classmethod
    def from_inventory(cls, bot_inventory: BotInventory) -> BotInventoryContainers:
        containers: Dict[str, MultiGridContainer] = {}
        for slot_id in cls.__fields__:
            try:
                containers[slot_id] = MultiGridContainer.from_item(
                    bot_inventory.get_equipment(slot_id), slot_id
                )
            except NotFoundError:
                pass

        obj = cls.parse_obj(
            containers,
        )
        obj.__bot_inventory__ = bot_inventory
        return obj

    def flush(self) -> None:
        """
        Flushes inventories items into bot inventory
        """
        for container in self.containers():
            for sub_inventory in container.inventories:
                self.__bot_inventory__.items.update(sub_inventory.items)

    def random_container(self, include: Sequence[str] = None) -> MultiGridContainer:
        """
        :param include: slot id's to include, will include all containers if none
        :return: Randomly chosen container, weighted by it's size
        """
        containers = self.containers(include=include)
        weights = [container.size for container in containers]

        return random.choices(containers, weights=weights, k=1)[0]
