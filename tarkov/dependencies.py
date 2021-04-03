from asyncio import Lock
from collections import defaultdict
from typing import AsyncIterable, Dict

from fastapi import BackgroundTasks
from fastapi.params import Cookie

from server import logger
from tarkov.profile import Profile


class ProfileManager:
    def __init__(self) -> None:
        self.locks: Dict[str, Lock] = defaultdict(Lock)
        self.profiles: Dict[str, Profile] = {}

    def get_or_create_profile(self, profile_id: str) -> Profile:
        if profile_id not in self.profiles:
            self.profiles[profile_id] = Profile(profile_id)
            self.profiles[profile_id].read()
        return self.profiles[profile_id]

    def _save_profile_task(self, profile: Profile) -> None:
        assert self.locks[profile.profile_id].locked()
        profile.write()

    async def with_profile(
        self,
        background_tasks: BackgroundTasks,
        profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
    ) -> AsyncIterable[Profile]:
        """
        Provides a Profile instance and saves it after request using background task
        Should be only used as a dependency for fastapi routes
        """
        async with self.locks[profile_id]:
            profile = self.get_or_create_profile(profile_id)
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
        profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
    ) -> AsyncIterable[Profile]:
        """
        Provides a Profile instance
        Should work the same way as with_profile method but it won't save the profile
        """
        async with self.locks[profile_id]:
            profile = self.get_or_create_profile(profile_id)
            try:
                yield profile
            except Exception as error:
                profile.read()
                logger.exception(error)
                raise


profile_manager = ProfileManager()
