from dependency_injector import containers, providers

from tarkov.inventory import ItemTemplatesRepository


class Container(containers.DeclarativeContainer):
    templates_repository = providers.Singleton(ItemTemplatesRepository)
