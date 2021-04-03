from dependency_injector import containers, providers

from tarkov.fleamarket.fleamarket import FleaMarket
from tarkov.fleamarket.offer_generator import OfferGenerator
from tarkov.fleamarket.views import FleaMarketView


class FleaMarketContainer(containers.DeclarativeContainer):
    generator: providers.Provider[OfferGenerator] = providers.Singleton(OfferGenerator)

    view: providers.Provider[FleaMarketView] = providers.Factory(
        FleaMarketView,
    )

    market: providers.Provider[FleaMarket] = providers.Singleton(
        FleaMarket,
        offer_generator=generator,
        flea_view_factory=view.provider,
    )
