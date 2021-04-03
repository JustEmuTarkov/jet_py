import random
from functools import cached_property
from typing import List

from tarkov.exceptions import NoSpaceError
from tarkov.inventory.models import Item, ItemTemplate
from tarkov.inventory.prop_models import MedsProps
from ._base import BaseLootGenerator


class MedsGenerator(BaseLootGenerator):
    def generate(self) -> None:
        """
        Generates med items in tactical vest and pockets

        :return: None
        """
        amount = random.randint(self.config.healing.min, self.config.healing.max)

        for _ in range(amount):
            container = self.inventory_containers.random_container(include=["TacticalVest", "Pockets"])
            try:
                container.place_randomly(self._make_random_meds())
            except NoSpaceError:
                pass

    @cached_property
    def _meds_templates(self) -> List[ItemTemplate]:
        return [
            tpl
            for tpl in self.templates_repository.templates.values()
            if isinstance(tpl.props, MedsProps) and tpl.props.Rarity != "Not_Exists"
        ]

    def _make_random_meds(self) -> Item:
        template = random.choices(
            population=self._meds_templates,
            weights=[tpl.props.SpawnChance for tpl in self._meds_templates],
            k=1,
        )[0]
        return Item(tpl=template.id)
