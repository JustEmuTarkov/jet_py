import pydantic
from pydantic import Extra


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
