from pathlib import Path

import pydantic
from pydantic import Extra

from server.utils import atomic_write


class Base(pydantic.BaseModel):
    class Config:
        extra = Extra.forbid
        use_enum_values = True
        validate_assignment = True
        validate_all = True
        allow_population_by_field_name = True

    def dict(self, by_alias=True, exclude_unset=True, **kwargs) -> dict:
        return super().dict(
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            **kwargs,
        )

    def json(self, *args, indent=4, **kwargs, ) -> str:  # pylint: disable=useless-super-delegation
        return super().json(*args, indent=indent, **kwargs)

    def atomic_write(self, path: Path):
        atomic_write(path=path, str_=self)
