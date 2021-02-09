from typing import List

import ujson
from flask import Blueprint, request
from pydantic import parse_obj_as

from server import db_dir, logger
from server.utils import tarkov_response, zlib_middleware
from tarkov.inventory.helpers import regenerate_items_ids
from tarkov.inventory.models import Item
from tarkov.lib import locations
from tarkov.lib.bots import BotGenerator
from tarkov.profile import Profile

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/singleplayer/bundles', methods=['POST', 'GET'])
def singleplayer_bundles():
    return ujson.dumps([])


@blueprint.route('/singleplayer/settings/raid/menu')
@zlib_middleware
def singleplayer_settings_raid_menu():
    # TODO: Put that into the config file !
    return {
        "aiAmount": "AsOnline",
        "aiDifficulty": "AsOnline",
        "bossEnabled": True,
        "scavWars": False,
        "taggedAndCursed": False
    }


@blueprint.route('/api/location/<string:location_name>', methods=['POST', 'GET'])
@zlib_middleware
def location(location_name: str):
    location_name = location_name.lower()

    location_generator = locations.LocationGenerator(location_name)

    return location_generator.generate_location()


@blueprint.route('/singleplayer/settings/bot/difficulty/<string:type_>/<string:difficulty>')
@zlib_middleware
def bot_difficulty_settings(type_: str, difficulty: str):
    if type_ == 'core':
        return ujson.load(db_dir.joinpath('base', 'botCore.json').open(encoding='utf8'))

    bot_file = db_dir.joinpath('bots', type_, 'difficulty', f'{difficulty}.json').open(encoding='utf8')

    return ujson.load(bot_file)


@blueprint.route('/singleplayer/settings/bot/limit/<string:bot_type>')
@zlib_middleware
def settings_bot_limit(bot_type: str):  # pylint: disable=unused-argument
    return 30


@blueprint.route('/client/game/bot/generate', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def generate_bots() -> List[dict]:
    bots: List[dict] = []
    request_data: dict = request.data  # type: ignore

    logger.debug(request.data)
    bot_generator = BotGenerator()
    for condition in request_data['conditions']:
        bot_limit = condition['Limit']

        for _ in range(bot_limit):
            bot = bot_generator.generate_bot(role=condition['Role'], difficulty=condition['Difficulty'])
            bots.append(bot)

    return bots


@blueprint.route('/mode/offline', methods=['POST', 'GET'])
@zlib_middleware
def mode_offline():
    # TODO: Put that into Server config file
    # return str(True)
    return {
        "OfflineLootPatch": True,
        "InsuranceScreenPatch": True,
        "BossSpawnChancePatch": True,
        "BotTemplateLimitPatch": True,
        "RemoveUsedBotProfilePatch": True,
        "OfflineSaveProfilePatch": True,
        "OfflineSpawnPointPatch": True,
        "WeaponDurabilityPatch": True,
        "SingleModeJamPatch": True,
        "ExperienceGainPatch": True,
        "MainMenuControllerPatch": True,
        "PlayerPatch": True,
        "MatchmakerOfflineRaidPatch": True,
        "MatchMakerSelectionLocationScreenPatch": True,
        "GetNewBotTemplatesPatch": True,
        "SpawnPmcPatch": True,
        "CoreDifficultyPatch": True,
        "BotDifficultyPatch": True,
        "OnDeadPatch": True,
        "OnShellEjectEventPatch": True,
        "BotStationaryWeaponPatch": True,
        "BeaconPatch": True,
        "DogtagPatch": True,
        "LoadOfflineRaidScreenPatch": True,
        "ScavPrefabLoadPatch": True,
        "ScavProfileLoadPatch": True,
        "ScavSpawnPointPatch": False,
        "ScavExfilPatch": True,
        "EndByTimerPatch": True
    }


@blueprint.route('/raid/profile/save', methods=['PUT'])
@zlib_middleware()
@tarkov_response
def singleplayer_raid_profile_save() -> None:
    # TODO: Add Saving profile here
    # data struct {exit, isPlayerScav, profile, health}
    # update profile on this request
    data: dict = request.data  # type: ignore
    raid_profile: dict = data['profile']

    with Profile(profile_id=raid_profile['aid']) as profile:
        # profile.pmc_profile['Health']['BodyParts'] = data['health']['Health']
        # for body_part in profile.pmc_profile['HealtPh']['BodyParts']:
        #     del body_part['Effects']
        #
        # profile.pmc_profile['Health']['Hydration']['Current'] = data['health']['Hydration']
        # profile.pmc_profile['Health']['Energy']['Current'] = data['health']['Energy']

        # profile.pmc_profile['Info'] = profile_data['Info']
        # profile.pmc_profile['Encyclopedia'] = profile_data['Encyclopedia']
        # profile.pmc_profile['Skills'] = profile_data['Skills']

        raid_inventory_items = parse_obj_as(List[Item], raid_profile['Inventory']['items'])
        equipment = profile.inventory.get_item(profile.inventory.inventory.equipment)

        # Remove all equipment children
        profile.inventory.remove_item(equipment, remove_children=True)
        profile.inventory.add_item(equipment, child_items=[])

        items = list(item for item in raid_inventory_items if item.slotId is not None)
        regenerate_items_ids(items)  # Regenerate item ids to be 100% safe
        profile.inventory.add_items(items)


@blueprint.route('/raid/profile/list', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def singleplayer_raid_profile_list():
    # TODO: Put that into the config file !
    return {
        "aiAmount": "AsOnline",
        "aiDifficulty": "AsOnline",
        "bossEnabled": True,
        "scavWars": False,
        "taggedAndCursed": False
    }


@blueprint.route('/raid/map/name', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def singleplayer_raid_menu_name():
    # TODO: This should get a Map Name and store that with profile ID(session id)
    return None


@blueprint.route('/singleplayer/settings/weapon/durability')
@zlib_middleware
def weapon_durability():
    return True
