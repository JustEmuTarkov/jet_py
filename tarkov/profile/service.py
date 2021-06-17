from __future__ import annotations

from pathlib import Path
from typing import Final, TYPE_CHECKING

import ujson

from server import db_dir, root_dir

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from tarkov.launcher.accounts import AccountService
    from tarkov.profile.models import ProfileModel
    from tarkov.profile.profile_manager import ProfileManager


class ProfileService:
    def __init__(
        self,
        account_service: AccountService,
        profile_manager: ProfileManager,
    ):
        self.__account_service = account_service
        self.__profile_manager = profile_manager

    def create_profile(
        self,
        profile_id: str,
        nickname: str,
        side: str,
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

        profile_dir: Final[Path] = root_dir.joinpath(
            "resources", "profiles", account.id
        )
        profile_dir.mkdir(parents=True, exist_ok=True)

        with profile_dir.joinpath("pmc_profile.json").open(
            "w", encoding="utf8"
        ) as file:
            file.write(profile.json(exclude_none=True))

        # TODO: Scav profile generation, for not it just copies
        scav_profile = ujson.load(
            root_dir.joinpath("resources", "scav_profile.json").open(
                "r", encoding="utf8"
            )
        )
        scav_profile["id"] = f"scav{profile.aid}"
        scav_profile["savage"] = f"scav{profile.aid}"
        scav_profile["aid"] = profile.aid
        ujson.dump(
            scav_profile,
            profile_dir.joinpath("scav_profile.json").open("w", encoding="utf8"),
            indent=4,
            ensure_ascii=False,
        )

        self.__profile_manager.get_profile(profile_id=profile_id)
        return profile
