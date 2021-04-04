from dependency_injector import containers, providers
from dependency_injector.providers import Dependency

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


class ItemsContainer(containers.DeclarativeContainer):
    templates_repository: Dependency[ItemTemplatesRepository] = providers.Dependency()
    globals_repository: Dependency[GlobalsRepository] = providers.Dependency()

    factory = providers.Singleton(
        ItemFactory,
        templates_repository=templates_repository,
        globals_repository=globals_repository,
    )
