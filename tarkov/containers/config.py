from dependency_injector import containers, providers

from tarkov.config import BotGenerationConfig, FleaMarketConfig


class ConfigContainer(containers.DeclarativeContainer):
    flea_market = providers.Singleton(
        FleaMarketConfig,
    )

    bot_generation = providers.Singleton(BotGenerationConfig)
