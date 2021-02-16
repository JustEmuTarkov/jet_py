from typing import Any, Generic, Optional, TypeVar

import pydantic
from pydantic import Extra
from pydantic.generics import GenericModel


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

    def json(
        self,
        *args,
        indent=4,
        **kwargs,
    ) -> str:
        # pylint: disable=useless-super-delegation
        return super().json(*args, indent=indent, **kwargs)


ResponseType = TypeVar("ResponseType")


class TarkovSuccessResponse(GenericModel, Generic[ResponseType]):
    err: int = 0
    errmsg: Optional[str] = None
    data: Optional[ResponseType] = None


class TarkovErrorResponse(GenericModel, Generic[ResponseType]):
    err: int = True
    errmsg: Optional[str]
    data: Any = None

    @staticmethod
    def profile_id_is_none() -> "TarkovErrorResponse":
        return TarkovErrorResponse(errmsg="Profile id is None")
