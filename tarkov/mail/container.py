from dependency_injector import containers, providers
from dependency_injector.providers import Dependency  # pylint: disable=no-name-in-module

from tarkov.notifier.notifier import NotifierService


class MailContainer(containers.DeclarativeContainer):
    notifier_service: Dependency[NotifierService] = providers.Dependency()
