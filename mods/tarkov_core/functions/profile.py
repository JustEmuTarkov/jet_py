import ujson

from core.main import root_dir


class Profile:
    profiles = {}

    def __init__(self):
        profiles_path = root_dir.joinpath('resources', 'profiles')
        profile_paths = set(profiles_path.glob('*'))
        profile_data = {}
        for profile_id in profile_paths:
            single_dir = set(profiles_path.joinpath(profile_id).glob('pmc_*.json'))
            profile_data[profile_id.stem] = {file.stem: ujson.load(file.open('r', encoding='utf8')) for file in single_dir}
        self.profiles = profile_data
        pass

    def save_profile(self, profile_id):
        saving_profile_path = root_dir.joinpath('resources', 'profiles', profile_id)
        ujson.dump(self.profiles[profile_id]["pmc_profile"], saving_profile_path.joinpath("pmc_profile.json"))
        ujson.dump(self.profiles[profile_id]["pmc_hideout"], saving_profile_path.joinpath("pmc_hideout.json"))
        ujson.dump(self.profiles[profile_id]["pmc_inventory"], saving_profile_path.joinpath("pmc_inventory.json"))
        ujson.dump(self.profiles[profile_id]["pmc_quests"], saving_profile_path.joinpath("pmc_quests.json"))
        ujson.dump(self.profiles[profile_id]["pmc_stats"], saving_profile_path.joinpath("pmc_stats.json"))
        ujson.dump(self.profiles[profile_id]["pmc_traders"], saving_profile_path.joinpath("pmc_traders.json"))

    # just for testing
    def get_all_profiles(self):
        return self.profiles

    def get_profile(self, profile_id):
        profile_base = self.profiles[profile_id]['pmc_profile']
        profile_base['Inventory'] = self.profiles[profile_id]['pmc_inventory']
        profile_base['Hideout'] = self.profiles[profile_id]['pmc_hideout']
        profile_base['TraderStandings'] = self.profiles[profile_id]['pmc_traders']
        profile_base['Stats'] = self.profiles[profile_id]['pmc_stats']
        profile_base['Quests'] = self.profiles[profile_id]['pmc_quests']
        return profile_base

    def inventory_add_item(self, data):
        pass

    def inventory_remove_item(self, data):
        pass

    def inventory_move_item(self, data):
        pass


