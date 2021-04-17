from __future__ import annotations

import random
from typing import Set, TYPE_CHECKING

from dependency_injector.wiring import Provide, inject

from server.container import AppContainer
from tarkov.inventory.helpers import generate_item_id
from tarkov.inventory.models import Item
from tarkov.inventory.types import TemplateId

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.bots.generator.preset import BotGeneratorPreset
    from tarkov.bots.bots import BotInventory
    from tarkov.inventory.repositories import ItemTemplatesRepository


class BotEquipmentGenerator:
    @inject
    def __init__(
        self,
        bot_inventory: BotInventory,
        preset: BotGeneratorPreset,
        templates_repository: ItemTemplatesRepository = Provide[
            AppContainer.repos.templates
        ],
    ):
        self.bot_inventory = bot_inventory
        self.preset = preset
        self.templates_repository = templates_repository

    def __filter_conflicting_items(
        self, template_id: TemplateId, equipment_slots_to_generate: Set[str]
    ) -> bool:
        template = self.templates_repository.get_template(template_id)
        blocks_slots: Set[str] = {
            k.lstrip("Blocks")
            for k, v in template.props.dict().items()
            if k.startswith("Blocks") and v is True
        }
        # If any of slots that should be generated conflicts with slots that item blocks
        if not blocks_slots.isdisjoint(equipment_slots_to_generate):
            return False
        # If template conflicts with any of the existing items
        if any(
            item.tpl in template.props.ConflictingItems
            for item in self.bot_inventory.items.values()
        ):
            return False
        # If any of the existing items conflict with template
        if any(
            template.id
            in self.templates_repository.get_template(item).props.ConflictingItems
            for item in self.bot_inventory.items.values()
        ):
            return False
        return True

    def generate_equipment(self) -> None:

        """
        Generates equipment items (Weapons, Backpack, Rig, etc)
        """

        # A set with equipment slots that should be generated
        equipment_slots_to_generate: Set[str] = {
            slot
            for slot, template_ids in self.preset.inventory["equipment"].items()
            if (
                # If slot isn't present in the _chances then it should be always generated
                slot not in self.preset.chances["equipment"]
                # Else we check if it should spawn
                or random.uniform(0, 100) <= self.preset.chances["equipment"][slot]
            )
            and template_ids
        }
        # Force pistol to generate if primary weapon wasn't generated
        weapon_slots = "FirstPrimaryWeapon", "SecondPrimaryWeapon"
        if not any(slot in equipment_slots_to_generate for slot in weapon_slots):
            equipment_slots_to_generate.add("Holster")

        assert any(
            i in weapon_slots
            for i in ("FirstPrimaryWeapon", "SecondPrimaryWeapon", "Holster")
        )
        for equipment_slot in equipment_slots_to_generate:
            template_ids = self.preset.inventory["equipment"][equipment_slot]
            template_ids = [
                i
                for i in template_ids
                if self.__filter_conflicting_items(i, equipment_slots_to_generate)
            ]

            random_template_id = random.choice(template_ids)
            self.bot_inventory.add_item(
                Item(
                    id=generate_item_id(),
                    tpl=random_template_id,
                    slot_id=equipment_slot,
                    parent_id=self.bot_inventory.inventory.equipment,
                )
            )
