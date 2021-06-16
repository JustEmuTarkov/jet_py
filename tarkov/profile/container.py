from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from tarkov.profile.profile_manager import ProfileManager
from tarkov.profile.service import ProfileService

if TYPE_CHECKING:
    from tarkov.launcher.accounts import AccountService


class ProfileContainer(containers.DeclarativeContainer):
    account_service: providers.Dependency[AccountService] = providers.Dependency()

    manager = providers.Singleton(
        ProfileManager,
    )

    service = providers.Singleton(
        ProfileService,
        account_service=account_service,
        profile_manager=manager,
    )
