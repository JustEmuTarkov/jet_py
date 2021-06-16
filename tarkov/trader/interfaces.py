import abc
from typing import Dict, Iterable, List

from tarkov.inventory.models import Item
from tarkov.trader.models import BarterScheme, QuestAssort, TraderBase, TraderStanding


class BaseTraderView(abc.ABC):
    barter_scheme: BarterScheme
    loyal_level_items: Dict[str, int]
    quest_assort: QuestAssort

    @property
    @abc.abstractmethod
    def assort(self) -> List[Item]:
        ...

    @property
    @abc.abstractmethod
    def standing(self) -> TraderStanding:
        ...

    @property
    @abc.abstractmethod
    def base(self) -> TraderBase:
        ...

    def insurance_price(self, items: Iterable[Item]) -> int:
        ...
