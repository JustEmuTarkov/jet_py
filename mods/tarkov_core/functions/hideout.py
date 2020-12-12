import ujson

from server.main import db_dir
from mods.tarkov_core.library import concat_items_files_into_array


class Hideout:
    hideout_database = {
        "area": [],
        "settings": {},
        "production": [],
        "scavcase": [],
    }

    def __init__(self):
        # Load hideout areas
        hideout_areas_dir = db_dir.joinpath('hideout', 'areas')
        self.hideout_database['area'] = concat_items_files_into_array(hideout_areas_dir)
        # Load hideout settings
        setting_path = db_dir.joinpath('hideout', 'settings.json')
        self.hideout_database['settings'] = ujson.load(setting_path.open('r', encoding='utf8'))['data']
        # Load hideout production
        production_dir = db_dir.joinpath('hideout', 'production')
        self.hideout_database['production'] = concat_items_files_into_array(production_dir)
        # Load hideout scav case
        scavcase_dir = db_dir.joinpath('hideout', 'scavcase')
        self.hideout_database['scavcase'] = concat_items_files_into_array(scavcase_dir)
        pass

    def upgrade(self):
        pass

    def complete(self):
        pass

    def scav_case_start(self):
        pass

    def continue_production_start(self):
        pass

    def single_production_start(self):
        pass

    def take_production(self):
        pass

    def put_in_area_slot(self):
        pass

    def take_from_area_slot(self):
        pass

    def toggle(self):
        pass
