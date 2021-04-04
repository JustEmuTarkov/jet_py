from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from tarkov.fleamarket.fleamarket import FleaMarket
from tarkov.fleamarket.offer_generator import OfferGenerator
from tarkov.fleamarket.views import FleaMarketView

if TYPE_CHECKING:
    from tarkov.config import FleaMarketConfig


class FleaMarketContainer(containers.DeclarativeContainer):
    flea_config: FleaMarketConfig = providers.Dependency()
    templates_repository = providers.Dependency()
    globals_repository = providers.Dependency()
    item_factory = providers.Dependency()

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
