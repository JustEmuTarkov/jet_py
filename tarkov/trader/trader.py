from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Dict, Final, Iterable, List, TYPE_CHECKING

import pydantic

from server import db_dir
from tarkov.config import TradersConfig
from tarkov.inventory.helpers import regenerate_items_ids
from tarkov.inventory.inventory import ImmutableInventory
from tarkov.inventory.models import Item, ItemUpd
from tarkov.inventory.repositories import ItemTemplatesRepository
from tarkov.inventory.types import CurrencyEnum, ItemId, TemplateId
from tarkov.repositories.categories import category_repository
from tarkov.trader.assort_generators import FenceAssortGenerator, TraderAssortGenerator
from tarkov.trader.interfaces import BaseTraderView
from tarkov.trader.models import (
    BarterScheme,
    BoughtItems,
    Price,
    QuestAssort,
    TraderBase,
    TraderType,
)

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile.profile import Profile


class Trader:
    inventory: ImmutableInventory
    barter_scheme: BarterScheme
    __supply_next_time: datetime

    def __init__(
        self,
        trader_type: TraderType,
        templates_repository: ItemTemplatesRepository,
        trader_view_factory: Callable[..., BaseTraderView],
        config: TradersConfig,
    ):
        self.__templates_repository = templates_repository
        self.__view_factory = trader_view_factory
        self.__config = config

        self.type: Final[TraderType] = trader_type
        self.path = db_dir.joinpath("traders", self.type.value)

        self.__barter_scheme_generator: TraderAssortGenerator
        if trader_type == TraderType.Fence:
            self.__barter_scheme_generator = FenceAssortGenerator(self)
        else:
            self.__barter_scheme_generator = TraderAssortGenerator(self)

        self._base: Final[TraderBase] = TraderBase.parse_file(
            self.path.joinpath("base.json")
        )
        self.loyal_level_items: Final[Dict[str, int]] = pydantic.parse_file_as(
            Dict[str, int], self.path.joinpath("loyal_level_items.json")
        )
        self.quest_assort: Final[QuestAssort] = QuestAssort.parse_file(
            self.path.joinpath("questassort.json")
        )
        self.__update()

    def __update(self) -> None:
        self.__supply_next_time = datetime.now() + timedelta(
            seconds=self.__config.assort_refresh_time_sec
        )
        self.inventory = self.__barter_scheme_generator.generate_inventory()
        self.barter_scheme: BarterScheme = (
            self.__barter_scheme_generator.generate_barter_scheme(self.inventory)
        )

    def __try_update(self) -> None:
        now = datetime.now()
        if now > self.__supply_next_time:
            self.__update()

    def view(self, player_profile: Profile) -> BaseTraderView:
        self.__try_update()
        return self.__view_factory(trader=self, player_profile=player_profile)

    @property
    def base(self) -> TraderBase:
        self.__try_update()
        trader_base = self._base.copy(deep=True)
        trader_base.supply_next_time = int(self.__supply_next_time.timestamp())
        return trader_base

    def can_sell(self, item: Item) -> bool:
        try:
            category = category_repository.get_category(item.tpl)
            return category.Id in self.base.sell_category or any(
                c.Id in self.base.sell_category
                for c in category_repository.parent_categories(category)
            )
        except KeyError:
            return False

    def get_sell_price(self, item: Item, children_items: Iterable[Item]) -> Price:
        """
        :returns Price of item and it's children
        """
        if not self.can_sell(item):
            raise ValueError("Item is not sellable")

        tpl = self.__templates_repository.get_template(item)
        price_rub = tpl.props.CreditsPrice

        for child in children_items:
            child_tpl = self.__templates_repository.get_template(child)
            child_price = child_tpl.props.CreditsPrice
            if self.can_sell(child):
                price_rub += child_price

        currency_template_id: TemplateId = TemplateId(
            CurrencyEnum[self.base.currency].value
        )
        currency_ratio = category_repository.item_categories[currency_template_id].Price
        price = round(price_rub / currency_ratio)
        return Price(
            template_id=currency_template_id,
            amount=price,
        )

    def buy_item(self, item_id: ItemId, count: int) -> List[BoughtItems]:
        base_item = self.inventory.get(item_id)
        item_template = self.__templates_repository.get_template(base_item.tpl)
        item_stack_size = item_template.props.StackMaxSize

        bought_items_list: List[BoughtItems] = []

        while count:
            stack_size = min(count, item_stack_size)
            count -= stack_size
            item: Item = base_item.copy(deep=True)
            item.upd.StackObjectsCount = 1
            children_items: List[Item] = [
                child.copy(deep=True)
                for child in self.inventory.iter_item_children_recursively(base_item)
            ]

            all_items = children_items + [item]
            regenerate_items_ids(all_items)
            for item in all_items:
                item.upd.UnlimitedCount = False

            item.upd = ItemUpd(StackObjectsCount=stack_size)
            bought_items_list.append(
                BoughtItems(item=item, children_items=children_items)
            )

        return bought_items_list
