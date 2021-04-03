from dependency_injector import containers, providers

from tarkov.config import BotGenerationConfig, FleaMarketConfig
from tarkov.inventory import ItemTemplatesRepository


class Container(containers.DeclarativeContainer):
    templates_repository = providers.Singleton(ItemTemplatesRepository)


class ConfigContainer(containers.DeclarativeContainer):
    flea_market = providers.Singleton(
        FleaMarketConfig,
    )

    bot_generation = providers.Singleton(BotGenerationConfig)
