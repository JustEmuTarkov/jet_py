from dependency_injector import containers, providers

from tarkov.inventory.factories import ItemFactory


class Container(containers.DeclarativeContainer):
    item_factory = providers.Singleton(
        ItemFactory,
    )
