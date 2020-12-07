from flask import Blueprint

from core.utils import route_decorator

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/singleplayer/bundles', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def singleplayer_bundles():
    return {}


@blueprint.route('/singleplayer/settings/raid/menu')
@route_decorator()
def singleplayer_settings_raid_menu():
    # TODO: Put that into the config file !
    return {
        "aiAmount": "AsOnline",
        "aiDifficulty": "AsOnline",
        "bossEnabled": True,
        "scavWars": False,
        "taggedAndCursed": False
    }


@blueprint.route('/mode/offline', methods=['POST', 'GET'])
@route_decorator(is_static=True)
def mode_offline():
    # TODO: Put that into Server config file
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


@blueprint.route('/raid/profile/save', methods=['POST', 'GET'])
@route_decorator()
def singleplayer_raid_profile_save():
    # TODO: Add Saving profile here
    # data struct {exit, isPlayerScav, profile, health}
    # update profile on this request
    return None


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
