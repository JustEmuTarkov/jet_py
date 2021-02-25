import ujson

from server import db_dir
from tarkov.models import Base


class HideoutSettingsModel(Base):
    generatorSpeedWithoutFuel: float
    generatorFuelFlowRate: float
    airFilterUnitFlowRate: float
    gpuBoostRate: float


settings = HideoutSettingsModel.parse_file(db_dir.joinpath("hideout", "settings.json"))
