from __future__ import annotations

from typing import TYPE_CHECKING

from ._loose import LooseLootGenerator
from ._magazine import BotMagazineGenerator
from ._meds import MedsGenerator
from ._types import BotInventoryContainers, LootGenerationConfig

if TYPE_CHECKING:
    from tarkov.bots import BotGeneratorPreset
    from tarkov.bots.bots import BotInventory


class BotLootGenerator:
    def __init__(self, bot_inventory: BotInventory, preset: BotGeneratorPreset):
        self.bot_inventory = bot_inventory
        self.preset = preset
        self.config = LootGenerationConfig.parse_obj(preset.generation["items"])
        self.bot_inventory_containers = BotInventoryContainers.from_inventory(self.bot_inventory)

    def generate(self) -> None:
        """
        Generates loot in bot inventory

        :return: None
        """
        generators = [
            MedsGenerator,
            BotMagazineGenerator,
            LooseLootGenerator,
        ]
        for generator in generators:
            g = generator(
                inventory_containers=self.bot_inventory_containers,
                bot_inventory=self.bot_inventory,
                config=self.config,
                preset=self.preset,
            )
            g.generate()

        self.bot_inventory_containers.flush()
