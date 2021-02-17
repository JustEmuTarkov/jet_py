from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Generic, Optional, Type, TypeVar

import pydantic
import yaml
from pydantic import Extra, ValidationError
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


ConfigType = TypeVar("ConfigType", bound="BaseConfig")


class BaseConfig(pydantic.BaseModel):
    __config_path__: ClassVar[Path]

    class Config:
        extra = Extra.forbid
        use_enum_values = True
        validate_all = True
        allow_mutation = False

    @classmethod
    def load(cls: Type[ConfigType], path: Path = None, auto_create=True) -> ConfigType:
        path = path or cls.__config_path__
        if not path.exists():
            if auto_create:
                try:
                    config = cls()
                    if not path.parent.exists():
                        path.parent.mkdir(parents=True, exist_ok=True)
                    yaml.safe_dump(config.dict(), path.open(mode="w", encoding="utf8"))
                except ValidationError as error:
                    raise ValueError(f"Config on {path} does not exists.") from error

        with path.open(encoding="utf8") as file:
            config = yaml.safe_load(file)

        return cls.parse_obj(config)


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
