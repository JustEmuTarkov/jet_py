from typing import List

import pydantic
import ujson
from pydantic import Field

from server import db_dir
from tarkov.hideout.models import HideoutAreaType
from tarkov.inventory.types import TemplateId
from tarkov.models import Base


class HideoutProductionModel(Base):
    id: str = Field(alias="_id")
    areaType: HideoutAreaType
    requirements: List[dict]
    continuous: bool
    productionTime: int
    endProduct: TemplateId
    count: int
    productionLimitCount: int


class HideoutProductionRepository:
    production: List[HideoutProductionModel]

    def __init__(self, production: List[dict]):
        self.production = pydantic.parse_obj_as(List[HideoutProductionModel], production)

    def view(self) -> List[dict]:
        return [p.dict() for p in self.production]


production = HideoutProductionRepository(
    production=[ujson.load(path.open()) for path in db_dir.joinpath("hideout", "production").glob("*.json")]
)
