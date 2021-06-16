from __future__ import annotations

import random
from typing import List

import pydantic

import server.app
from tarkov.inventory.implementations import SimpleInventory
from tarkov.inventory.inventory import ImmutableInventory
from tarkov.inventory.models import Item
from tarkov.inventory.repositories import ItemTemplatesRepository
from tarkov.inventory.types import TemplateId
from tarkov.trader.models import BarterScheme, BarterSchemeEntry
from tarkov.trader.trader import Trader


class TraderAssortGenerator:
    def __init__(self, trader: Trader) -> None:
        self.trader = trader

    def _read_items(self) -> List[Item]:
        return pydantic.parse_file_as(
            List[Item],
            self.trader.path.joinpath("items.json"),
        )

    def generate_inventory(self) -> ImmutableInventory:
        return SimpleInventory(self._read_items())

    def generate_barter_scheme(self, inventory: ImmutableInventory) -> BarterScheme:
        return BarterScheme.parse_file(self.trader.path.joinpath("barter_scheme.json"))


class FenceAssortGenerator(TraderAssortGenerator):
    def generate_inventory(self) -> ImmutableInventory:
        inventory = SimpleInventory(self._read_items())
        root_items = set(
            item for item in inventory.items.values() if item.slot_id == "hideout"
        )
        assort = random.sample(root_items, k=min(len(root_items), 200))

        child_items: List[Item] = []

        for item in assort:
            child_items.extend(inventory.iter_item_children_recursively(item))

        assort.extend(child_items)

        return SimpleInventory(assort)

    def generate_barter_scheme(self, inventory: ImmutableInventory) -> BarterScheme:
        templates_repository: ItemTemplatesRepository = (
            server.app.container.repos.templates()
        )
        barter_scheme = BarterScheme()

        for item in inventory.items.values():
            item_price = templates_repository.get_template(item.tpl).props.CreditsPrice
            item_price += int(item_price * self.trader.base.discount / 100)
            barter_scheme[item.id] = [
                [
                    BarterSchemeEntry(
                        count=item_price,
                        item_required=TemplateId("5449016a4bdc2d6f028b456f"),
                    )
                ]
            ]

        return barter_scheme
