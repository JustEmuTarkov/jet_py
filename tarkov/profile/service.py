import ujson

from server import db_dir, root_dir
from tarkov.launcher.accounts import account_service
from tarkov.profile.models import ProfileModel


class ProfileService:
    @staticmethod
    def create_profile(nickname: str, side: str, profile_id: str) -> ProfileModel:
        account = account_service.get_account(profile_id)
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


profile_service = ProfileService()
