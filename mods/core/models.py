import pydantic
from pydantic import Extra


class Base(pydantic.BaseModel):
    class Config:
        extra = Extra.forbid
