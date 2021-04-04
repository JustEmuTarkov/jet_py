from dependency_injector import containers, providers

from tarkov.config import BotGenerationConfig, FleaMarketConfig
from tarkov.globals_.repository import GlobalsRepository
from tarkov.inventory.factories import ItemFactory
from tarkov.inventory.repositories import ItemTemplatesRepository


class ConfigContainer(containers.DeclarativeContainer):
    flea_market = providers.Singleton(
        FleaMarketConfig,
    )

    bot_generation = providers.Singleton(BotGenerationConfig)


class RepositoriesContainer(containers.DeclarativeContainer):
    templates = providers.Singleton(ItemTemplatesRepository)
    globals = providers.Singleton(GlobalsRepository)


class Container(containers.DeclarativeContainer):
    item_factory = providers.Singleton(
        ItemFactory,
        templates_repository=RepositoriesContainer.templates,
        globals_repository=RepositoriesContainer.globals,
    )
