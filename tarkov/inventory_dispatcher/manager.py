from typing import Dict, Iterable, List

import ujson
from flask import Request, request
from pydantic import Field

from server import logger
from tarkov.inventory import Item, PlayerInventory
from tarkov.models import Base
from tarkov.profile import Profile
from . import dispatchers
from .adapters import InventoryToRequestAdapter


class DispatcherResponseItems(Base):
    class Config:
        fields = {
            'del_': 'del'
        }

    new: List[Item] = Field(default_factory=list)
    change: List[Item] = Field(default_factory=list)
    del_: List[Item] = Field(default_factory=list)


class DispatcherResponse(Base):
    items: DispatcherResponseItems = Field(default_factory=DispatcherResponseItems)
    badRequest: list = Field(default_factory=list)
    quests: list = Field(default_factory=list)
    ragFairOffers: list = Field(default_factory=list)
    builds: list = Field(default_factory=list)
    currentSalesSums: Dict[str, int] = Field(default_factory=dict)


class DispatcherManager:
    profile: Profile
    inventory: PlayerInventory
    inventory_adapter: InventoryToRequestAdapter

    request: Request
    response: DispatcherResponse

    dispatchers: Iterable['dispatchers.Dispatcher']

    def __init__(self, session_id: str):
        self.profile: Profile = Profile(session_id)

        self.request = request
        self.response: DispatcherResponse = DispatcherResponse()

    def __make_dispatchers(self):
        self.dispatchers = (
            dispatchers.InventoryDispatcher(self),
            dispatchers.HideoutDispatcher(self),
            dispatchers.TradingDispatcher(self),
            dispatchers.QuestDispatcher(self),
        )

    def dispatch(self) -> DispatcherResponse:
        with self.profile:
            self.inventory = self.profile.inventory
            self.inventory_adapter = InventoryToRequestAdapter(self.inventory)
            self.__make_dispatchers()

            # request.data should be dict at this moment
            # noinspection PyTypeChecker
            actions: List[dict] = request.data['data']  # type: ignore

            for action in actions:
                logger.debug(ujson.dumps(action, indent=4))

                for dispatcher in self.dispatchers:
                    try:
                        dispatcher.dispatch(action)
                        logger.debug(f'Action was dispatched in {dispatcher.__class__.__name__}')
                        break
                    except NotImplementedError:
                        pass
                else:
                    raise NotImplementedError(f'Action {action} not implemented in any of the dispatchers')

        return self.response
