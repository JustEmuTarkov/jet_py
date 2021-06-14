from __future__ import annotations

import abc
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from tarkov.inventory.models import Item
    from tarkov.offraid.models import OffraidProfile
    from tarkov.profile.profile import Profile
    from tarkov.trader.models import ItemInsurance
    from tarkov.trader.types import TraderId


class IInsuranceService(abc.ABC):
    @abc.abstractmethod
    def is_item_insured(self, item: Item, profile: Profile) -> bool: ...

    @abc.abstractmethod
    def insurance_info(self, item: Item, profile: Profile) -> ItemInsurance: ...

    @abc.abstractmethod
    def get_insurance(
        self,
        profile: Profile,
        offraid_profile: OffraidProfile,
        is_alive: bool,
    ) -> Dict[TraderId, List[Item]]: ...

    @abc.abstractmethod
    def send_insurance_mail(
        self,
        items: List[Item],
        trader_id: TraderId,
        profile: Profile
    ) -> None: ...
