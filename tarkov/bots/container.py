from dependency_injector import containers, providers

from server import db_dir
from tarkov.bots import BotGenerator, BotGeneratorPreset


class BotContainer(containers.DeclarativeContainer):
    preset = providers.Factory(
        BotGeneratorPreset,
        database_dir=db_dir,
    )
    bot_generator = providers.Factory(
        BotGenerator,
        preset_factory=preset.provider,
    )
