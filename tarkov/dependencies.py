from __future__ import annotations

from asyncio import Lock
from collections import defaultdict
from typing import AsyncIterable, Dict, TYPE_CHECKING

from fastapi import BackgroundTasks
from fastapi.params import Cookie

from server import logger

if TYPE_CHECKING:
    from tarkov.profile.profile import Profile


class ProfileManager:
    def __init__(self) -> None:
        self.locks: Dict[str, Lock] = defaultdict(Lock)
        self.profiles: Dict[str, Profile] = {}

    def get_profile(self, profile_id: str) -> Profile:
        from tarkov.profile.profile import Profile

        if profile_id not in self.profiles:
            profile = Profile(profile_id)
            profile.read()
            self.profiles[profile_id] = profile

        return self.profiles[profile_id]

    def _save_profile_task(self, profile: Profile) -> None:
        assert self.locks[profile.profile_id].locked()
        profile.write()

    def has(self, profile_id: str) -> bool:
        return profile_id in self.profiles

    async def with_profile(
        self,
        background_tasks: BackgroundTasks,
        profile_id: str = Cookie(..., alias="PHPSESSID"),
    ) -> AsyncIterable[Profile]:
        """
        Provides a Profile instance and saves it after request using background task
        Should be only used as a dependency for fastapi routes
        """
        async with self.locks[profile_id]:
            profile = self.get_profile(profile_id)
            try:
                background_tasks.add_task(self._save_profile_task, profile)
                profile.update()
                yield profile

            except Exception as error:
                # Else read it again from filesystem
                profile.read()
                logger.exception(error)
                raise

    async def with_profile_readonly(
        self,
        profile_id: str = Cookie(..., alias="PHPSESSID"),
    ) -> AsyncIterable[Profile]:
        """
        Provides a Profile instance
        Should work the same way as with_profile method but it won't save the profile
        """
        async with self.locks[profile_id]:
            profile = self.get_profile(profile_id)
            try:
                yield profile
            except Exception as error:
                profile.read()
                logger.exception(error)
                raise


profile_manager = ProfileManager()
