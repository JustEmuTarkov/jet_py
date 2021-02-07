from flask import Blueprint

from server.utils import game_response_middleware
from tarkov.lib import hideout

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/hideout/areas', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def client_hideout_areas():
    return hideout.hideout_database['areas']


@blueprint.route('/client/hideout/settings', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def client_hideout_settings():
    return hideout.hideout_database['settings']


@blueprint.route('/client/hideout/production/recipes', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def client_hideout_production_recipes():
    return hideout.hideout_database['production']


@blueprint.route('/client/hideout/production/scavcase/recipes', methods=['POST', 'GET'])
@game_response_middleware(is_static=True)
def client_hideout_production_scavcase_recipes():
    return hideout.hideout_database['scavcase']
