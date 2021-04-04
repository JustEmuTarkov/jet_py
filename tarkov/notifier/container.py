from dependency_injector import containers, providers

from tarkov.notifier.notifier import Notifier


class NotifierContainer(containers.DeclarativeContainer):
    notifier: providers.Provider[Notifier] = providers.Singleton(Notifier)
