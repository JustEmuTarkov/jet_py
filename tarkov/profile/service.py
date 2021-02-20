from tarkov.launcher.accounts import account_service


class ProfileService:
    @staticmethod
    def create_profile(nickname: str, side: str, profile_id: str) -> None:
        account = account_service.get_account(profile_id)


profile_service = ProfileService()
