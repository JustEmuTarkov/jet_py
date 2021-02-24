from typing import Any, Dict, List

import pydantic
from fastapi import Request
from fastapi.params import Depends
from pydantic import BaseModel, parse_obj_as

from server.utils import make_router
from tarkov.dependencies import with_profile
from tarkov.inventory.implementations import SimpleInventory
from tarkov.inventory.models import Item
from tarkov.lib import locations
from tarkov.models import TarkovSuccessResponse
from tarkov.profile import Profile
from tarkov.profile.models import BackendCounter, ProfileInfo, ProfileModel, Skills
from tarkov.quests.models import Quest

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
async def singleplayer_raid_profile_save(
    request: Request,
    profile: Profile = Depends(with_profile),  # type: ignore
) -> TarkovSuccessResponse:
    # TODO: Add Saving profile here
    # data struct {exit, isPlayerScav, profile, health}
    # update profile on this request
    body = await request.json()

    pmc_health = profile.pmc_profile.Health
    for body_part, health in body["health"]["Health"].items():
        pmc_health["BodyParts"][body_part]["Health"]["Maximum"] = health["Maximum"]
        pmc_health["BodyParts"][body_part]["Health"]["Current"] = health["Current"]
        pmc_health["BodyParts"][body_part]["Effects"] = health["Effects"]

    pmc_health["Hydration"]["Current"] = body["health"]["Hydration"]
    pmc_health["Energy"]["Current"] = body["health"]["Energy"]

    raid_profile = body["profile"]
    profile.pmc_profile.Encyclopedia.update(raid_profile["Encyclopedia"])
    profile.pmc_profile.Skills = Skills.parse_obj(raid_profile["Skills"])
    profile.pmc_profile.Quests = pydantic.parse_obj_as(List[Quest], raid_profile["Quests"])

    info = raid_profile["Info"]
    info["LowerNickname"] = profile.pmc_profile.Info.LowerNickname
    info["GameVersion"] = profile.pmc_profile.Info.GameVersion
    info["LastTimePlayedAsSavage"] = profile.pmc_profile.Info.LastTimePlayedAsSavage
    profile.pmc_profile.Info = ProfileInfo.parse_obj(info)

    backend_counters: Dict[str, BackendCounter] = {
        k: BackendCounter.parse_obj(v)
        for k, v in raid_profile["BackendCounters"].items()
        if v["id"] and v["qid"]
    }
    for key, raid_counter in backend_counters.items():
        profile_counter = profile.pmc_profile.BackendCounters.get(key, raid_counter)
        profile.pmc_profile.BackendCounters[key] = max(raid_counter, profile_counter, key=lambda c: c.value)

    profile.pmc_profile.Stats = raid_profile["Stats"]

    raid_inventory_items: List[Item] = parse_obj_as(List[Item], body["profile"]["Inventory"]["items"])
    raid_inventory = SimpleInventory(items=raid_inventory_items)
    equipment = profile.inventory.get(profile.inventory.inventory.equipment)

    # Remove all equipment children
    profile.inventory.remove_item(equipment, remove_children=True)

    raid_equipment = raid_inventory.iter_item_children_recursively(raid_inventory.get(equipment.id))
    profile.inventory.add_item(equipment, list(raid_equipment))

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


@singleplayer_router.post("/player/health/sync")
async def health_sync(
    request: Request,
    profile: Profile = Depends(with_profile),  # type: ignore
) -> TarkovSuccessResponse:
    body = await request.json()

    profile.pmc_profile.Health["Hydration"]["Current"] = body["Hydration"]
    profile.pmc_profile.Health["Energy"]["Current"] = body["Energy"]

    for limb, health in body["Health"].items():
        profile.pmc_profile.Health["BodyParts"][limb]["Health"] = health

    return TarkovSuccessResponse(data=None)
