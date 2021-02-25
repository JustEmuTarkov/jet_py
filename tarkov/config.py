from pathlib import Path
from typing import ClassVar

from server import root_dir
from tarkov.models import BaseConfig

config_dir = root_dir.joinpath("config")
config_dir.mkdir(parents=True, exist_ok=True)


class FleaMarketConfig(BaseConfig):
    __config_path__: ClassVar[Path] = config_dir.joinpath("flea_market.yaml")

    offers_amount: int = 7500
    percentile_high: float = 0.98
    percentile_low: float = 0.2
    level_required: int = 10


class BotGenerationConfig(BaseConfig):
    __config_path__: ClassVar[Path] = config_dir.joinpath("bot_generation.yaml")

    scav_chance: float = 1
    bear_chance: float = 0.5
    usec_change: float = 0.5


flea_market = FleaMarketConfig.load()
bot_generation = BotGenerationConfig.load()
