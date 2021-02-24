from __future__ import annotations

import typing
from typing import Callable, Dict, TYPE_CHECKING

from tarkov.inventory_dispatcher.models import ActionType


if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile import Profile
    from tarkov.inventory import PlayerInventory
    from tarkov.inventory_dispatcher.manager import (
        DispatcherManager,
        DispatcherResponse,
    )


class Dispatcher:
    dispatch_map: Dict[ActionType, Callable]
    inventory: PlayerInventory
    profile: Profile
    response: DispatcherResponse

    def __init__(self, manager: "DispatcherManager"):
        self.manager = manager
        self.inventory = manager.inventory
        self.profile = manager.profile
        self.response = manager.response

    def dispatch(self, action: dict) -> None:
        action_type: ActionType = ActionType(action["Action"])

        try:
            method = self.dispatch_map[action_type]
        except KeyError as error:
            raise NotImplementedError(
                f"Action with type {action_type} not implemented in dispatcher {self.__class__}"
            ) from error

        types = typing.get_type_hints(method)
        model_type = types["action"]
        # noinspection PyArgumentList
        method(model_type(**action))  # type: ignore
