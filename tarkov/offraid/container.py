from dependency_injector import containers, providers

from tarkov.offraid.services import OffraidSaveService


class OffraidContainer(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)

    service: OffraidSaveService = providers.Factory(
        OffraidSaveService,
        protected_slots=config.protected_slots,
        retained_slots=config.retained_slots,
    )
