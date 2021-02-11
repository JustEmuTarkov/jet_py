import time
from typing import Dict, List, TYPE_CHECKING, Tuple

from pydantic import StrictInt

from tarkov import inventory
from tarkov.inventory import PlayerInventory, item_templates_repository
from tarkov.inventory.models import Item
from tarkov.lib.trader import TraderInventory, Traders
from tarkov.notifier.models import MailDialogueMessage, MailMessageItems
from .models import QuestMessageType, QuestRewardExperience, QuestRewardItem, QuestRewardTraderStanding
from .repositories import quests_repository

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile import Profile


class Quests:
    profile: 'Profile'
    data: List[dict]

    def __init__(self, profile: 'Profile', ):
        self.profile: 'Profile' = profile
        self.data = self.profile.quests_data

    def get_quest(self, quest_id: str):
        try:
            return next(quest for quest in self.data if quest['qid'] == quest_id)
        except StopIteration as e:
            raise KeyError from e

    def accept_quest(self, quest_id: str):
        # TODO: Create quest if it does not exist
        try:
            quest = self.get_quest(quest_id)
            if quest['status'] in ('Started', 'Success'):
                raise ValueError('Quest is already accepted')
        except KeyError:
            pass

        quest = self.get_quest(quest_id)
        quest['status'] = 'Started'
        quest['startTime'] = int(time.time())

    def handover_items(self, quest_id: str, condition_id: str, items: Dict[inventory.models.ItemId, int]) \
            -> Tuple[List[inventory.models.Item], List[inventory.models.Item]]:

        try:
            condition = self.profile.pmc_profile['BackendCounters'][condition_id]
        except KeyError:
            condition = {
                'id': condition_id,
                'qid': quest_id,
                'value': 0
            }
            self.profile.pmc_profile['BackendCounters'][condition_id] = condition

        removed_items = []
        changed_items = []
        for item_id, count in items.items():
            item = self.profile.inventory.get_item(item_id)

            if not self.profile.inventory.can_split(item) and count == 1:
                removed_items.append(item)
                self.profile.inventory.remove_item(item)
            else:
                changed_items.append(item)
                self.profile.inventory.simple_split_item(item=item, count=count)
                # removed_items.append(self.profile.inventory.split_item(item=item, count=count))

            condition['value'] += count

        return removed_items, changed_items

    @staticmethod
    def get_quest_reward(quest_id: str) -> Tuple[List[Item], List[Item]]:
        quest_template = quests_repository.get_quest_template(quest_id)
        rewards = quest_template.rewards.Success

        for reward in rewards:
            if isinstance(reward, QuestRewardItem):
                pass

        return [], []

    def complete_quest(self, quest_id: str):
        quest_template = quests_repository.get_quest_template(quest_id)

        reward_items: List[Item] = []
        for reward in quest_template.rewards.Success:
            if isinstance(reward, QuestRewardItem):
                for reward_item in reward.items:
                    item_template = item_templates_repository.get_template(reward_item)
                    stack_size: int = item_template.props.StackMaxSize

                    while reward_item.upd.StackObjectsCount > 0:
                        amount_to_split = min(reward_item.upd.StackObjectsCount, stack_size)
                        reward_items.append(PlayerInventory.simple_split_item(reward_item, amount_to_split))

            elif isinstance(reward, QuestRewardExperience):
                exp_amount: str = reward.value
                self.profile.receive_experience(int(exp_amount))

            elif isinstance(reward, QuestRewardTraderStanding):
                standing_change = float(reward.value)
                trader_id = reward.target

                trader = TraderInventory(Traders(trader_id), self.profile)
                standing = trader.standing
                standing['currentStanding'] += standing_change

            else:
                raise ValueError(f'Unknown reward: {reward.__class__.__name__} {reward}')

        message = MailDialogueMessage(
            uid=quest_template.traderId,
            type=StrictInt(QuestMessageType.questSuccess.value),
            templateId='5ab0f32686f7745dd409f56b',  # TODO: Right now this is a placeholder
            systemData={},
            items=MailMessageItems.from_items(reward_items),
            hasRewards=True,
        )
        self.profile.notifier.add_message(message)
