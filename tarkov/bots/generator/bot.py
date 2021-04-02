from __future__ import annotations

import copy
import random
from typing import Callable, Final, TYPE_CHECKING

import ujson
from dependency_injector.wiring import inject

from server import db_dir
from tarkov.bots.bots import BotInventory
from tarkov.inventory import generate_item_id
from .equipment import BotEquipmentGenerator
from .loot import BotLootGenerator
from .weapon import BotWeaponGenerator

if TYPE_CHECKING:
    from tarkov.bots import BotGeneratorPreset


class BotGenerator:
    @inject
    def __init__(self, preset_factory: Callable[..., BotGeneratorPreset]) -> None:
        self._bot_base: Final[dict] = ujson.load(db_dir.joinpath("base", "botBase.json").open(encoding="utf8"))
        self.preset_factory = preset_factory

    def generate(self, bot_role: str) -> dict:
        """
        Generates bot profile with role specified in class constructor.
        All bot parameters such as inventory and health are taken from database.

        :return: Bot profile as dictionary
        """
        preset: BotGeneratorPreset = self.preset_factory(bot_role=bot_role)

        bot_inventory = BotInventory.make_empty()
        bot_base = copy.deepcopy(self._bot_base)

        with bot_inventory:
            equipment_generator = BotEquipmentGenerator(bot_inventory=bot_inventory, preset=preset)
            equipment_generator.generate_equipment()

            weapon_generator = BotWeaponGenerator(bot_inventory=bot_inventory, preset=preset)
            weapon_generator.generate()

            loot_generator = BotLootGenerator(bot_inventory=bot_inventory, preset=preset)
            loot_generator.generate()
            bot_inventory.regenerate_ids()

        bot_base["Inventory"] = bot_inventory.inventory.dict(exclude_none=True)
        bot_base["Health"] = copy.deepcopy(preset.health)

        bot_base["_id"] = generate_item_id()
        bot_base["Info"]["Side"] = "Savage"
        self.__generate_appearance(bot_base, preset)

        return bot_base

    @staticmethod
    def __generate_appearance(bot_base: dict, preset: BotGeneratorPreset) -> None:
        """
        Changes bot_base appearance and voice to random ones from self.appearance

        :param bot_base: Bot base to apply appearance
        :return: None
        """
        bot_base["Info"]["Voice"] = random.choice(preset.appearance["voice"])
        # TODO customization probably have incorrect id's or it's from newer version
        # so 9787 client doesn't work with it

        # bot_base["Customization"]["Head"] = random.choice(self.appearance["head"])
        # bot_base["Customization"]["Body"] = random.choice(self.appearance["body"])
        # bot_base["Customization"]["Feet"] = random.choice(self.appearance["feet"])
        # bot_base["Customization"]["Hands"] = random.choice(self.appearance["hands"])
