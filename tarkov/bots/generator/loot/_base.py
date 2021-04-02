from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject

from tarkov.containers import Container
from ._types import BotInventoryContainers, LootGenerationConfig

if TYPE_CHECKING:
    from tarkov.bots.bots import BotInventory
    from tarkov.bots import BotGeneratorPreset
    from tarkov.inventory import ItemTemplatesRepository


class BaseLootGenerator:
    @inject
    def __init__(
        self,
        inventory_containers: BotInventoryContainers,
        bot_inventory: BotInventory,
        config: LootGenerationConfig,
        preset: BotGeneratorPreset,
        templates_repository: ItemTemplatesRepository = Provide[Container.templates_repository],
    ):
        self.inventory_containers = inventory_containers
        self.bot_inventory = bot_inventory
        self.config = config
        self.preset = preset
        self.templates_repository = templates_repository

    def generate(self) -> None:
        raise NotImplementedError
