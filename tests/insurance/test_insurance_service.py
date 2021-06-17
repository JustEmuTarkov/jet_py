from tarkov.insurance.interfaces import IInsuranceService
from tarkov.inventory.models import Item
from tarkov.profile.profile import Profile
from tarkov.trader.models import ItemInsurance, TraderType


def test_insurance_service_exists(
    insurance_service
):
    assert insurance_service


def test_is_item_insured_if_insurance_does_not_exists(
    insurance_service: IInsuranceService,
    profile: Profile,
    item,
):
    assert not insurance_service.is_item_insured(item=item, profile=profile)


def test_is_item_insured_if_insurance_exists(
    insurance_service: IInsuranceService,
    profile: Profile,
    item,
):
    profile.pmc.InsuredItems.append(ItemInsurance(item_id=item.id, trader_id=""))
    assert insurance_service.is_item_insured(item=item, profile=profile)


def test_can_insure_item(
    insurance_service: IInsuranceService,
    profile: Profile,
    item,
):
    item = Item(id="Item Id", tpl="Template Id", slot_id=None)
    profile.add_insurance(item=item, trader=TraderType.Prapor)
    assert insurance_service.is_item_insured(item=item, profile=profile)
