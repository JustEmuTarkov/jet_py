from __future__ import annotations

from typing import List, TYPE_CHECKING, Tuple

from tarkov.inventory.implementations import SimpleInventory

if TYPE_CHECKING:
    from tarkov.inventory.models import Item
    from tarkov.offraid.models import OffraidHealth, OffraidProfile
    from tarkov.profile.profile import Profile


class OffraidSaveService:
    def __init__(
        self,
        protected_slots: List[str],
        retained_slots: List[str],
    ):
        self.protected_slots = protected_slots
        self.retained_slots = retained_slots

    def _update_health(self, profile: Profile, raid_health: OffraidHealth) -> None:
        pmc_health = profile.pmc.Health

        for body_part, body_part_health in raid_health.health.items():
            pmc_health["BodyParts"][body_part]["Health"][
                "Maximum"
            ] = body_part_health.maximum
            pmc_health["BodyParts"][body_part]["Health"][
                "Current"
            ] = body_part_health.current
            pmc_health["BodyParts"][body_part]["Effects"] = body_part_health.effects

        pmc_health["Hydration"]["Current"] = raid_health.hydration
        pmc_health["Energy"]["Current"] = raid_health.energy

    def get_protected_items(
        self, raid_profile: OffraidProfile
    ) -> List[Tuple[Item, List[Item]]]:
        raid_inventory = SimpleInventory(raid_profile.Inventory.items)
        protected_items: List[Tuple[Item, List[Item]]] = []
        for item in raid_inventory:
            if item.parent_id != raid_profile.Inventory.equipment:
                continue

            if item.slot_id in self.protected_slots:
                protected_items.append(
                    (item, list(raid_inventory.iter_item_children_recursively(item)))
                )

            elif item.slot_id in self.retained_slots:
                protected_items.append((item, []))

        return protected_items

    def _update_inventory(
        self,
        profile: Profile,
        raid_profile: OffraidProfile,
        is_alive: bool,
    ) -> None:
        raid_inventory = SimpleInventory(items=raid_profile.Inventory.items)
        equipment: Item = profile.inventory.get(profile.inventory.inventory.equipment)
        # Remove current profile equipment completely
        profile.inventory.remove_item(equipment, remove_children=True)

        if is_alive:
            raid_equipment: List[Item] = list(
                raid_inventory.iter_item_children_recursively(
                    raid_inventory.get(equipment.id)
                )
            )
            profile.inventory.add_item(equipment, child_items=raid_equipment)
        else:
            profile.inventory.add_item(equipment)
            protected_items = self.get_protected_items(raid_profile=raid_profile)
            for item, child_items in protected_items:
                profile.inventory.add_item(item=item, child_items=child_items)

    def update_profile(
        self,
        profile: Profile,
        raid_profile: OffraidProfile,
        raid_health: OffraidHealth,
    ) -> None:
        self._update_health(profile=profile, raid_health=raid_health)
        self._update_inventory(
            profile=profile, raid_profile=raid_profile, is_alive=raid_health.is_alive
        )

        profile.pmc.Encyclopedia.update(raid_profile.Encyclopedia)
        profile.pmc.Skills = raid_profile.Skills
        profile.pmc.Quests = raid_profile.Quests
        profile.pmc.Stats = raid_profile.Stats

        backend_counters = raid_profile.BackendCounters
        for key, raid_counter in backend_counters.items():
            profile_counter = profile.pmc.BackendCounters.get(key, raid_counter)
            profile.pmc.BackendCounters[key] = max(
                raid_counter, profile_counter, key=lambda c: c.value
            )
