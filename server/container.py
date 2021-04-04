from typing import cast

from dependency_injector import containers, providers

from tarkov.containers import ConfigContainer, ItemsContainer, RepositoriesContainer
from tarkov.fleamarket.container import FleaMarketContainer
from tarkov.notifier.container import NotifierContainer
from tarkov.quests.container import QuestsContainer


class AppContainer(containers.DeclarativeContainer):
    # Code completion is better when using container types instead of say
    # Container[ConfigContainer]

    config: ConfigContainer = cast(
        ConfigContainer,
        providers.Container(
            ConfigContainer,
        ),
    )
    repos: RepositoriesContainer = cast(
        RepositoriesContainer,
        providers.Container(
            RepositoriesContainer,
        ),
    )

    items: ItemsContainer = cast(
        ItemsContainer,
        providers.Container(
            ItemsContainer,
            globals_repository=repos.globals,
            templates_repository=repos.templates,
        ),
    )

    flea: FleaMarketContainer = cast(
        FleaMarketContainer,
        providers.Container(
            FleaMarketContainer,
            globals_repository=repos.globals,
            templates_repository=repos.templates,
            flea_config=config.flea_market,
            item_factory=items.factory,
        ),
    )

    notifier: NotifierContainer = cast(NotifierContainer, providers.Container(NotifierContainer))

    quests: QuestsContainer = cast(QuestsContainer, providers.Container(QuestsContainer))
