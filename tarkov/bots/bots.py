from __future__ import annotations

import copy
import random
from pprint import pprint
from typing import Dict, Final

import ujson
from pydantic import parse_obj_as

from server import db_dir
from tarkov.bots.equipment import BotEquipmentGenerator
from tarkov.bots.loot import BotLootGenerator
from tarkov.bots.weapon import BotWeaponGenerator
from tarkov.exceptions import NotFoundError
from tarkov.inventory import (
    MutableInventory,
    generate_item_id,
    regenerate_items_ids,
)
from tarkov.inventory.models import InventoryModel, Item
from tarkov.inventory.types import ItemId, TemplateId


class BotInventory(MutableInventory):
    inventory: InventoryModel

    def __init__(self, bot_inventory: dict):
        self.inventory = parse_obj_as(InventoryModel, bot_inventory)
        self.__items = {i.id: i for i in self.inventory.items}

    @staticmethod
    def make_empty() -> BotInventory:
        equipment_id = generate_item_id()
        stash_id = generate_item_id()
        quest_raid_items_id = generate_item_id()
        quest_stash_items_id = generate_item_id()

        bot_inventory = {
            "items": [
                {"_id": stash_id, "_tpl": "566abbc34bdc2d92178b4576"},
                {"_id": quest_raid_items_id, "_tpl": "5963866286f7747bf429b572"},
                {"_id": quest_stash_items_id, "_tpl": "5963866b86f7747bfa1c4462"},
                {"_id": equipment_id, "_tpl": "55d7217a4bdc2d86028b456d"},
            ],
            "equipment": equipment_id,
            "stash": stash_id,
            "questRaidItems": quest_raid_items_id,
            "questStashItems": quest_stash_items_id,
            "fastPanel": {},
        }
        return BotInventory(bot_inventory)

    def get_equipment(self, slot_id: str) -> Item:
        """
        :param slot_id: Slot id of an item to find (For example "Headwear")
        :return: item with given slot_id
        :raises: NotFoundError if item with specified slot_id was not found
        """

        for item in self.items.values():
            if item.slot_id == slot_id:
                return item
        else:
            raise NotFoundError(f"Item with slot_id {slot_id} was not found")

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self.__items

    def regenerate_ids(self) -> None:
        regenerate_items_ids(list(self.items.values()))

        equipment_item = self.get_by_template(TemplateId("55d7217a4bdc2d86028b456d"))
        self.inventory.equipment = equipment_item.id

        quest_raid_items = self.get_by_template(TemplateId("5963866286f7747bf429b572"))
        self.inventory.questRaidItems = quest_raid_items.id

        quest_stash_items = self.get_by_template(TemplateId("5963866b86f7747bfa1c4462"))
        self.inventory.questStashItems = quest_stash_items.id

        stash = self.get_by_template(TemplateId("566abbc34bdc2d92178b4576"))
        self.inventory.stash = stash.id

    def __enter__(self) -> BotInventory:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        if exc_type is None:
            self.inventory.items = list(self.__items.values())


class BotGenerator:
    bot_inventory: BotInventory

    def __init__(self, bot_role: str) -> None:
        self._bot_base: Final[dict] = ujson.load(db_dir.joinpath("base", "botBase.json").open(encoding="utf8"))
        self.dir = db_dir.joinpath("bots", bot_role)
        self.bot_role = bot_role

        self.generation_preset: dict = ujson.load(self.dir.joinpath("generation.json").open(encoding="utf8"))
        self.inventory_preset: dict = ujson.load(self.dir.joinpath("inventory.json").open(encoding="utf8"))
        self.chances_preset: dict = ujson.load(self.dir.joinpath("chances.json").open(encoding="utf8"))
        self.health_base: dict = ujson.load(self.dir.joinpath("health.json").open(encoding="utf8"))
        self.appearance: dict = ujson.load(self.dir.joinpath("appearance.json").open(encoding="utf8 "))

    def generate(self) -> dict:
        """
        Generates bot profile with role specified in class constructor.
        All bot parameters such as inventory and health are taken from database.

        :return: Bot profile as dictionary
        """

        self.bot_inventory = BotInventory.make_empty()
        bot_base = copy.deepcopy(self._bot_base)

        with self.bot_inventory:
            equipment_generator = BotEquipmentGenerator(self)
            equipment_generator.generate_equipment()

            weapon_generator = BotWeaponGenerator(self)
            weapon_generator.generate()

            loot_generator = BotLootGenerator(self)
            loot_generator.generate()
            self.bot_inventory.regenerate_ids()

        bot_base["Inventory"] = self.bot_inventory.inventory.dict(exclude_none=True)
        bot_base["Health"] = copy.deepcopy(self.health_base)

        bot_base["_id"] = generate_item_id()
        bot_base["Info"]["Side"] = "Savage"
        self.__generate_appearance(bot_base)

        return bot_base

    def __generate_appearance(self, bot_base: dict) -> None:
        """
        Changes bot_base appearance and voice to random ones from self.appearance

        :param bot_base: Bot base to apply appearance
        :return: None
        """
        bot_base["Info"]["Voice"] = random.choice(self.appearance["voice"])
        # TODO customization probably have incorrect id's or it's from newer version
        # So 9787 client doesn't work with it

        # bot_base["Customization"]["Head"] = random.choice(self.appearance["head"])
        # bot_base["Customization"]["Body"] = random.choice(self.appearance["body"])
        # bot_base["Customization"]["Feet"] = random.choice(self.appearance["feet"])
        # bot_base["Customization"]["Hands"] = random.choice(self.appearance["hands"])


if __name__ == "__main__":
    bot_generator = BotGenerator("assault")
    bot_profile = bot_generator.generate()

    print(ujson.dumps(bot_profile))
