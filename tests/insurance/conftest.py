import pytest
from dependency_injector.wiring import Provide, inject

from server.container import AppContainer
from tarkov.insurance.interfaces import IInsuranceService
from tarkov.inventory.models import Item


@pytest.fixture()
@inject
def insurance_service(
    insurance_service: IInsuranceService = Provide[AppContainer.insurance.service]
) -> IInsuranceService:
    return insurance_service


@pytest.fixture()
def item() -> Item:
    return Item(id="Item Id", tpl="Template Id", slot_id=None)
