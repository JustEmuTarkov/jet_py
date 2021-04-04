from pathlib import Path
from typing import Dict

import ujson

from tarkov.exceptions import NotFoundError
from tarkov.quests.models import QuestTemplate


class QuestsRepository:
    __quests: Dict[str, QuestTemplate]

    def __init__(self, quests_path: Path):
        quests = ujson.load(quests_path.open(encoding="utf8"))
        self.__quests = {quest.id: quest for quest in map(QuestTemplate.parse_obj, quests)}

    def get_quest_template(self, quest_id: str) -> QuestTemplate:
        try:
            return self.__quests[quest_id]
        except KeyError as e:
            raise NotFoundError(f"Quest template with id {quest_id} was not found") from e
