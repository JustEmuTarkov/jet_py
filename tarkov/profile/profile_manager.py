from __future__ import annotations

from asyncio import Lock
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.profile.profile import Profile


class ProfileManager:
    def __init__(
        self,
        profiles_dir: str,
        profile_factory: Callable[..., Profile],
    ) -> None:
        self.__profiles_dir = profiles_dir
        self.__profile_factory = profile_factory

        self.locks: Dict[str, Lock] = defaultdict(Lock)
        self.profiles: Dict[str, Profile] = {}

    def get_profile(self, profile_id: str) -> Profile:
        if profile_id not in self.profiles:
            profile = self.__profile_factory(
                profile_dir=Path(self.__profiles_dir).joinpath(profile_id),
                profile_id=profile_id,
            )
            profile.read()
            self.profiles[profile_id] = profile

        return self.profiles[profile_id]

    def save_profile_task(self, profile: Profile) -> None:
        assert self.locks[profile.profile_id].locked()
        profile.write()
