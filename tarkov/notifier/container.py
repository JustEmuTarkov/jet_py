from dependency_injector import containers, providers

from tarkov.notifier.notifier import NotifierService


class NotifierContainer(containers.DeclarativeContainer):
    service: providers.Provider[NotifierService] = providers.Singleton(NotifierService)
