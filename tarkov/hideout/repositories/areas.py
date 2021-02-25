from typing import Dict, List

import pydantic
import ujson
from pydantic import Field

from server import db_dir
from tarkov.models import Base


class HideoutAreaTemplate(Base):
    id: str = Field(alias="_id")
    type: int
    enabled: bool
    needsFuel: bool
    takeFromSlotLocked: bool
    stages: Dict[str, dict]


class HideoutAreasRepository:
    areas: List[HideoutAreaTemplate]

    def __init__(self, areas: List[dict]):
        self.areas = pydantic.parse_obj_as(List[HideoutAreaTemplate], areas)


areas = HideoutAreasRepository(
    areas=[ujson.load(path.open()) for path in db_dir.joinpath("hideout", "areas").glob("*.json")]
)
