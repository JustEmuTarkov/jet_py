from __future__ import annotations

from typing import Dict

from pydantic import parse_obj_as

from tarkov.exceptions import NotFoundError
from tarkov.inventory.helpers import (
    generate_item_id,
    regenerate_items_ids,
)
from tarkov.inventory.inventory import MutableInventory
from tarkov.inventory.models import InventoryModel, Item
from tarkov.inventory.types import ItemId, TemplateId


class BotInventory(MutableInventory):
    inventory: InventoryModel

    def __init__(self, bot_inventory: dict):
        super().__init__()
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
