from typing import Dict

import ujson

from server import db_dir
from tarkov.exceptions import NotFoundError
from tarkov.quests.models import QuestTemplate


class QuestsRepository:
    def __init__(self, quests: list):
        self.__quests: Dict[str, QuestTemplate] = {
            quest.id: quest for quest in map(lambda q: QuestTemplate(**q), quests)
        }

    def get_quest_template(self, quest_id: str) -> QuestTemplate:
        try:
            return self.__quests[quest_id]
        except KeyError as e:
            raise NotFoundError(f'Quest template with id {quest_id} was not found') from e


quests_repository = QuestsRepository(
    quests=ujson.load(db_dir.joinpath('quests', 'all.json').open(encoding='utf8'))
)
