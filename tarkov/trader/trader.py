from __future__ import annotations

import random
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Callable, Dict, Final, Iterable, List, Protocol, TYPE_CHECKING

import pydantic

import server.app
from server import db_dir
from tarkov.config import TradersConfig
from tarkov.inventory.helpers import regenerate_items_ids
from tarkov.inventory.implementations import SimpleInventory
from tarkov.inventory.inventory import ImmutableInventory
from tarkov.inventory.models import Item, ItemUpd
from tarkov.inventory.repositories import ItemTemplatesRepository
from tarkov.inventory.types import CurrencyEnum, ItemId, TemplateId
from tarkov.quests.models import QuestStatus
from tarkov.repositories.categories import category_repository
from tarkov.trader.models import (
    BarterScheme,
    BarterSchemeEntry,
    BoughtItems,
    Price,
    QuestAssort,
    TraderBase,
    TraderStanding,
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
        return self.__view_factory(self, player_profile)

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


class BaseTraderView(Protocol):
    barter_scheme: BarterScheme
    loyal_level_items: Dict[str, int]
    quest_assort: QuestAssort

    @property
    @abstractmethod
    def assort(self) -> List[Item]:
        ...

    @property
    @abstractmethod
    def standing(self) -> TraderStanding:
        ...

    @property
    @abstractmethod
    def base(self) -> TraderBase:
        ...

    def insurance_price(self, items: Iterable[Item]) -> int:
        ...


class TraderView(BaseTraderView):
    def __init__(
        self,
        trader: Trader,
        player_profile: Profile,
        templates_repository: ItemTemplatesRepository,
    ):
        self.__trader = trader
        self.__profile = player_profile
        self.__templates_repository = templates_repository

        self.barter_scheme = self.__trader.barter_scheme
        self.loyal_level_items = self.__trader.loyal_level_items
        self.quest_assort = self.__trader.quest_assort

    @property
    def assort(self) -> List[Item]:
        return self.__trader_assort()

    @property
    def standing(self) -> TraderStanding:
        trader_type = self.__trader.type
        if trader_type.value not in self.__profile.pmc.TraderStandings:
            standing_copy: TraderStanding = self.__trader.base.loyalty.copy(deep=True)
            self.__profile.pmc.TraderStandings[
                trader_type.value
            ] = TraderStanding.parse_obj(standing_copy)

        return self.__profile.pmc.TraderStandings[trader_type.value]

    @property
    def base(self) -> TraderBase:
        trader_base = self.__trader.base.copy(deep=True)
        trader_base.loyalty = self.standing
        return trader_base

    def insurance_price(self, items: Iterable[Item]) -> int:
        price: float = 0
        standing = self.standing.current_standing
        for item in items:
            item_price = (
                self.__templates_repository.get_template(item).props.CreditsPrice * 0.1
            )
            item_price -= item_price * min(standing, 0.5)
            price += item_price

        return int(price)

    @property
    def __trader_items(self) -> Iterable[Item]:
        return self.__trader.inventory.items.values()

    def __trader_assort(self) -> List[Item]:
        def filter_quest_assort(item: Item) -> bool:
            if item.id not in self.quest_assort.success:
                return True

            quest_id = self.quest_assort.success[item.id]
            try:
                quest = self.__profile.quests.get_quest(quest_id)
            except KeyError:
                return False
            return quest.status == QuestStatus.Success

        def filter_loyal_level(item: Item) -> bool:
            if item.id not in self.loyal_level_items:
                return True

            required_standing = self.loyal_level_items[item.id]
            return self.standing.current_level >= required_standing

        # Filter items that require quest completion
        items = filter(filter_quest_assort, self.__trader_items)

        # Filter items that require loyalty level
        items = filter(filter_loyal_level, items)

        assort = {item.id: item for item in items}

        # Remove orphan items from assort
        while True:
            assort_size = len(assort)
            assort = {
                item.id: item
                for item in assort.values()
                if item.parent_id in assort or item.slot_id == "hideout"
            }
            if len(assort) == assort_size:
                break

        return list(assort.values())


class TraderInventory(ImmutableInventory):
    def __init__(self, trader: Trader):
        super().__init__()
        self.trader = trader
        self.__items = {
            item.id: item
            for item in pydantic.parse_file_as(
                List[Item],
                self.trader.path.joinpath("items.json"),
            )
        }

    @property
    def items(self) -> Dict[ItemId, Item]:
        return self.__items
