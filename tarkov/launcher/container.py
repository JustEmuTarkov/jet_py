from dependency_injector import containers, providers

from tarkov.launcher.accounts import AccountService


class LauncherContainer(containers.DeclarativeContainer):
    account_service = providers.Singleton(AccountService)
