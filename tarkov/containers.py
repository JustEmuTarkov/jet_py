from dependency_injector import containers, providers

from tarkov.config import BotGenerationConfig, FleaMarketConfig
from tarkov.inventory import ItemTemplatesRepository


class RepositoriesContainer(containers.DeclarativeContainer):
    templates = providers.Singleton(ItemTemplatesRepository)


class ConfigContainer(containers.DeclarativeContainer):
    flea_market = providers.Singleton(
        FleaMarketConfig,
    )

    bot_generation = providers.Singleton(BotGenerationConfig)
