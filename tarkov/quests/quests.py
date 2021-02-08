import time
from typing import Dict, List, Tuple

import tarkov.profile as profile_
from tarkov import inventory
from tarkov.inventory import Item
from .models import QuestRewardItem
from .repositories import quests_repository


class Quests:
    profile: 'profile_.Profile'
    data: List[dict]

    def __init__(
            self,
            profile: 'profile_.Profile',
    ):
        self.profile: profile_.Profile = profile
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

    def handover_items(self, quest_id: str, condition_id: str, items: Dict[inventory.ItemId, int]) \
            -> Tuple[List[inventory.Item], List[inventory.Item]]:

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

    def get_quest_reward(self, quest_id: str) -> Tuple[List[Item], List[Item]]:
        quest_template = quests_repository.get_quest_template(quest_id)
        rewards = quest_template.rewards.Success

        for reward in rewards:
            if isinstance(reward, QuestRewardItem):
                pass

        return [], []
