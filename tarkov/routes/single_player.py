from typing import Any, List

from fastapi import Request
from fastapi.params import Depends
from pydantic import BaseModel

from server.utils import make_router
from tarkov.profile.dependencies import with_profile
from tarkov.lib import locations
from tarkov.models import TarkovSuccessResponse
from tarkov.profile.models import ProfileModel
from tarkov.profile.profile import Profile

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
    profile: Profile = Depends(with_profile),
) -> TarkovSuccessResponse:
    body = await request.json()

    profile.pmc.Health["Hydration"]["Current"] = body["Hydration"]
    profile.pmc.Health["Energy"]["Current"] = body["Energy"]

    for limb, health in body["Health"].items():
        profile.pmc.Health["BodyParts"][limb]["Health"] = health

    return TarkovSuccessResponse(data=None)
