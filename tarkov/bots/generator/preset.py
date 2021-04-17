from pathlib import Path

import ujson


class BotGeneratorPreset:
    def __init__(self, database_dir: Path, bot_role: str):
        bots_dir = database_dir.joinpath("bots", bot_role)

        self.generation: dict = ujson.load(
            bots_dir.joinpath("generation.json").open(encoding="utf8")
        )
        self.inventory: dict = ujson.load(
            bots_dir.joinpath("inventory.json").open(encoding="utf8")
        )
        self.chances: dict = ujson.load(
            bots_dir.joinpath("chances.json").open(encoding="utf8")
        )
        self.health: dict = ujson.load(
            bots_dir.joinpath("health.json").open(encoding="utf8")
        )
        self.appearance: dict = ujson.load(
            bots_dir.joinpath("appearance.json").open(encoding="utf8")
        )
