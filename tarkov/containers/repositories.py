from dependency_injector import containers, providers

from tarkov.globals_.repository import GlobalsRepository
from tarkov.inventory.repositories import ItemTemplatesRepository


class RepositoriesContainer(containers.DeclarativeContainer):
    templates = providers.Singleton(ItemTemplatesRepository)
    globals = providers.Singleton(GlobalsRepository)
