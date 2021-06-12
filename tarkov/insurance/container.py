from dependency_injector import containers, providers

from tarkov.offraid.services import OffraidSaveService
from tarkov.trader.manager import TraderManager
from .interfaces import IInsuranceService
from .services import _InsuranceService
from ..inventory.repositories import ItemTemplatesRepository


class InsuranceContainer(containers.DeclarativeContainer):
    trader_manager = providers.Dependency(instance_of=TraderManager)
    offraid_service = providers.Dependency(instance_of=OffraidSaveService)
    templates_repository = providers.Dependency(instance_of=ItemTemplatesRepository)

    service: providers.Provider[IInsuranceService] = providers.Factory(
        _InsuranceService,
        trader_manager=trader_manager,
        offraid_service=offraid_service,
        templates_repository=templates_repository,
    )
