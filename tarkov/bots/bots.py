import copy
import random
import time
from pathlib import Path
from typing import Dict, List

import ujson
from pydantic import parse_obj_as

from server import db_dir
from tarkov import config
from tarkov.inventory import MutableInventory, generate_item_id, regenerate_items_ids
from tarkov.inventory.models import InventoryModel, Item
from tarkov.inventory.types import ItemId, TemplateId


class BotInventory(MutableInventory):
    data: InventoryModel

    def __init__(self, bot_inventory: dict):
        self.data = parse_obj_as(InventoryModel, bot_inventory)
        self.__items = {i.id: i for i in self.data.items}

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self.__items

    def regenerate_ids(self) -> None:
        regenerate_items_ids(list(self.items.values()))

        equipment_item = self.get_by_template(TemplateId("55d7217a4bdc2d86028b456d"))
        self.data.equipment = equipment_item.id

        quest_raid_items = self.get_by_template(TemplateId("5963866286f7747bf429b572"))
        self.data.questRaidItems = quest_raid_items.id

        quest_stash_items = self.get_by_template(TemplateId("5963866b86f7747bfa1c4462"))
        self.data.questStashItems = quest_stash_items.id

        stash = self.get_by_template(TemplateId("566abbc34bdc2d92178b4576"))
        self.data.stash = stash.id


class BotGenerator:
    def __init__(self) -> None:
        self.__bot_base = ujson.load(db_dir.joinpath("base", "botBase.json").open(encoding="utf8"))
        self.bots_directory = db_dir.joinpath("bots")

    @staticmethod
    def __choose_bot_role(role: str) -> str:
        if role != "assault":
            return role
        cfg = config.bot_generation
        roles = {"assault": cfg.scav_chance, "bear": cfg.bear_chance, "usec": cfg.usec_change}
        return random.choices(population=list(roles.keys()), weights=list(roles.values()), k=1)[0]

    def __choose_bot_name(self, role: str) -> str:
        names_path = self.bots_directory.joinpath(role, "names.json")
        names: List[str] = ujson.load(names_path.open(encoding="utf8"))
        return random.choice(names)

    @staticmethod
    def __get_bot_side(role: str) -> str:
        sides_map = {
            "bear": "Bear",
            "usec": "Usec",
            "scav": "Savage",
        }
        try:
            return sides_map[role.lower()]
        except KeyError:
            return "Savage"

    def __apply_customization(self, role: str, bot: dict) -> None:
        customization_path = self.bots_directory.joinpath(role, "appearance.json")
        customization: dict = ujson.load(customization_path.open(encoding="utf8"))

        bot["Customization"] = {
            k: random.choice(values)
            for k, values in customization.items()
            if k in {"body", "feet", "hands", "head"}
        }
        bot["Info"]["Voice"] = random.choice(customization["voice"])

    def generate_bot(self, role: str, difficulty: str) -> dict:
        bot = copy.deepcopy(self.__bot_base)

        bot_role = self.__choose_bot_role(role)
        self.__apply_customization(bot_role, bot)

        bot["_id"] = f"bot{generate_item_id()}"
        bot["Info"]["Side"] = self.__get_bot_side(bot_role)
        bot["Info"]["Nickname"] = self.__choose_bot_name(role)

        bot["Info"]["Settings"]["Role"] = role
        bot["Info"]["Settings"]["BotDifficulty"] = difficulty
        bot["Info"]["experience"] = 1

        bot_path = db_dir.joinpath("bots", bot_role)

        random_inventory_path: Path = random.choice(list(bot_path.joinpath("inventory").glob("*.json")))

        bot_inventory = BotInventory(ujson.load(random_inventory_path.open(encoding="utf8")))
        bot_inventory.regenerate_ids()

        bot["Inventory"] = bot_inventory.data.dict(exclude_none=True)

        self.__generate_health(bot, bot_role)

        return bot

    @staticmethod
    def __generate_health(bot: dict, role: str) -> None:
        health_base: dict = {
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

        bot_health: dict = ujson.load(
            db_dir.joinpath("bots", role).joinpath("health", "default.json").open(encoding="utf8")
        )

        # Set current and maximum energy and hydration
        health_base["Hydration"]["Current"] = bot_health["Hydration"]
        health_base["Hydration"]["Maximum"] = bot_health["Hydration"]

        health_base["Energy"]["Current"] = bot_health["Energy"]
        health_base["Energy"]["Maximum"] = bot_health["Energy"]

        for key, body_part in health_base["BodyParts"].items():
            bot_body_part_hp = bot_health["BodyParts"][key]
            body_part["Health"]["Current"] = bot_body_part_hp
            body_part["Health"]["Maximum"] = bot_body_part_hp

        health_base["UpdateTime"] = int(time.time())
        bot["Health"] = health_base
