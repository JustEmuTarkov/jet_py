from asyncio import Lock
from collections import defaultdict
from typing import AsyncIterable, Dict

from fastapi.params import Cookie

from tarkov.profile import Profile

locks: Dict[str, Lock] = defaultdict(Lock)


async def with_profile(
    profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> AsyncIterable[Profile]:
    async with locks[profile_id]:
        with Profile(profile_id) as profile:
            yield profile
