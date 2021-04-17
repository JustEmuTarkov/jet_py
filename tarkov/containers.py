from dependency_injector import containers, providers
from dependency_injector.providers import (
    Dependency,
)  # pylint: disable=no-name-in-module

from tarkov.globals_.repository import GlobalsRepository
from tarkov.inventory.factories import ItemFactory
from tarkov.inventory.repositories import ItemTemplatesRepository
from . import config


class ConfigContainer(containers.DeclarativeContainer):
    flea_market = providers.Singleton(
        config.FleaMarketConfig.load,
    )

    bot_generation = providers.Singleton(config.BotGenerationConfig.load)
    traders = providers.Singleton(config.TradersConfig.load)


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
