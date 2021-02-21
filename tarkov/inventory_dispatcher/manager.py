from typing import Dict, Iterable, List, TYPE_CHECKING

from pydantic import Field

import tarkov.inventory_dispatcher.dispatchers.fleamarket
import tarkov.inventory_dispatcher.dispatchers.hideout
import tarkov.inventory_dispatcher.dispatchers.inventory
import tarkov.inventory_dispatcher.dispatchers.quests
import tarkov.inventory_dispatcher.dispatchers.trading
from server import logger
from tarkov.inventory import PlayerInventory
from tarkov.inventory.models import Item
from tarkov.models import Base
from tarkov.profile import Profile


if TYPE_CHECKING:
    # pylint: disable=unused-import
    from tarkov.inventory_dispatcher.dispatchers import Dispatcher


class DispatcherResponseItems(Base):
    new: List[Item] = Field(default_factory=list)
    change: List[Item] = Field(default_factory=list)
    del_: List[Item] = Field(default_factory=list, alias="del")


class DispatcherResponse(Base):
    items: DispatcherResponseItems = Field(default_factory=DispatcherResponseItems)
    badRequest: list = Field(default_factory=list)
    quests: list = Field(default_factory=list)
    ragFairOffers: list = Field(default_factory=list)
    builds: list = Field(default_factory=list)
    currentSalesSums: Dict[str, int] = Field(default_factory=dict)

    def append_error(self, title: str, message: str) -> None:
        self.badRequest.append(
            {
                "index": len(self.badRequest),
                "err": title,
                "errmsg": message,
            }
        )


class DispatcherManager:
    profile: Profile
    inventory: PlayerInventory

    response: DispatcherResponse

    dispatchers: Iterable["Dispatcher"]

    def __init__(self, profile: Profile):
        self.profile: Profile = profile

        self.response: DispatcherResponse = DispatcherResponse()

    def __make_dispatchers(self) -> None:
        self.dispatchers = (
            tarkov.inventory_dispatcher.dispatchers.inventory.InventoryDispatcher(self),
            tarkov.inventory_dispatcher.dispatchers.hideout.HideoutDispatcher(self),
            tarkov.inventory_dispatcher.dispatchers.trading.TradingDispatcher(self),
            tarkov.inventory_dispatcher.dispatchers.quests.QuestDispatcher(self),
            tarkov.inventory_dispatcher.dispatchers.fleamarket.FleaMarketDispatcher(self),
        )

    def dispatch(self, request_data: List[dict]) -> DispatcherResponse:
        with self.profile:
            self.inventory = self.profile.inventory
            self.__make_dispatchers()

            actions: List[dict] = request_data

            for action in actions:
                logger.debug(action)
                for dispatcher in self.dispatchers:
                    try:
                        dispatcher.dispatch(action)
                        logger.debug(f"Action was dispatched in {dispatcher.__class__.__name__}")
                        break
                    except NotImplementedError:
                        pass
                else:
                    raise NotImplementedError(f"Action {action} not implemented in any of the dispatchers")

        return self.response
