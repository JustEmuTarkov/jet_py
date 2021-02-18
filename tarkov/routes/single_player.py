from typing import Any, List

import ujson
from fastapi import Request
from pydantic import BaseModel, parse_obj_as

from server import db_dir, logger
from server.utils import make_router
from tarkov.inventory.helpers import regenerate_items_ids
from tarkov.inventory.models import Item
from tarkov.lib import locations
from tarkov.lib.bots import BotGenerator
from tarkov.models import TarkovSuccessResponse
from tarkov.profile import Profile
from tarkov.profile.models import ProfileModel

singleplayer_router = make_router(tags=["Singleplayer"])


@singleplayer_router.get("/singleplayer/bundles")
def singleplayer_bundles() -> List:
    return []


@singleplayer_router.get("/singleplayer/settings/raid/menu")
def singleplayer_settings_raid_menu() -> dict:
    # TODO: Put that into the config file !
    return {
        "aiAmount": "AsOnline",
        "aiDifficulty": "AsOnline",
        "bossEnabled": True,
        "scavWars": False,
        "taggedAndCursed": False,
    }


@singleplayer_router.get("/api/location/{location_name}")
def location(location_name: str) -> dict:
    location_name = location_name.lower()

    location_generator = locations.LocationGenerator(location_name)

    return location_generator.generate_location()


@singleplayer_router.get("/singleplayer/settings/bot/difficulty/{type_}/{difficulty}")
def bot_difficulty_settings(type_: str, difficulty: str) -> dict:
    if type_ == "core":
        return ujson.load(db_dir.joinpath("base", "botCore.json").open(encoding="utf8"))

    bot_file = db_dir.joinpath("bots", type_, "difficulty", f"{difficulty}.json").open(encoding="utf8")

    return ujson.load(bot_file)


@singleplayer_router.get("/singleplayer/settings/bot/limit/{bot_type}")
def settings_bot_limit(bot_type: str) -> int:  # pylint: disable=unused-argument
    return 30


@singleplayer_router.post("/client/game/bot/generate")
async def generate_bots(request: Request) -> TarkovSuccessResponse[List[dict]]:
    bots: List[dict] = []
    request_data: dict = await request.json()

    logger.debug(request_data)
    bot_generator = BotGenerator()
    for condition in request_data["conditions"]:
        bot_limit = condition["Limit"]

        for _ in range(bot_limit):
            bot = bot_generator.generate_bot(role=condition["Role"], difficulty=condition["Difficulty"])
            bots.append(bot)

    return TarkovSuccessResponse(data=bots)


@singleplayer_router.get("/mode/offline")
def mode_offline() -> dict:
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
        "ScavSpawnPointPatch": True,
        "ScavExfilPatch": True,
        "EndByTimerPatch": True,
    }


class ProfileSaveRequest(BaseModel):
    profile: ProfileModel
    isPlayerScav: bool
    exit: Any
    health: Any


@singleplayer_router.put("/raid/profile/save")
async def singleplayer_raid_profile_save(request: Request) -> TarkovSuccessResponse:
    # TODO: Add Saving profile here
    # data struct {exit, isPlayerScav, profile, health}
    # update profile on this request
    body = await request.json()

    with Profile(profile_id=body["profile"]["aid"]) as profile:
        # profile.pmc_profile['Health']['BodyParts'] = data['health']['Health']
        # for body_part in profile.pmc_profile['HealtPh']['BodyParts']:
        #     del body_part['Effects']
        #
        # profile.pmc_profile['Health']['Hydration']['Current'] = data['health']['Hydration']
        # profile.pmc_profile['Health']['Energy']['Current'] = data['health']['Energy']

        # profile.pmc_profile['Info'] = profile_data['Info']
        # profile.pmc_profile['Encyclopedia'] = profile_data['Encyclopedia']
        # profile.pmc_profile['Skills'] = profile_data['Skills']

        raid_inventory_items: List[Item] = parse_obj_as(List[Item], body["profile"]["Inventory"]["items"])
        equipment = profile.inventory.get_item(profile.inventory.inventory.equipment)

        # Remove all equipment children
        profile.inventory.remove_item(equipment, remove_children=True)
        profile.inventory.add_item(equipment, child_items=[])

        items = list(item for item in raid_inventory_items if item.slotId is not None)
        regenerate_items_ids(items)  # Regenerate item ids to be 100% safe
        profile.inventory.add_items(items)

    return TarkovSuccessResponse(data=None)


@singleplayer_router.post("/raid/profile/list")
def singleplayer_raid_profile_list() -> TarkovSuccessResponse[dict]:
    # TODO: Put that into the config file !
    return TarkovSuccessResponse(
        data={
            "aiAmount": "AsOnline",
            "aiDifficulty": "AsOnline",
            "bossEnabled": True,
            "scavWars": False,
            "taggedAndCursed": False,
        }
    )


@singleplayer_router.post("/raid/map/name")
def singleplayer_raid_menu_name() -> TarkovSuccessResponse:
    # TODO: This should get a Map Name and store that with profile ID(session id)
    return TarkovSuccessResponse(data=None)


@singleplayer_router.get("/singleplayer/settings/weapon/durability")
def weapon_durability() -> bool:
    return True
