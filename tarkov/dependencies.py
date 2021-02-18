from typing import Iterable

from fastapi.params import Cookie

from tarkov.profile import Profile


def with_profile(
    profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> Iterable[Profile]:
    with Profile(profile_id) as profile:
        yield profile
