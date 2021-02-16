from server import root_dir
from tarkov.models import BaseConfig

config_dir = root_dir.joinpath('config')
config_dir.mkdir(parents=True, exist_ok=True)


class FleaMarketConfig(BaseConfig):
    __config_path__ = config_dir.joinpath('flea_market.yaml')

    offers_amount: int = 7500
    percentile_high: float = 0.98
    percentile_low: float = 0.2


flea_market = FleaMarketConfig.load()
