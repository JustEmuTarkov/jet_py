from __future__ import annotations

import random
from typing import List, Set, TYPE_CHECKING

from tarkov.inventory import generate_item_id, item_templates_repository
from tarkov.inventory.models import Item
from tarkov.inventory.types import TemplateId

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.bots.bots import BotInventory
    from tarkov.bots import BotGeneratorPreset


class BotWeaponGenerator:
    def __init__(self, bot_inventory: BotInventory, preset: BotGeneratorPreset):
        self.bot_inventory = bot_inventory
        self.preset = preset

    def __filter_conflicting_items(self, template_id: TemplateId) -> bool:
        template = item_templates_repository.get_template(template_id)

        for inventory_item in self.bot_inventory.items.values():
            item_template = item_templates_repository.get_template(inventory_item.tpl)

            if template_id in item_template.props.ConflictingItems:
                return False

            if inventory_item.tpl in template.props.ConflictingItems:
                return False
        return True

    def generate(self) -> None:
        """
        Generates equipment mods based on inventory.json file
        """
        amount_of_items = len(self.bot_inventory.items)
        # List of templates that were already populated
        seen_templates: Set[TemplateId] = set()

        while True:
            for item_template_id, slots in self.preset.inventory["mods"].items():
                try:
                    # Skip iteration if item with template id we need isn't present in inventory
                    parent = next(i for i in self.bot_inventory.items.values() if i.tpl == item_template_id)
                except StopIteration:
                    continue
                # Skip if we already generated children for that template
                if item_template_id in seen_templates:
                    continue

                seen_templates.add(item_template_id)

                for slot, template_ids in slots.items():
                    self.__generate_mod(slot=slot, template_ids=template_ids, parent=parent)

            # break from loop if we didn't generate any new items
            if amount_of_items == len(self.bot_inventory.items):
                break
            amount_of_items = len(self.bot_inventory.items)

    def __generate_mod(self, slot: str, template_ids: List[TemplateId], parent: Item) -> None:
        try:
            if not random.uniform(0, 100) <= self.preset.chances["mods"][slot]:
                return
        except KeyError:
            return

        template_ids = list(filter(self.__filter_conflicting_items, template_ids))
        if not template_ids:
            return

        random_template = item_templates_repository.get_template(random.choice(template_ids))
        # Ammo generation will be handler later via BotMagazineGenerator class
        if slot == "cartridges":
            return
        else:
            item = Item(
                id=generate_item_id(),
                tpl=random_template.id,
                slot_id=slot,
                parent_id=parent.id,
            )
        self.bot_inventory.add_item(item)