import pydantic
from pydantic import Field

from .models import OffraidHealth, OffraidProfile


class OffraidSaveRequest(pydantic.BaseModel):
    exit: str
    is_player_scav: bool = Field(alias="isPlayerScav")
    health: OffraidHealth
    profile: OffraidProfile
