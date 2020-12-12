from flask import Blueprint

from mods.tarkov_core.functions import hideout
from server.utils import route_decorator

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/hideout/areas', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def client_hideout_areas():
    return hideout.hideout_database['areas']


@blueprint.route('/client/hideout/settings', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def client_hideout_settings():
    return hideout.hideout_database['settings']


@blueprint.route('/client/hideout/production/recipes', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def client_hideout_production_recipes():
    return hideout.hideout_database['production']


@blueprint.route('/client/hideout/production/scavcase/recipes', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def client_hideout_production_scavcase_recipes():
    return hideout.hideout_database['scavcase']
