from dependency_injector import containers, providers
from dependency_injector.providers import Dependency

from tarkov.config import TradersConfig
from tarkov.inventory.repositories import ItemTemplatesRepository
from tarkov.trader.manager import TraderManager
from tarkov.trader.trader import Trader, TraderView


class TraderContainer(containers.DeclarativeContainer):
    config: Dependency[TradersConfig] = providers.Dependency()
    templates_repository: Dependency[ItemTemplatesRepository] = providers.Dependency()

    trader_view = providers.Factory(
        TraderView,
        templates_repository=templates_repository,
    )

    trader = providers.Factory(
        Trader,
        templates_repository=templates_repository,
        trader_view_factory=trader_view.provider,
        config=config,
    )

    manager = providers.Singleton(
        TraderManager,
        trader_factory=trader.provider,
    )
