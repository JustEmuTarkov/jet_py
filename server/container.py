from typing import cast

from dependency_injector import containers, providers

from tarkov.containers import ConfigContainer, ItemsContainer, RepositoriesContainer
from tarkov.fleamarket.container import FleaMarketContainer
from tarkov.insurance.container import InsuranceContainer
from tarkov.launcher.container import LauncherContainer
from tarkov.mail.container import MailContainer
from tarkov.notifier.container import NotifierContainer
from tarkov.offraid.container import OffraidContainer
from tarkov.profile.container import ProfileContainer
from tarkov.quests.container import QuestsContainer
from tarkov.trader.container import TraderContainer


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

    notifier: NotifierContainer = cast(
        NotifierContainer,
        providers.Container(NotifierContainer),
    )

    quests: QuestsContainer = cast(
        QuestsContainer,
        providers.Container(QuestsContainer),
    )

    mail: MailContainer = cast(
        MailContainer,
        providers.Container(
            MailContainer,
            notifier_service=notifier.service,
        ),
    )

    launcher: LauncherContainer = cast(
        LauncherContainer, providers.Container(LauncherContainer)
    )

    profile: ProfileContainer = cast(
        ProfileContainer,
        providers.Container(
            ProfileContainer,
            account_service=launcher.account_service,
        ),
    )

    trader: TraderContainer = cast(
        TraderContainer,
        providers.Container(
            TraderContainer,
            templates_repository=repos.templates,
            config=config.traders,
        ),
    )

    offraid: OffraidContainer = providers.Container(OffraidContainer)
    insurance: InsuranceContainer = providers.Container(
        InsuranceContainer,
        trader_manager=trader.manager,
        offraid_service=offraid.service,
    )
