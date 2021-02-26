from asyncio import Lock
from collections import defaultdict
from typing import AsyncIterable, Dict

from fastapi.params import Cookie
from fastapi import BackgroundTasks

from server import logger
from tarkov.profile import Profile

locks: Dict[str, Lock] = defaultdict(Lock)

profiles: Dict[str, Profile] = {}


async def save_profile_task(profile: Profile) -> None:
    assert locks[profile.profile_id].locked()
    profile.write()


async def with_profile(
    background_tasks: BackgroundTasks,
    profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> AsyncIterable[Profile]:
    if profile_id not in profiles:
        profiles[profile_id] = Profile(profile_id)
        profiles[profile_id].read()
    profile = profiles[profile_id]

    # After completing request flush profile to drive
    background_tasks.add_task(save_profile_task, profile)
    async with locks[profile_id]:
        try:
            profiles.update()
            yield profiles[profile_id]

        except Exception as error:
            # Else read it again from filesystem
            profiles[profile_id].read()
            logger.exception(error)
            raise
