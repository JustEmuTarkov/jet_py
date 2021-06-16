from __future__ import annotations

from asyncio import Lock
from collections import defaultdict
from typing import Dict, TYPE_CHECKING

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

    def save_profile_task(self, profile: Profile) -> None:
        assert self.locks[profile.profile_id].locked()
        profile.write()

    def has(self, profile_id: str) -> bool:
        return profile_id in self.profiles
