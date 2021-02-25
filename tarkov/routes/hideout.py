from typing import List

from server.utils import make_router
from tarkov.hideout.repositories.areas import HideoutAreaTemplate
from tarkov.hideout.repositories.production import HideoutProductionModel
from tarkov.hideout.repositories.scavcase_production import ScavcaseProductionModel
from tarkov.hideout.repositories.settings import HideoutSettingsModel
from tarkov.models import TarkovSuccessResponse
from tarkov.hideout import repositories as hideout_repositories

hideout_router = make_router(tags=["Hideout"])


@hideout_router.post("/client/hideout/areas")
def hideout_areas() -> TarkovSuccessResponse[List[HideoutAreaTemplate]]:
    return TarkovSuccessResponse(data=hideout_repositories.areas_repository.areas)


@hideout_router.post("/client/hideout/settings")
def hideout_settings() -> TarkovSuccessResponse[HideoutSettingsModel]:
    return TarkovSuccessResponse(data=hideout_repositories.settings)


@hideout_router.post("/client/hideout/production/recipes")
def client_hideout_production_recipes() -> TarkovSuccessResponse[List[HideoutProductionModel]]:
    return TarkovSuccessResponse(data=hideout_repositories.production_repository.production)


@hideout_router.post("/client/hideout/production/scavcase/recipes")
def hideout_production_scav_recipes() -> TarkovSuccessResponse[List[ScavcaseProductionModel]]:
    return TarkovSuccessResponse(data=hideout_repositories.scavcase_production_repository.production)
