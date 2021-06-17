from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers
from dependency_injector.providers import Dependency

from tarkov.hideout.main import Hideout
from tarkov.profile.encyclopedia import Encyclopedia
from tarkov.profile.profile import Profile
from tarkov.profile.profile_manager import ProfileManager
from tarkov.profile.service import ProfileService
from tarkov.quests.quests import Quests

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.launcher.accounts import AccountService
    from tarkov.inventory.repositories import ItemTemplatesRepository
    from tarkov.notifier.notifier import NotifierService
    from tarkov.inventory.factories import ItemFactory
    from tarkov.quests.repositories import QuestsRepository
    from tarkov.trader.manager import TraderManager


class ProfileContainer(containers.DeclarativeContainer):
    account_service: Dependency[AccountService] = providers.Dependency()
    templates_repository: Dependency[ItemTemplatesRepository] = providers.Dependency()
    notifier_service: Dependency[NotifierService] = providers.Dependency()
    item_factory: Dependency[ItemFactory] = providers.Dependency()
    quests_repository: Dependency[QuestsRepository] = providers.Dependency()
    trader_manager: Dependency[TraderManager] = providers.Dependency()

    config = providers.Configuration(strict=True)

    encyclopedia = providers.Factory(Encyclopedia, templates_repository=templates_repository)
    hideout = providers.Factory(Hideout, item_factory=item_factory)
    quests = providers.Factory(
        Quests,
        quests_repository=quests_repository,
        templates_repository=templates_repository,
        trader_manager=trader_manager,
    )
    profile = providers.Factory(
        Profile,
        encyclopedia_factory=encyclopedia.provider,
        hideout_factory=hideout.provider,
        quests_factory=quests.provider,
        notifier_service=notifier_service,
    )

    manager = providers.Singleton(
        ProfileManager,
        profile_factory=profile.provider,
        profiles_dir=config.profiles_dir,
    )

    service = providers.Singleton(
        ProfileService,
        account_service=account_service,
        profile_manager=manager,
    )
