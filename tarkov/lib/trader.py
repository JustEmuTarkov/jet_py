import copy
import itertools
import random
import time
from enum import Enum
from typing import List, Tuple, TypedDict, Union

import pydantic
import ujson

from server import db_dir
from tarkov.inventory import (ImmutableInventory, Item, ItemUpd, PlayerInventory, TemplateId,
                              item_templates_repository, )
from tarkov.inventory.helpers import generate_item_id, regenerate_items_ids


class Traders(Enum):
    Mechanic = '5a7c2eca46aef81a7ca2145d'
    Ragman = '5ac3b934156ae10c4430e83c'
    Jaeger = '5c0647fdd443bc2504c2d371'
    Prapor = '54cb50c76803fa8b248b4571'
    Therapist = '54cb57776803fa99248b456e'
    Fence = '579dc571d53a0658a154fbec'
    Peacekeeper = '5935c25fb3acc3127c3d8cd9'
    Skier = '58330581ace78e27b8b10cee'


class TraderBase(TypedDict):
    sell_category: List[TemplateId]


class TraderInventory(ImmutableInventory):
    trader: Traders
    player_inventory: PlayerInventory

    FENCE_ASSORT_LIFETIME = 10 * 60
    __fence_assort: List[Item] = []
    __fence_assort_created_at: int = 0

    def __init__(self, trader: Traders, player_inventory: PlayerInventory):
        self.trader = trader
        self.player_inventory = player_inventory

        assort_path = db_dir.joinpath('assort', self.trader.value)
        self.__items: List[Item] = pydantic.parse_obj_as(
            List[Item],
            ujson.load(assort_path.joinpath('items.json').open('r', encoding='utf8'))
        )
        base_path = db_dir.joinpath('base', 'traders', self.trader.value, 'base.json')
        self.__base = ujson.load(base_path.open('r', encoding='utf8'))

        self.__barter_scheme = ujson.load(assort_path.joinpath('barter_scheme.json').open('r', encoding='utf8'))
        self.loyal_level_items = ujson.load(assort_path.joinpath('loyal_level_items.json').open('r', encoding='utf8'))

    @property
    def assort(self) -> List[Item]:
        if self.trader == Traders.Fence:
            current_time = time.time()
            expired = current_time > TraderInventory.__fence_assort_created_at + TraderInventory.FENCE_ASSORT_LIFETIME

            if not TraderInventory.__fence_assort or expired:
                root_items = [item for item in self.__items if item.slotId == 'hideout']
                assort = random.sample(root_items, k=min(len(root_items), 500))

                child_items: List[Item] = []

                for item in assort:
                    child_items.extend(self.iter_item_children_recursively(item))

                assort.extend(child_items)

                TraderInventory.__fence_assort = assort
                TraderInventory.__fence_assort_created_at = int(time.time())

            return TraderInventory.__fence_assort

        return self.__items

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

        return self.__barter_scheme

    @property
    def base(self):
        return self.__base

    def can_sell(self, item: Item) -> bool:
        try:
            category_id = item_templates_repository.get_category(item)
        except KeyError:
            return False
        return category_id in self.__base['sell_category']

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

        for child in self.player_inventory.iter_item_children_recursively(item):
            child_tpl = item_templates_repository.get_template(child)
            child_price = child_tpl.props.CreditsPrice
            if self.can_sell(child):
                price += child_price
            else:
                price += child_price * 0.85

        return int(price)

    @property
    def items(self) -> List[Item]:
        return self.__items

    def buy_item(self, item_id: str, count: int) -> Tuple[List[Item], List[Item]]:
        """
        :return: Tuple with two elements: first is bought items, second is children of these items
        """
        base_item = copy.deepcopy(self.get_item(item_id))
        item_template = item_templates_repository.get_template(base_item.tpl)
        item_stack_size = item_template.props.StackMaxSize

        bought_items: List[Item] = []
        bought_child_items: List[Item] = []

        if item_stack_size == 1:
            for _ in range(count):
                item: Item = base_item.copy(deep=True)
                item.upd.StackObjectsCount = 1
                child_items: List[Item] = list(child.copy(deep=True) for child in self.iter_item_children_recursively(base_item))

                all_items = child_items + [item]
                regenerate_items_ids(all_items)

                bought_items.append(item)
                bought_child_items.extend(child_items)

            return bought_items, bought_child_items

        while count:
            stack_size = min(count, item_stack_size)
            count -= stack_size
            item = copy.deepcopy(base_item)
            item.id = generate_item_id()
            item.upd = ItemUpd(StackObjectsCount=stack_size)
            bought_items.append(item)

        return bought_items, []

    def calculate_insurance_price(self, items: Union[Item, List[Item]]) -> int:
        if isinstance(items, Item):
            items = [items]

        price: float = 0
        for item in items:
            item_template = item_templates_repository.get_template(item)
            price += item_template.props.CreditsPrice * 0.1
            #  Todo account for trader standing (subtract standing from insurance price, 0.5 (50%) max)

        return int(price)
