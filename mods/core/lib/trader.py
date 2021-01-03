import copy
from enum import Enum
from typing import Tuple, TypedDict, List

import ujson

from mods.core.lib.inventory import ImmutableInventory, InventoryItems, generate_item_id
from mods.core.lib.inventory import Inventory
from mods.core.lib.items import Item, ItemUpd
from mods.core.lib.items import TemplateId, ItemTemplatesRepository
from server import db_dir


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
    def __init__(self, trader: Traders, player_inventory: Inventory):
        self.player_inventory = player_inventory
        self.trader_id = trader.value
        self.__items = ujson.load(db_dir.joinpath('assort', self.trader_id, 'items.json').open('r', encoding='utf8'))

        base_path = db_dir.joinpath('base', 'traders', self.trader_id, 'base.json')
        self.__base = ujson.load(base_path.open('r', encoding='utf8'))

    def can_sell(self, item: Item) -> bool:
        try:
            category_id = ItemTemplatesRepository().get_category(item)
        except KeyError:
            return False
        return category_id in self.__base['sell_category']

    def get_price(self, item: Item) -> int:
        """
        :returns Price of item and it's children
        """
        if not self.can_sell(item):
            raise ValueError('Item is not sellable')

        templates_repository = ItemTemplatesRepository()
        tpl = templates_repository.get_template(item)
        price = tpl['_props']['CreditsPrice']

        for child in self.player_inventory.iter_item_children_recursively(item):
            child_tpl = templates_repository.get_template(child)
            child_price = child_tpl['_props']['CreditsPrice']
            if self.can_sell(child):
                price += child_price
            else:
                price += child_price * 0.85

        return int(price)

    @property
    def items(self) -> InventoryItems:
        return self.__items

    def buy_item(self, item_id: str, count: int) -> Tuple[InventoryItems, InventoryItems]:
        """
        :return: Tuple with two elements: first is bought items, second is children of these items
        """
        base_item = copy.deepcopy(self.get_item(item_id))
        item_template = ItemTemplatesRepository().get_template(base_item['_tpl'])
        item_stack_size = item_template['_props']['StackMaxSize']

        bought_items: InventoryItems = []
        bought_child_items: InventoryItems = []

        if item_stack_size == 1:
            for _ in range(count):
                item: Item = copy.deepcopy(base_item)
                id_map = {
                    item['_id']: generate_item_id()
                }
                child_items = []

                for child in (copy.deepcopy(child) for child in self.iter_item_children_recursively(item)):
                    id_map[child['_id']] = generate_item_id()
                    child_items.append(child)

                item['_id'] = id_map[item['_id']]
                for child in child_items:
                    child['_id'] = id_map[child['_id']]
                    child['parentId'] = id_map[child['parentId']]

                del item['upd']
                bought_items.append(item)
                bought_child_items.extend(child_items)

            return bought_items, bought_child_items

        while count:
            stack_size = min(count, item_stack_size)
            count -= stack_size
            item = copy.deepcopy(base_item)
            item['_id'] = generate_item_id()
            item['upd'] = ItemUpd(StackObjectsCount=stack_size)
            bought_items.append(item)

        return bought_items, []
