from dependency_injector import containers, providers

from server import db_dir
from tarkov.quests.repositories import QuestsRepository


class QuestsContainer(containers.DeclarativeContainer):
    repository: providers.Provider[QuestsRepository] = providers.Singleton(
        QuestsRepository, quests_path=db_dir.joinpath("quests", "all.json")
    )
