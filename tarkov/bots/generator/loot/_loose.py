import random
from typing import List, Tuple

from dependency_injector.wiring import Provide, inject

from server.container import AppContainer
from tarkov.exceptions import NoSpaceError
from tarkov.inventory.factories import ItemFactory
from tarkov.inventory.models import Item, ItemTemplate
from tarkov.inventory.prop_models import StackableItemProps
from ._base import BaseLootGenerator


class LooseLootGenerator(BaseLootGenerator):
    def generate(self) -> None:
        """
        Generates loose loot items in backpack, tactical vest or pockets.

        :return: None
        """
        amount = random.randint(self.config.loose_loot.min, self.config.loose_loot.max)
        for _ in range(amount):
            for _ in range(10):
                try:
                    container = self.inventory_containers.random_container()
                    item, child_items = self._make_random_item(container.slot_id)
                    container.place_randomly(item, child_items)
                    break
                except NoSpaceError:
                    continue

    @inject
    def _make_random_item(
        self,
        slot_id: str,
        item_factory: ItemFactory = Provide[AppContainer.items.factory],
    ) -> Tuple[Item, List[Item]]:
        templates: List[ItemTemplate] = [
            self.templates_repository.get_template(tpl)
            for tpl in self.preset.inventory["items"][slot_id]
        ]
        templates_chances: List[float] = [t.props.SpawnChance for t in templates]
        template: ItemTemplate = random.choices(templates, templates_chances, k=1)[0]

        # If item is stackable then we have to generate count for it
        if isinstance(template.props, StackableItemProps):
            return item_factory.create_item(
                template,
                count=random.randint(
                    template.props.StackMinRandom, template.props.StackMaxRandom
                ),
            )

        return item_factory.create_item(template)
