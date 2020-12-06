import ujson

from core.app import app
from core.main import db_dir
from core.utils import route_decorator
from mods.tarkov_core.library import concat_items_files_into_array


@app.route('/client/hideout/areas', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def client_hideout_areas():
    hideout_areas_dir = db_dir.joinpath('hideout', 'areas')
    return concat_items_files_into_array(hideout_areas_dir)


@app.route('/client/hideout/settings', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def client_hideout_settings():
    setting_path = db_dir.joinpath('hideout', 'settings.json')
    return ujson.load(setting_path.open('r', encoding='utf8'))


@app.route('/client/hideout/production/recipes', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def client_hideout_production_recipes():
    production_dir = db_dir.joinpath('hideout', 'production')
    return concat_items_files_into_array(production_dir)


@app.route('/client/hideout/production/scavcase/recipes', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def client_hideout_production_scavcase_recipes():
    scavcase_dir = db_dir.joinpath('hideout', 'scavcase')
    return concat_items_files_into_array(scavcase_dir)
