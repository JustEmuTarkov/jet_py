from __future__ import annotations

import json
import shutil
from typing import TYPE_CHECKING

import ujson

from server import db_dir, root_dir
from tarkov.dependencies import profile_manager

if TYPE_CHECKING:
    from tarkov.launcher.accounts import AccountService
    from tarkov.profile.models import ProfileModel


class ProfileService:
    def __init__(self, account_service: AccountService):
        self.__account_service = account_service

    def create_profile(
        self,
        nickname: str,
        side: str,
        profile_id: str,
    ) -> ProfileModel:
        from tarkov.profile.models import ProfileModel

        account = self.__account_service.get_account(profile_id)
        base_profile_dir = db_dir.joinpath("profile", account.edition)

        starting_outfit = ujson.load(
            base_profile_dir.joinpath("starting_outfit.json").open()
        )
        character = ujson.load(base_profile_dir.joinpath("character.json").open())

        character["Customization"] = starting_outfit[side.lower()]

        profile: ProfileModel = ProfileModel.parse_obj(character)

        profile.aid = f"{account.id}"
        profile.id = f"pmc{account.id}"
        profile.savage = f"scav{account.id}"

        profile.Info.Nickname = nickname
        profile.Info.LowerNickname = nickname.lower()
        profile.Info.Side = side.capitalize()
        profile.Info.Voice = f"{side.capitalize()}_1"

        profile_dir = root_dir.joinpath("resources", "profiles", account.id)
        profile_dir.mkdir(parents=True, exist_ok=True)

        with profile_dir.joinpath("pmc_profile.json").open(
            "w", encoding="utf8"
        ) as file:
            file.write(profile.json(exclude_none=True))

        # TODO: Scav profile generation
        scav_profile = json.load(root_dir.joinpath("resources", "scav_profile.json").open("r", encoding="utf8"))
        scav_profile["id"] = f"scav{profile.aid}"
        scav_profile["savage"] = f"scav{profile.aid}"
        scav_profile["aid"] = profile.aid
        json.dump(
            scav_profile,
            profile_dir.joinpath("scav_profile.json").open("w", encoding="utf8"),
            indent=4,
            ensure_ascii=False,
        )

        profile_manager.get_or_create_profile(profile_id=profile_id)
        return profile
