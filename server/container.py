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
    config = providers.Container(ConfigContainer)
    repos = providers.Container(RepositoriesContainer)

    items = providers.Container(
        ItemsContainer,
        globals_repository=repos.globals,
        templates_repository=repos.templates
    )

    flea = providers.Container(
        FleaMarketContainer,
        globals_repository=repos.globals,
        templates_repository=repos.templates,
        flea_config=config.flea_market,
        item_factory=items.factory,
    )

    notifier = providers.Container(NotifierContainer)

    quests = providers.Container(QuestsContainer)

    mail = providers.Container(
        MailContainer,
        notifier_service=notifier.service,
    )

    launcher = providers.Container(LauncherContainer)

    profile = providers.Container(
        ProfileContainer,
        account_service=launcher.account_service,
    )

    trader: TraderContainer = providers.Container(
        TraderContainer,
        templates_repository=repos.templates,
        config=config.traders,
    )

    offraid: OffraidContainer = providers.Container(OffraidContainer)
    insurance: InsuranceContainer = providers.Container(
        InsuranceContainer,
        trader_manager=trader.manager,
        offraid_service=offraid.service,
        templates_repository=items.templates_repository,
    )
