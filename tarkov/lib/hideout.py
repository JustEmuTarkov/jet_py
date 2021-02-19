import ujson

from server import db_dir
from tarkov.library import concat_items_files_into_array

hideout_database: dict = {
    "areas": [],
    "settings": {},
    "production": [],
    "scavcase": [],
}

# Load hideout areas
hideout_areas_dir = db_dir.joinpath("hideout", "areas")
hideout_database["areas"] = concat_items_files_into_array(hideout_areas_dir)

# Load hideout settings
setting_path = db_dir.joinpath("hideout", "settings.json")
hideout_database["settings"] = ujson.load(setting_path.open("r", encoding="utf8"))["data"]

# Load hideout production
production_dir = db_dir.joinpath("hideout", "production")
hideout_database["production"] = concat_items_files_into_array(production_dir)

# Load hideout scav case
scavcase_dir = db_dir.joinpath("hideout", "scavcase")
hideout_database["scavcase"] = concat_items_files_into_array(scavcase_dir)
