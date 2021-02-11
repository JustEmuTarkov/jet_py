from __future__ import annotations

import copy
import itertools
import random
import time
from typing import Iterable, List, TYPE_CHECKING, Union

import pydantic
import ujson

from server import db_dir
from tarkov.inventory import ImmutableInventory, item_templates_repository, regenerate_items_ids
from tarkov.inventory.models import Item, ItemUpd
from tarkov.trader.models import BoughtItems, Traders

if TYPE_CHECKING:
    from tarkov.profile import Profile

FENCE_ASSORT_LIFETIME = 10 * 60


class TraderInventory(ImmutableInventory):
    trader: Traders
    profile: Profile
    items: List[Item]
    base: dict
    _barter_scheme: dict
    _loyal_level_items: dict
    quest_assort: dict

    __fence_assort: List[Item] = []
    __fence_assort_created_at: int = 0

    def __init__(self, trader: Traders, profile: Profile):
        self.trader = trader
        self.profile = profile

        trader_path = db_dir.joinpath('traders', self.trader.value)

        self.items = pydantic.parse_obj_as(
            List[Item],
            ujson.load(trader_path.joinpath('items.json').open('r', encoding='utf8'))
        )
        self.base = ujson.load(trader_path.joinpath('base.json').open('r', encoding='utf8'))
        self._barter_scheme = ujson.load(trader_path.joinpath('barter_scheme.json').open('r', encoding='utf8'))
        self.loyal_level_items = ujson.load(trader_path.joinpath('loyal_level_items.json').open('r', encoding='utf8'))
        self._quest_assort = ujson.load(trader_path.joinpath('questassort.json').open('r', encoding='utf8'))

    @property
    def assort(self) -> List[Item]:
        if self.trader == Traders.Fence:
            current_time = time.time()
            expired = current_time > TraderInventory.__fence_assort_created_at + FENCE_ASSORT_LIFETIME

            if not TraderInventory.__fence_assort or expired:
                TraderInventory.__fence_assort = self._generate_fence_assort()
                TraderInventory.__fence_assort_created_at = int(time.time())

            return TraderInventory.__fence_assort
        return self._trader_assort()

    @property
    def barter_scheme(self):
        if self.trader == Traders.Fence:
            barter_scheme = {}

            for item in self.items:
                item_price = self.get_item_price(item)

                barter_scheme[item.id] = [[
                    {
                        'count': item_price,
                        "_tpl": "5449016a4bdc2d6f028b456f",
                    }
                ]]

            return barter_scheme

        return self._barter_scheme

    def _generate_fence_assort(self) -> List[Item]:
        root_items = [item for item in self.items if item.slotId == 'hideout']
        assort = random.sample(root_items, k=min(len(root_items), 500))

        child_items: List[Item] = []

        for item in assort:
            child_items.extend(self.iter_item_children_recursively(item))

        assort.extend(child_items)

        return assort

    def _trader_assort(self) -> List[Item]:
        items: Iterable[Item] = self.items

        def filter_quest_assort(item: Item) -> bool:
            if item.id not in self._quest_assort['success']:
                return True

            quest_id = self._quest_assort['success'][item.id]
            quest = self.profile.quests.get_quest(quest_id)
            return quest['status'] == 'Success'  # TODO: Extract into enum

        def filter_loyal_level(item: Item) -> bool:
            if item.id not in self.loyal_level_items:
                return True

            required_standing = self.loyal_level_items[item.id]
            return self.standing['currentLevel'] >= required_standing

        items = filter(filter_quest_assort, items)
        items = filter(filter_loyal_level, items)
        return list(items)

    def can_sell(self, item: Item) -> bool:
        try:
            category_id = item_templates_repository.get_category(item)
        except KeyError:
            return False
        return category_id in self.base['sell_category']

    def get_item_price(self, item: Item) -> int:
        price: float = 0

        for i in itertools.chain([item], self.iter_item_children_recursively(item)):
            item_template = item_templates_repository.get_template(i)
            price += item_template.props.CreditsPrice

        return int(price)

    def get_sell_price(self, item: Item) -> int:
        """
        :returns Price of item and it's children
        """
        if not self.can_sell(item):
            raise ValueError('Item is not sellable')

        tpl = item_templates_repository.get_template(item)
        price = tpl.props.CreditsPrice

        for child in self.profile.inventory.iter_item_children_recursively(item):
            child_tpl = item_templates_repository.get_template(child)
            child_price = child_tpl.props.CreditsPrice
            if self.can_sell(child):
                price += child_price
            else:
                price += child_price * 0.85

        return int(price)

    def buy_item(self, item_id: str, count: int) -> List[BoughtItems]:
        base_item = self.get_item(item_id)
        item_template = item_templates_repository.get_template(base_item.tpl)
        item_stack_size = item_template.props.StackMaxSize

        bought_items_list: List[BoughtItems] = []

        while count:
            stack_size = min(count, item_stack_size)
            count -= stack_size
            item: Item = base_item.copy(deep=True)
            item.upd.StackObjectsCount = 1
            children_items: List[Item] = [
                child.copy(deep=True) for child in self.iter_item_children_recursively(base_item)
            ]

            all_items = children_items + [item]
            regenerate_items_ids(all_items)
            for item in all_items:
                item.upd.UnlimitedCount = False

            item.upd = ItemUpd(StackObjectsCount=stack_size)
            bought_items_list.append(BoughtItems(item=item, children_items=children_items))

        return bought_items_list

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

    def _increase_sales_sum(self, amount: int):
        raise NotImplementedError

    @property
    def standing(self) -> dict:
        trader_id = self.trader.value

        if self.trader.value not in self.profile.pmc_profile['TraderStandings']:
            self.profile.pmc_profile['TraderStandings'][trader_id] = copy.deepcopy(self.base['loyalty'])

        return self.profile.pmc_profile['TraderStandings'][trader_id]


def get_trader_bases() -> List[dict]:
    traders_path = db_dir.joinpath('traders')

    paths = set(traders_path.rglob('*/base.json')) - set(traders_path.rglob('ragfair/base.json'))

    traders_data = [ujson.load(file.open('r', encoding='utf8')) for file in paths]
    traders_data = sorted(traders_data, key=lambda trader: trader['_id'])

    return traders_data


def get_trader_base(trader_id: str) -> dict:
    base_path = db_dir.joinpath('traders', trader_id, 'base.json')
    if not base_path.exists():
        raise ValueError(f'Path {base_path} does not exists')
    return ujson.load(base_path.open('r', encoding='utf8'))
