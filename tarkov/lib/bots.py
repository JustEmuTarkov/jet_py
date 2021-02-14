import copy
import random
import time
from pathlib import Path
from typing import List

import ujson
from pydantic import parse_obj_as

from server import db_dir
from tarkov.inventory import MutableInventory
from tarkov.inventory.helpers import generate_item_id, regenerate_items_ids
from tarkov.inventory.models import InventoryModel, Item
from tarkov.inventory.types import TemplateId


class BotInventory(MutableInventory):
    data: InventoryModel

    def __init__(self, bot_inventory: dict):
        self.data = parse_obj_as(InventoryModel, bot_inventory)

    @property
    def items(self) -> List[Item]:
        return self.data.items

    def regenerate_ids(self) -> None:
        regenerate_items_ids(self.items)

        equipment_item = self.get_item_by_template(TemplateId("55d7217a4bdc2d86028b456d"))
        self.data.equipment = equipment_item.id

        quest_raid_items = self.get_item_by_template(TemplateId("5963866286f7747bf429b572"))
        self.data.questRaidItems = quest_raid_items.id

        quest_stash_items = self.get_item_by_template(TemplateId("5963866b86f7747bfa1c4462"))
        self.data.questStashItems = quest_stash_items.id

        stash = self.get_item_by_template(TemplateId("566abbc34bdc2d92178b4576"))
        self.data.stash = stash.id


class BotGenerator:
    def __init__(self):
        self.__bot_base = ujson.load(db_dir.joinpath("base", "botBase.json").open(encoding="utf8"))

    def generate_bot(self, role: str, difficulty: str) -> dict:
        bot = copy.deepcopy(self.__bot_base)

        bot["_id"] = f"bot{generate_item_id()}"

        bot["Info"]["Settings"]["Role"] = role
        bot["Info"]["Settings"]["BotDifficulty"] = difficulty
        bot["Info"]["experience"] = 1

        bot_path = db_dir.joinpath("bots", role)

        random_inventory_path: Path = random.choice(list(bot_path.joinpath("inventory").glob("*.json")))

        bot_inventory = BotInventory(ujson.load(random_inventory_path.open(encoding="utf8")))
        bot_inventory.regenerate_ids()

        bot["Inventory"] = bot_inventory.data.dict()

        self.__generate_health(bot, role)

        return bot

    @staticmethod
    def __generate_health(bot, role):
        health_base = {
            "Hydration": {"Current": 100, "Maximum": 100},
            "Energy": {"Current": 100, "Maximum": 100},
            "BodyParts": {
                "Head": {"Health": {"Current": 35, "Maximum": 35}},
                "Chest": {"Health": {"Current": 80, "Maximum": 80}},
                "Stomach": {"Health": {"Current": 70, "Maximum": 70}},
                "LeftArm": {"Health": {"Current": 60, "Maximum": 60}},
                "RightArm": {"Health": {"Current": 60, "Maximum": 60}},
                "LeftLeg": {"Health": {"Current": 65, "Maximum": 65}},
                "RightLeg": {"Health": {"Current": 65, "Maximum": 65}},
            },
            "UpdateTime": 0,
        }

        bot_health = ujson.load(db_dir.joinpath("bots", role).joinpath("health", "default.json").open(encoding="utf8"))

        # Set current and maximum energy and hydration
        health_base["Hydration"]["Current"] = bot_health["Hydration"]
        health_base["Hydration"]["Maximum"] = bot_health["Hydration"]

        health_base["Energy"]["Current"] = bot_health["Energy"]
        health_base["Energy"]["Maximum"] = bot_health["Energy"]

        for key, value in health_base["BodyParts"].items():
            bot_body_part_hp = bot_health["BodyParts"][key]
            value["Health"]["Current"] = bot_body_part_hp
            value["Health"]["Maximum"] = bot_body_part_hp

        health_base["UpdateTime"] = int(time.time())
        bot["Health"] = health_base
