from __future__ import annotations

import itertools
import random
import time
from typing import ClassVar, Dict, Iterable, List, TYPE_CHECKING, Union

import pydantic
import ujson

from server import db_dir
from tarkov.inventory import (
    ImmutableInventory,
    item_templates_repository,
    regenerate_items_ids,
)
from tarkov.inventory.models import Item, ItemUpd
from tarkov.inventory.types import CurrencyEnum, ItemId, TemplateId
from tarkov.quests.models import QuestStatus
from tarkov.repositories.categories import category_repository
from tarkov.trader.models import (
    BarterScheme,
    BarterSchemeEntry,
    BoughtItems,
    Price,
    TraderBase,
    TraderStanding,
    TraderType,
)

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile import Profile

FENCE_ASSORT_LIFETIME = 10 * 60


class Trader:
    def __init__(self, type_: TraderType, profile: Profile):
        self.type: TraderType = type_
        self.path = db_dir.joinpath("traders", self.type.value)
        self.player_profile: Profile = profile

        self._base: TraderBase = TraderBase.parse_file(self.path.joinpath("base.json"))
        self.inventory = TraderInventory(self)

    @property
    def base(self) -> TraderBase:
        trader_base = self._base.copy(deep=True)
        trader_base.loyalty = self.standing
        return trader_base

    def can_sell(self, item: Item) -> bool:
        try:
            category_id = category_repository.get_category(item.tpl).Id
        except KeyError:
            return False
        return category_id in self.base.sell_category

    def get_item_price(self, item: Item) -> int:
        price: float = 0

        for i in itertools.chain([item], self.inventory.iter_item_children_recursively(item)):
            item_template = item_templates_repository.get_template(i)
            price += item_template.props.CreditsPrice

        return int(price)

    def get_sell_price(self, item: Item) -> Price:
        """
        :returns Price of item and it's children
        """
        if not self.can_sell(item):
            raise ValueError("Item is not sellable")

        tpl = item_templates_repository.get_template(item)
        price_rub = tpl.props.CreditsPrice

        for child in self.player_profile.inventory.iter_item_children_recursively(item):
            child_tpl = item_templates_repository.get_template(child)
            child_price = child_tpl.props.CreditsPrice
            if self.can_sell(child):
                price_rub += child_price
            # else:
            #     price += int(child_price * 0.85)
        currency_template_id: TemplateId = TemplateId(CurrencyEnum[self.base.currency].value)
        currency_ratio = category_repository.item_categories[currency_template_id].Price
        price = round(price_rub / currency_ratio)
        return Price(
            template_id=currency_template_id,
            amount=price,
        )

    @staticmethod
    def calculate_insurance_price(items: Union[Item, List[Item]]) -> int:
        if isinstance(items, Item):
            items = [items]

        price: float = 0
        for item in items:
            item_template = item_templates_repository.get_template(item)
            price += item_template.props.CreditsPrice * 0.1
            #  Todo account for trader standing (subtract standing from insurance price, 0.5 (50%) max)

        return int(price)

    def buy_item(self, item_id: ItemId, count: int) -> List[BoughtItems]:
        base_item = self.inventory.get(item_id)
        item_template = item_templates_repository.get_template(base_item.tpl)
        item_stack_size = item_template.props.StackMaxSize

        bought_items_list: List[BoughtItems] = []

        while count:
            stack_size = min(count, item_stack_size)
            count -= stack_size
            item: Item = base_item.copy(deep=True)
            item.upd.StackObjectsCount = 1
            children_items: List[Item] = [
                child.copy(deep=True) for child in self.inventory.iter_item_children_recursively(base_item)
            ]

            all_items = children_items + [item]
            regenerate_items_ids(all_items)
            for item in all_items:
                item.upd.UnlimitedCount = False

            item.upd = ItemUpd(StackObjectsCount=stack_size)
            bought_items_list.append(BoughtItems(item=item, children_items=children_items))

        return bought_items_list

    @property
    def standing(self) -> TraderStanding:
        if self.type.value not in self.player_profile.pmc.TraderStandings:
            standing_copy: TraderStanding = self._base.loyalty.copy(deep=True)
            self.player_profile.pmc.TraderStandings[self.type.value] = TraderStanding.parse_obj(
                standing_copy
            )

        return self.player_profile.pmc.TraderStandings[self.type.value]


class TraderInventory(ImmutableInventory):
    __fence_assort: ClassVar[List[Item]] = []
    __fence_assort_created_at: ClassVar[int] = 0

    def __init__(self, trader: Trader):
        self.trader = trader

        self.assort_items: Dict[ItemId, Item] = {
            item.id: item
            for item in pydantic.parse_obj_as(
                List[Item],
                ujson.load(self.trader.path.joinpath("items.json").open("r", encoding="utf8")),
            )
        }
        self._barter_scheme = BarterScheme.parse_file(self.trader.path.joinpath("barter_scheme.json"))
        self.loyal_level_items = ujson.load(
            self.trader.path.joinpath("loyal_level_items.json").open("r", encoding="utf8")
        )
        self._quest_assort = ujson.load(
            self.trader.path.joinpath("questassort.json").open("r", encoding="utf8")
        )

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self.assort_items

    @property
    def assort(self) -> List[Item]:
        if self.trader.type == TraderType.Fence:
            current_time = time.time()
            expired = current_time > (TraderInventory.__fence_assort_created_at + FENCE_ASSORT_LIFETIME)

            if not TraderInventory.__fence_assort or expired:
                TraderInventory.__fence_assort = self._generate_fence_assort()
                TraderInventory.__fence_assort_created_at = int(time.time())

            return TraderInventory.__fence_assort
        return self._trader_assort()

    @property
    def barter_scheme(self) -> BarterScheme:
        if self.trader.type == TraderType.Fence:
            return self._get_fence_barter_scheme()

        return self._barter_scheme

    def _get_fence_barter_scheme(self) -> BarterScheme:
        barter_scheme = BarterScheme()

        for item in self.items.values():
            item_price = self.trader.get_item_price(item)

            barter_scheme[item.id] = [
                [
                    BarterSchemeEntry(
                        count=item_price,
                        item_required=TemplateId("5449016a4bdc2d6f028b456f"),
                    )
                ]
            ]

        return barter_scheme

    def _generate_fence_assort(self) -> List[Item]:
        root_items = set(item for item in self.items.values() if item.slot_id == "hideout")
        assort = random.sample(root_items, k=min(len(root_items), 200))

        child_items: List[Item] = []

        for item in assort:
            child_items.extend(self.iter_item_children_recursively(item))

        assort.extend(child_items)

        return assort

    def _trader_assort(self) -> List[Item]:
        def filter_quest_assort(item: Item) -> bool:
            if item.id not in self._quest_assort["success"]:
                return True

            quest_id = self._quest_assort["success"][item.id]
            try:
                quest = self.trader.player_profile.quests.get_quest(quest_id)
            except KeyError:
                return False
            return quest.status == QuestStatus.Success

        def filter_loyal_level(item: Item) -> bool:
            if item.id not in self.loyal_level_items:
                return True

            required_standing = self.loyal_level_items[item.id]
            return self.trader.standing.current_level >= required_standing

        def filter_in_root(item: Item) -> bool:
            return item.slot_id == "hideout"

        items = filter(filter_in_root, self.items.values())  # Filter root items
        items = filter(filter_quest_assort, items)  # Filter items that require quest completion
        items = filter(filter_loyal_level, items)  # Filter items that require loyalty level

        def assort_inner(items_list: Iterable[Item]) -> Iterable[Item]:
            """Return item and it's children from trader inventory"""
            for item in items_list:
                yield item
                yield from self.iter_item_children_recursively(item)

        return list(assort_inner(items))
