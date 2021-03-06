from __future__ import annotations

import time
from typing import Dict, List, TYPE_CHECKING, Tuple

from dependency_injector.wiring import Provide, inject
from pydantic import StrictInt

import tarkov.inventory.types
from server.container import AppContainer
from tarkov import inventory
from tarkov.inventory.inventory import PlayerInventory
from tarkov.inventory.models import Item
from tarkov.mail.models import (
    MailDialogueMessage,
    MailMessageItems,
    MailMessageType,
)
from tarkov.profile.models import BackendCounter
from tarkov.trader.models import TraderType
from .models import (
    Quest,
    QuestRewardAssortUnlock,
    QuestRewardExperience,
    QuestRewardItem,
    QuestRewardTraderStanding,
    QuestStatus,
)
from .repositories import QuestsRepository
from tarkov.trader.manager import TraderManager

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile.profile import Profile
    from tarkov.inventory.repositories import ItemTemplatesRepository


class Quests:
    profile: "Profile"
    quests: List[Quest]

    @inject
    def __init__(
        self,
        profile: "Profile",
        quests_repository: QuestsRepository = Provide[AppContainer.quests.repository],
    ):
        self.__quests_repository = quests_repository

        self.profile: "Profile" = profile
        self.quests = self.profile.pmc.Quests

    def create_quest(self, quest_id: str) -> Quest:
        quest_template = self.__quests_repository.get_quest_template(quest_id)
        quest = Quest(
            quest_id=quest_template.id,
            started_at=0,
            status=QuestStatus.AvailableForStart,
        )
        self.quests.append(quest)
        return quest

    def get_quest(self, quest_id: str) -> Quest:
        try:
            return next(quest for quest in self.quests if quest.quest_id == quest_id)
        except StopIteration as e:
            raise KeyError from e

    def accept_quest(self, quest_id: str) -> None:
        # TODO: Create quest if it does not exist
        try:
            quest = self.get_quest(quest_id)
        except KeyError:
            quest = self.create_quest(quest_id)
        print(quest.status)
        # if quest.status != QuestStatus.AvailableForStart.value:
        #     raise ValueError("Quest is already accepted or locked")

        quest.status = QuestStatus.Started
        quest.started_at = int(time.time())

    def handover_items(
        self,
        quest_id: str,
        condition_id: str,
        items: Dict[tarkov.inventory.types.ItemId, int],
    ) -> Tuple[List[inventory.models.Item], List[inventory.models.Item]]:
        try:
            backend_counter = self.profile.pmc.BackendCounters[condition_id]
        except KeyError:
            backend_counter = BackendCounter(id=condition_id, qid=quest_id, value=0)
            self.profile.pmc.BackendCounters[condition_id] = backend_counter

        quest_template = self.__quests_repository.get_quest_template(quest_id)
        quest_condition = next(
            cond
            for cond in quest_template.conditions.AvailableForFinish
            if cond.props["id"] == condition_id
        )
        # Amount of items required for quest condition
        required_amount: int = int(quest_condition.props["value"])

        removed_items: List[Item] = []
        changed_items: List[Item] = []

        for item_id, count in items.items():
            if required_amount <= 0:
                break
            item = self.profile.inventory.get(item_id)
            # Amount that we will subtract from item stack
            amount_to_subtract = min(required_amount, count, item.upd.StackObjectsCount)

            if amount_to_subtract == item.upd.StackObjectsCount:
                removed_items.append(item.copy(deep=True))
                self.profile.inventory.remove_item(item)

            else:
                item.upd.StackObjectsCount -= amount_to_subtract
                changed_items.append(item.copy(deep=True))

            backend_counter.value += amount_to_subtract
            required_amount -= amount_to_subtract

        return removed_items, changed_items

    def get_quest_reward(self, quest_id: str) -> Tuple[List[Item], List[Item]]:
        quest_template = self.__quests_repository.get_quest_template(quest_id)
        rewards = quest_template.rewards.Success

        for reward in rewards:
            if isinstance(reward, QuestRewardItem):
                pass

        return [], []

    def complete_quest(
        self,
        quest_id: str,
        templates_repository: ItemTemplatesRepository = Provide[
            AppContainer.repos.templates
        ],
        trader_manager: TraderManager = Provide[AppContainer.trader.manager],
    ) -> None:
        quest_template = self.__quests_repository.get_quest_template(quest_id)
        quest = self.get_quest(quest_id)
        quest.status = QuestStatus.Success

        reward_items: List[Item] = []
        for reward in quest_template.rewards.Success:
            if isinstance(reward, QuestRewardItem):
                for reward_item in reward.items:
                    item_template = templates_repository.get_template(reward_item)
                    stack_size: int = item_template.props.StackMaxSize

                    while reward_item.upd.StackObjectsCount > 0:
                        amount_to_split = min(
                            reward_item.upd.StackObjectsCount, stack_size
                        )
                        reward_items.append(
                            PlayerInventory.simple_split_item(
                                reward_item, amount_to_split
                            )
                        )

            elif isinstance(reward, QuestRewardExperience):
                exp_amount: str = reward.value
                self.profile.receive_experience(int(exp_amount))

            elif isinstance(reward, QuestRewardTraderStanding):
                standing_change = float(reward.value)
                trader_id = reward.target

                trader = trader_manager.get_trader(TraderType(trader_id))
                trader_view = trader.view(player_profile=self.profile)
                standing = trader_view.standing
                standing.current_standing += standing_change

            elif isinstance(reward, QuestRewardAssortUnlock):
                # We're checking for quest assort when generating it for specific player
                pass

            else:
                raise ValueError(
                    f"Unknown reward: {reward.__class__.__name__} {reward}"
                )

        message = MailDialogueMessage(
            uid=quest_template.traderId,
            type=StrictInt(MailMessageType.QuestSuccess.value),
            templateId="5ab0f32686f7745dd409f56b",  # TODO: Right now this is a placeholder
            systemData={},
            items=MailMessageItems.from_items(reward_items),
            hasRewards=True,
        )
        self.profile.mail.add_message(message)
