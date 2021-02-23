from asyncio import Lock
from collections import defaultdict
from typing import AsyncIterable, Dict

from fastapi.params import Cookie

from server import logger
from tarkov.profile import Profile

locks: Dict[str, Lock] = defaultdict(Lock)

profiles: Dict[str, Profile] = {}


async def with_profile(
    profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> AsyncIterable[Profile]:
    async with locks[profile_id]:
        if profile_id not in profiles:
            # Create profile instance if it doesn't exists
            profiles[profile_id] = Profile(profile_id)
            profiles[profile_id].read()

        try:
            yield profiles[profile_id]
            # After completing request write profile if everything is ok
            profiles[profile_id].write()

        except Exception as error:
            # Else read it again from filesystem
            profiles[profile_id].read()
            logger.exception(error)
            raise
