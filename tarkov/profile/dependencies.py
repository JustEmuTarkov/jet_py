from __future__ import annotations

from typing import AsyncIterable, TYPE_CHECKING

from fastapi import Cookie, Query, Request
from starlette.background import BackgroundTasks

from server import logger
from tarkov.profile.profile import Profile

if TYPE_CHECKING:
    from tarkov.profile.profile_manager import ProfileManager


async def with_profile(
    request: Request,
    background_tasks: BackgroundTasks,
    profile_id: str = Query(..., alias="PHPSESSID"),
) -> AsyncIterable[Profile]:
    """
    Provides a Profile instance and saves it after request using background task
    Should be only used as a dependency for fastapi routes
    """
    profile_manager: ProfileManager = request.app.container.profile.manager()
    async with profile_manager.locks[profile_id]:
        profile = profile_manager.get_profile(profile_id)
        try:
            background_tasks.add_task(profile_manager.save_profile_task, profile)
            profile.update()
            yield profile

        except Exception as error:
            # Else read it again from filesystem
            profile.read()
            logger.exception(error)
            raise


async def with_profile_readonly(
    request: Request,
    profile_id: str = Cookie(..., alias="PHPSESSID"),
) -> AsyncIterable[Profile]:
    """
    Provides a Profile instance
    Should work the same way as with_profile method but it won't save the profile
    """
    profile_manager: ProfileManager = request.app.container.profile.manager()

    async with profile_manager.locks[profile_id]:
        profile = profile_manager.get_profile(profile_id)
        try:
            yield profile
        except Exception as error:
            profile.read()
            logger.exception(error)
            raise
