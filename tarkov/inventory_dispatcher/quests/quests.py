from typing import TYPE_CHECKING

from tarkov.inventory_dispatcher.base import Dispatcher
from tarkov.inventory_dispatcher.models import ActionType
from .models import Accept, Complete, Handover

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.inventory_dispatcher import DispatcherManager


class QuestDispatcher(Dispatcher):
    def __init__(self, manager: "DispatcherManager") -> None:
        super().__init__(manager)
        self.dispatch_map = {
            ActionType.QuestAccept: self._quest_accept,
            ActionType.QuestHandover: self._quest_handover,
            ActionType.QuestComplete: self._quest_complete,
        }

    def _quest_accept(self, action: Accept) -> None:
        self.profile.quests.accept_quest(action.qid)

    def _quest_handover(self, action: Handover) -> None:
        items_dict = {item.id: item.count for item in action.items}
        removed, changed = self.profile.quests.handover_items(
            action.qid, action.conditionId, items_dict
        )

        self.response.items.change.extend(changed)
        self.response.items.del_.extend(removed)

    def _quest_complete(self, action: Complete) -> None:
        self.profile.quests.complete_quest(action.qid)
