from __future__ import annotations

import collections
import datetime
from typing import Dict, List, TYPE_CHECKING

from tarkov.mail.models import MailDialogueMessage, MailMessageItems, MailMessageType
from tarkov.offraid.services import OffraidSaveService
from tarkov.trader.models import TraderType
from . import exceptions, interfaces
from tarkov.inventory.prop_models import CompoundProps
from tarkov.inventory.repositories import ItemTemplatesRepository

if TYPE_CHECKING:
    from tarkov.inventory.models import Item
    from tarkov.offraid.models import OffraidProfile
    from tarkov.profile.profile import Profile
    from tarkov.trader.manager import TraderManager
    from tarkov.trader.models import ItemInsurance
    from tarkov.trader.types import TraderId


class _InsuredItemsProcessor:
    def __init__(
        self,
        insurance_service: _InsuranceService,
        templates_repository: ItemTemplatesRepository,
    ):
        self.__insurance_service = insurance_service
        self.__templates_repository = templates_repository

    def process(self, items: List[Item]) -> Dict[TraderId, List[Item]]:
        items = self._flatten_items(items)
        items = self._clean_orphan_items_properties(items)
        return self._group_items_by_insurer(items)

    def _flatten_items(self, items: List[Item]) -> List[Item]:
        """Takes out items from tactical vests and backpacks"""

        for item in items:
            tpl = self.__templates_repository.get_template(item=item)
            if isinstance(tpl, CompoundProps):
                item.parent_id = None
        return items

    def _clean_orphan_items_properties(self, items: List[Item]) -> List[Item]:
        """Cleans Item.parent_id, Item.location and Item.slot_id from orphan items"""

        for item in items:
            if any(item.parent_id == i.id for i in items):
                item.parent_id = None
                item.slot_id = None
                item.location = None
        return items

    def _group_items_by_insurer(self, items: List[Item], profile: Profile) -> Dict[TraderId, List[Item]]:
        item_groups: Dict[TraderId, List[Item]] = collections.defaultdict(list)
        for item in items:
            insurance_info = self.__insurance_service.insurance_info(item=item, profile=profile)
            item_groups[insurance_info.trader_id].append(item)
        return item_groups


class _InsuranceService(interfaces.IInsuranceService):
    def __init__(
        self,
        trader_manager: TraderManager,
        offraid_service: OffraidSaveService,
        templates_repository: ItemTemplatesRepository,
    ):
        self.__trader_manager = trader_manager
        self.__offraid_service = offraid_service
        self.__templates_repository = templates_repository
        self.__items_processor = _InsuredItemsProcessor(
            insurance_service=self,
            templates_repository=templates_repository,
        )

    def get_lost_insured_items(
        self,
        profile: Profile,
        offraid_profile: OffraidProfile,
    ) -> Dict[TraderId, List[Item]]:
        temp_ = self.__offraid_service.get_protected_items(raid_profile=offraid_profile)

        protected_items: List[Item] = []
        for item, children in temp_:
            protected_items.append(item)
            protected_items.extend(children)

        items = [
            i for i in offraid_profile.Inventory.items
            if i not in protected_items
            and self.is_item_insured(item=i, profile=profile)
        ]
        return self.__items_processor.process(items)

    def is_item_insured(self, item: Item, profile: Profile) -> bool:
        return any(
            insurance.item_id == item.id for insurance in profile.pmc.InsuredItems
        )

    def insurance_info(self, item: Item, profile: Profile) -> ItemInsurance:
        if not self.is_item_insured(item=item, profile=profile):
            raise exceptions.InsuranceNotFound
        return next(
            insurance
            for insurance in profile.pmc.InsuredItems
            if insurance.item_id == item.id
        )

    def send_insurance_mail(
        self,
        items: List[Item],
        trader_id: TraderId,
        profile: Profile
    ) -> None:
        trader = self.__trader_manager.get_trader(trader_type=TraderType(trader_id))
        insurance_storage_time = int(datetime.timedelta(hours=trader.base.insurance.max_storage_time).total_seconds())
        mail = profile.mail
        message = MailDialogueMessage(
            uid=trader_id,
            type=MailMessageType.InsuranceReturn.value,
            items=MailMessageItems.from_items(items=items),
            maxStorageTime=insurance_storage_time,
            templateId="5a8fd75188a45036844e0ae8",
            # Todo: Replace with actual date and time depending on message template_id
            systemData={"date": "Some date", "time": "Some Time"},
            hasRewards=True,
            rewardCollected=False,
        )
        mail.add_message(message=message)
