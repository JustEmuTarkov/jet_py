from __future__ import annotations

from typing import TYPE_CHECKING

import ujson

from server import db_dir, root_dir

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
        # TODO: That's just disgusting but i don't want to deal with cyclic imports right now
        from tarkov.profile.models import ProfileModel

        account = self.__account_service.get_account(profile_id)
        base_profile_dir = db_dir.joinpath("profile", account.edition)

        starting_outfit = ujson.load(base_profile_dir.joinpath("starting_outfit.json").open())
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

        with profile_dir.joinpath("pmc_profile.json").open("w", encoding="utf8") as file:
            file.write(profile.json())

        return profile
