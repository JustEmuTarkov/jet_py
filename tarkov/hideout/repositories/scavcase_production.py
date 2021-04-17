from typing import List

import pydantic
import ujson
from pydantic import Field

from server import db_dir
from tarkov.models import Base


class ScavcaseProductionModel(Base):
    id: str = Field(alias="_id")
    productionTime: int
    Requirements: List[dict]
    EndProducts: dict


class ScavcaseProductionRepository:
    production: List[ScavcaseProductionModel]

    def __init__(self, production: List[dict]):
        self.production = pydantic.parse_obj_as(
            List[ScavcaseProductionModel], production
        )


scavcase_production_repository = ScavcaseProductionRepository(
    production=[
        ujson.load(path.open())
        for path in db_dir.joinpath("hideout", "scavcase").glob("*.json")
    ]
)
