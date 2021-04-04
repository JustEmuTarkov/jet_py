from dependency_injector import containers, providers

from tarkov.containers import ConfigContainer, ItemsContainer, RepositoriesContainer
from tarkov.fleamarket.container import FleaMarketContainer
from tarkov.notifier.container import NotifierContainer


class AppContainer(containers.DeclarativeContainer):
    config: ConfigContainer = providers.Container(
        ConfigContainer,
    )

    repos: RepositoriesContainer = providers.Container(
        RepositoriesContainer,
    )

    items: ItemsContainer = providers.Container(
        ItemsContainer,
        globals_repository=repos.globals,
        templates_repository=repos.templates,
    )

    flea: FleaMarketContainer = providers.Container(
        FleaMarketContainer,
        globals_repository=repos.globals,
        templates_repository=repos.templates,
        flea_config=config.flea_market,
        item_factory=items.factory,
    )

    notifier: NotifierContainer = providers.Container(
        NotifierContainer,
    )
