import random
import time
from pathlib import Path

import ujson
from flask import Blueprint, request

from mods.core.lib import locations
from mods.core.lib.inventory import regenerate_items_ids
from mods.core.lib.profile import Profile
from server import db_dir, logger
from server.utils import route_decorator, ZlibMiddleware

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/singleplayer/bundles', methods=['POST', 'GET'])
def singleplayer_bundles():
    return ujson.dumps([])


@blueprint.route('/singleplayer/settings/raid/menu')
@ZlibMiddleware()
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
@ZlibMiddleware(send_browser_headers=True)
def location(location_name: str):
    location_name = location_name.lower()

    location_generator = locations.LocationGenerator(location_name)

    return location_generator.generate_location()


@blueprint.route('/singleplayer/settings/bot/difficulty/<string:type_>/<string:difficulty>')
@ZlibMiddleware()
def bot_difficulty_settings(type_: str, difficulty: str):
    if type_ == 'core':
        return ujson.load(db_dir.joinpath('base', 'botCore.json').open(encoding='utf8'))

    bot_file = db_dir.joinpath('bots', type_, 'difficulty', f'{difficulty}.json').open(encoding='utf8')

    return ujson.load(bot_file)


@blueprint.route('/singleplayer/settings/bot/limit/<string:bot_type>')
@ZlibMiddleware()
def settings_bot_limit(bot_type: str):
    return 30


def generate_bot(difficulty, role):
    # Bot generation will be moved into separate module

    bot = ujson.load(db_dir.joinpath('base', 'botBase.json').open(encoding='utf8'))

    bot['_id'] = 'bot' + ''.join(str(random.randint(0, 9)) for _ in range(7))

    bot['Info']['Settings']['Role'] = role
    bot['Info']['Settings']['BotDifficulty'] = difficulty

    bot_path = db_dir.joinpath('bots', role)

    random_inventory_path: Path = random.choice(list(bot_path.joinpath('inventory').glob('*.json')))
    bot['Inventory'] = ujson.load(random_inventory_path.open(encoding='utf8'))
    regenerate_items_ids(bot['Inventory']['items'])
    bot['Inventory']['equipment'] = bot['Inventory']['items'][0]['_id']

    health_base = {
        'Hydration': {'Current': 100, 'Maximum': 100},
        'Energy': {'Current': 100, 'Maximum': 100},
        'BodyParts': {
            'Head': {'Health': {'Current': 35, 'Maximum': 35}},
            'Chest': {'Health': {'Current': 80, 'Maximum': 80}},
            'Stomach': {'Health': {'Current': 70, 'Maximum': 70}},
            'LeftArm': {'Health': {'Current': 60, 'Maximum': 60}},
            'RightArm': {'Health': {'Current': 60, 'Maximum': 60}},
            'LeftLeg': {'Health': {'Current': 65, 'Maximum': 65}},
            'RightLeg': {'Health': {'Current': 65, 'Maximum': 65}}
        },
        'UpdateTime': 1598664622
    }

    bot_health = ujson.load(bot_path.joinpath('health', 'default.json').open(encoding='utf8'))
    # Set current and maximum energy and hydration
    health_base['Hydration']['Current'] = bot_health['Hydration']
    health_base['Hydration']['Maximum'] = bot_health['Hydration']

    health_base['Energy']['Current'] = bot_health['Energy']
    health_base['Energy']['Maximum'] = bot_health['Energy']

    for key, value in health_base['BodyParts'].items():
        bot_body_part_hp = bot_health['BodyParts'][key]
        value['Health']['Current'] = bot_body_part_hp
        value['Health']['Maximum'] = bot_body_part_hp

    health_base['UpdateTime'] = int(time.time())
    bot['Health'] = health_base
    bot['Info']['experience'] = 1

    return bot


@blueprint.route('/client/game/bot/generate', methods=['POST', 'GET'])
@route_decorator()
def generate_bots():
    bots = []
    # bot_base = ujson.load(db_dir.joinpath('base', 'botBase.json').open(encoding='utf8'))

    logger.debug(request.data)
    for condition in request.data['conditions']:
        bot_limit = condition['Limit']

        for _ in range(bot_limit):
            bot = generate_bot(
                difficulty=condition['Difficulty'],
                role=condition['Role']
            )
            bots.append(bot)

    return bots


@blueprint.route('/mode/offline', methods=['POST', 'GET'])
@ZlibMiddleware()
# @route_decorator(is_static=True)
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
@route_decorator()
def singleplayer_raid_profile_save():
    # TODO: Add Saving profile here
    # data struct {exit, isPlayerScav, profile, health}
    # update profile on this request
    data = request.data
    raid_profile: dict = data['profile']

    with Profile(profile_id=raid_profile['aid']) as profile:
        # profile.pmc_profile['Health']['BodyParts'] = data['health']['Health']
        # for body_part in profile.pmc_profile['Health']['BodyParts']:
        #     del body_part['Effects']
        #
        # profile.pmc_profile['Health']['Hydration']['Current'] = data['health']['Hydration']
        # profile.pmc_profile['Health']['Energy']['Current'] = data['health']['Energy']

        # profile.pmc_profile['Info'] = profile_data['Info']
        # profile.pmc_profile['Encyclopedia'] = profile_data['Encyclopedia']
        # profile.pmc_profile['Skills'] = profile_data['Skills']

        equipment = profile.inventory.get_item(profile.inventory.stash['equipment'])
        profile.inventory.remove_item(equipment)
        profile.inventory.add_item(equipment)
        # profile.inventory.remove_items(profile.inventory.iter_item_children_recursively(equipment))

        # Exclude root items like pockets, etc
        equipment_items = [i for i in raid_profile['Inventory']['items']
                           if i['_id'] not in raid_profile['Inventory'].values()]
        regenerate_items_ids(equipment_items)
        profile.inventory.items.extend(equipment_items)


@blueprint.route('/raid/profile/list', methods=['POST', 'GET'])
@route_decorator()
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
@route_decorator()
def singleplayer_raid_menu_name():
    # TODO: This should get a Map Name and store that with profile ID(session id)
    return None


@blueprint.route('/singleplayer/settings/weapon/durability')
@ZlibMiddleware()
def weapon_durability():
    return True
