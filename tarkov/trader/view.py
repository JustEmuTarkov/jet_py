from __future__ import annotations

from typing import Iterable, List, TYPE_CHECKING

from tarkov.trader.interfaces import BaseTraderView

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory.models import Item
    from tarkov.inventory.repositories import ItemTemplatesRepository
    from tarkov.quests.models import QuestStatus
    from tarkov.trader.models import TraderBase, TraderStanding
    from tarkov.trader.trader import Trader
    from tarkov.profile.profile import Profile


class TraderView(BaseTraderView):
    def __init__(
        self,
        insurance_price_multiplier: float,
        trader: Trader,
        player_profile: Profile,
        templates_repository: ItemTemplatesRepository,
    ):
        self.__insurance_price_multiplier = insurance_price_multiplier

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
        """
        Calculates insurance price of given items based on their total price, current standing and insurance config.
        """
        total_price: float = sum(
            self.__templates_repository.get_template(item).props.CreditsPrice
            for item in items
        )
        total_price *= self.__insurance_price_multiplier
        total_price -= total_price * min(self.standing.current_standing, 0.5)
        return int(total_price)

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
