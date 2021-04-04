from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers
from dependency_injector.providers import Dependency  # pylint: disable=no-name-in-module

from tarkov.fleamarket.fleamarket import FleaMarket
from tarkov.fleamarket.offer_generator import OfferGenerator
from tarkov.fleamarket.views import FleaMarketView

if TYPE_CHECKING:
    from tarkov.config import FleaMarketConfig
    from tarkov.inventory.repositories import ItemTemplatesRepository
    from tarkov.globals_.repository import GlobalsRepository
    from tarkov.inventory.factories import ItemFactory


class FleaMarketContainer(containers.DeclarativeContainer):
    flea_config: Dependency[FleaMarketConfig] = providers.Dependency()
    templates_repository: Dependency[ItemTemplatesRepository] = providers.Dependency()
    globals_repository: Dependency[GlobalsRepository] = providers.Dependency()
    item_factory: Dependency[ItemFactory] = providers.Dependency()

    generator: providers.Provider[OfferGenerator] = providers.Singleton(
        OfferGenerator,
        config=flea_config,
        templates_repository=templates_repository,
        globals_repository=globals_repository,
        item_factory=item_factory,
    )

    view: providers.Provider[FleaMarketView] = providers.Factory(
        FleaMarketView,
        templates_repository=templates_repository,
    )

    market: providers.Provider[FleaMarket] = providers.Singleton(
        FleaMarket,
        offer_generator=generator,
        flea_view_factory=view.provider,
    )
