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
    insurance_config = providers.Configuration()

    config: ConfigContainer = providers.Container(ConfigContainer)
    repos: RepositoriesContainer = providers.Container(RepositoriesContainer)

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

    notifier: NotifierContainer = providers.Container(NotifierContainer)

    quests: QuestsContainer = providers.Container(QuestsContainer)

    mail: MailContainer = providers.Container(
        MailContainer,
        notifier_service=notifier.service,
    )

    launcher: LauncherContainer = providers.Container(LauncherContainer)

    trader: TraderContainer = providers.Container(
        TraderContainer,
        templates_repository=repos.templates,
        config=config.traders,
        insurance_config=insurance_config,
    )

    profile: ProfileContainer = providers.Container(
        ProfileContainer,
        account_service=launcher.account_service,
        templates_repository=repos.templates,
        notifier_service=notifier.service,
        item_factory=items.factory,
        quests_repository=quests.repository,
        trader_manager=trader.manager,
    )

    offraid: OffraidContainer = providers.Container(OffraidContainer)
    insurance: InsuranceContainer = providers.Container(
        InsuranceContainer,
        config=insurance_config,
        trader_manager=trader.manager,
        offraid_service=offraid.service,
        templates_repository=items.templates_repository,
    )
