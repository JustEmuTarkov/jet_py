from asyncio import Lock
from collections import defaultdict
from typing import AsyncIterable, Dict

from fastapi.params import Cookie
from fastapi import BackgroundTasks

from server import logger
from tarkov.profile import Profile

locks: Dict[str, Lock] = defaultdict(Lock)

profiles: Dict[str, Profile] = {}


def save_profile_task(profile: Profile) -> None:
    assert locks[profile.profile_id].locked()
    profile.write()


def _get_or_create_profile(profile_id: str) -> Profile:
    if profile_id not in profiles:
        profiles[profile_id] = Profile(profile_id)
        profiles[profile_id].read()
    return profiles[profile_id]


async def with_profile(
    background_tasks: BackgroundTasks,
    profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> AsyncIterable[Profile]:
    async with locks[profile_id]:
        profile = _get_or_create_profile(profile_id)
        try:
            background_tasks.add_task(save_profile_task, profile)
            profile.update()
            yield profile

        except Exception as error:
            # Else read it again from filesystem
            profile.read()
            logger.exception(error)
            raise


async def with_profile_readonly(
    profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> AsyncIterable[Profile]:
    async with locks[profile_id]:
        profile = _get_or_create_profile(profile_id)
        try:
            yield profile
        except Exception as error:
            profile.read()
            logger.exception(error)
            raise
