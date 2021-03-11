from __future__ import annotations

import copy
import random
from pprint import pprint
from typing import Dict, Final, List, Set

import ujson
from pydantic import parse_obj_as

from server import db_dir
from tarkov.exceptions import NoSpaceError
from tarkov.inventory import (
    MutableInventory,
    generate_item_id,
    item_templates_repository,
    regenerate_items_ids,
)
from tarkov.inventory.factories import item_factory
from tarkov.inventory.implementations import MultiGridContainer
from tarkov.inventory.models import InventoryModel, Item, ItemTemplate, ItemUpd
from tarkov.inventory.prop_models import MagazineProps
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
    _bot_base: Final[dict]
    bot_inventory: BotInventory

    def __init__(self, bot_role: str) -> None:
        self._bot_base = ujson.load(db_dir.joinpath("base", "botBase.json").open(encoding="utf8"))
        self.dir = db_dir.joinpath("bots", bot_role)
        self.bot_role = bot_role

        self._generation_preset: dict = ujson.load(self.dir.joinpath("generation.json").open(encoding="utf8"))
        self._inventory_preset: dict = ujson.load(self.dir.joinpath("inventory.json").open(encoding="utf8"))
        self._chances_preset: dict = ujson.load(self.dir.joinpath("chances.json").open(encoding="utf8"))
        self._health_base: dict = ujson.load(self.dir.joinpath("health.json").open(encoding="utf8"))

    def generate(self) -> dict:
        """
        Generates bot profile with role specified in class constructor.
        All bot parameters such as inventory and health are taken from database.

        :return: Bot profile as dictionary
        """

        self.bot_inventory = BotInventory.make_empty()
        bot_base = copy.deepcopy(self._bot_base)
        with self.bot_inventory:
            self.__generate_inventory()
            self.bot_inventory.regenerate_ids()

        bot_base["Inventory"] = self.bot_inventory.inventory.dict(exclude_none=True)
        bot_base["Health"] = copy.deepcopy(self._health_base)

        bot_base["_id"] = generate_item_id()
        bot_base["Info"]["Side"] = "Savage"

        return bot_base

    def __generate_equipment_items(self) -> None:
        """
        Generates equipment items (Weapons, Backpack, Rig, etc)
        """

        # A set with equipment slots that should be generated
        equipment_slots_to_generate: Set[str] = {
            slot
            for slot, template_ids in self._inventory_preset["equipment"].items()
            if (
                # If slot isn't present in the _chances then it should be always generated
                slot not in self._chances_preset["equipment"]
                # Else we check if it should spawn
                or random.uniform(0, 100) <= self._chances_preset["equipment"][slot]
            )
            and template_ids
        }
        # Force pistol to generate if primary weapon wasn't generated
        weapon_slots = "FirstPrimaryWeapon", "SecondPrimaryWeapon"
        if not any(slot in equipment_slots_to_generate for slot in weapon_slots):
            equipment_slots_to_generate.add("Holster")

        assert any(i in weapon_slots for i in ("FirstPrimaryWeapon", "SecondPrimaryWeapon", "Holster"))
        for equipment_slot in equipment_slots_to_generate:
            template_ids = self._inventory_preset["equipment"][equipment_slot]

            # if equipment_slot in blocked_slots:
            #     continue

            def filter_conflicting_items(template_id: TemplateId) -> bool:
                template = item_templates_repository.get_template(template_id)
                blocks_slots: Set[str] = {
                    k.lstrip("Blocks")
                    for k, v in template.props.dict().items()
                    if k.startswith("Blocks") and v is True
                }
                if not blocks_slots.isdisjoint(equipment_slots_to_generate):
                    return False
                # If template conflicts with any of the existing items
                if any(
                    item.tpl in template.props.ConflictingItems for item in self.bot_inventory.items.values()
                ):
                    return False
                # If any of the existing items conflict with template
                if any(
                    template.id in item_templates_repository.get_template(item).props.ConflictingItems
                    for item in self.bot_inventory.items.values()
                ):
                    return False
                return True

            template_ids = list(filter(filter_conflicting_items, template_ids))
            random_template_id = random.choice(template_ids)

            self.bot_inventory.add_item(
                Item(
                    id=generate_item_id(),
                    tpl=random_template_id,
                    slot_id=equipment_slot,
                    parent_id=self.bot_inventory.inventory.equipment,
                )
            )

    def __generate_gun_mods(self) -> None:
        """
        Generates equipment mods
        """
        amount_of_items = len(self.bot_inventory.items)
        seen_templates: Set[str] = set()

        while True:
            for item_template_id, slots in self._inventory_preset["mods"].items():
                # Skip iteration if item with parent_id we need isn't present in inventory
                try:
                    parent = next(i for i in self.bot_inventory.items.values() if i.tpl == item_template_id)
                except StopIteration:
                    continue
                # Skip if we already generated children for that template
                if item_template_id in seen_templates:
                    continue
                seen_templates.add(item_template_id)

                for slot, template_ids in slots.items():
                    try:
                        if not random.uniform(0, 100) <= self._chances_preset["mods"][slot]:
                            continue
                    except KeyError:
                        pass

                    def filter_conflicting_items(template_id: TemplateId) -> bool:
                        template = item_templates_repository.get_template(template_id)

                        for inventory_item in self.bot_inventory.items.values():
                            item_template = item_templates_repository.get_template(inventory_item.tpl)

                            if template_id in item_template.props.ConflictingItems:
                                return False

                            if inventory_item.tpl in template.props.ConflictingItems:
                                return False
                        return True

                    template_ids = list(filter(filter_conflicting_items, template_ids))
                    if not template_ids:
                        continue

                    random_template = item_templates_repository.get_template(random.choice(template_ids))
                    # If parent item is a magazine then we should set proper stack size for ammo
                    upd = ItemUpd()
                    if slot == "cartridges":
                        parent_template = item_templates_repository.get_template(parent.tpl)
                        assert isinstance(parent_template.props, MagazineProps)
                        upd.StackObjectsCount = parent_template.props.Cartridges[0].max_count

                    item = Item(
                        id=generate_item_id(),
                        tpl=random_template.id,
                        slot_id=slot,
                        parent_id=parent.id,
                        upd=upd,
                    )
                    self.bot_inventory.add_item(item)

            # break from loop if we didn't generate any new items
            if amount_of_items == len(self.bot_inventory.items):
                break
            amount_of_items = len(self.bot_inventory.items)

    def __generate_inventory(self) -> None:
        self.__generate_equipment_items()
        self.__generate_gun_mods()
        self.__populate_containers()

    def __populate_containers(self) -> None:
        containers: List[Item] = [
            i for i in self.bot_inventory.items.values() if i.slot_id in self._inventory_preset["items"]
        ]
        for container in containers:
            assert container.slot_id is not None
            self.__populate_container(container, container.slot_id)

    def __populate_container(self, container: Item, container_slot: str) -> None:
        templates: List[ItemTemplate] = [
            item_templates_repository.get_template(tpl)
            for tpl in self._inventory_preset["items"][container_slot]
        ]
        templates_chances: List[float] = [t.props.SpawnChance for t in templates]

        items_to_generate: Final[int] = random.randint(
            self._generation_preset["items"]["looseLoot"]["min"],
            self._generation_preset["items"]["looseLoot"]["max"],
        )

        container_inventory = MultiGridContainer.from_item(container)

        for _ in range(items_to_generate):
            for _ in range(10):
                item_template: ItemTemplate = random.choices(templates, templates_chances, k=1)[0]
                item, child_items = item_factory.create_item(item_template, 1)
                try:
                    container_inventory.place_randomly(item, child_items)
                    break
                except NoSpaceError:
                    continue

        for sub_inventory in container_inventory.inventories:
            self.bot_inventory.items.update(sub_inventory.items)


if __name__ == "__main__":
    bot_generator = BotGenerator("assault")
    bot_profile = bot_generator.generate()
    pprint(bot_profile["Inventory"]["items"])
    print(len(bot_profile["Inventory"]["items"]))
