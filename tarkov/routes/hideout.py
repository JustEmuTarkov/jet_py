from server.utils import make_router
from tarkov.models import TarkovSuccessResponse
from tarkov.hideout import repositories as hideout_repositories

hideout_router = make_router(tags=["Hideout"])


@hideout_router.post("/client/hideout/areas")
def hideout_areas() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(data=hideout_repositories.areas.view())


@hideout_router.post("/client/hideout/settings")
def hideout_settings() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(data=hideout_repositories.settings.dict())


@hideout_router.post("/client/hideout/production/recipes")
def client_hideout_production_recipes() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(data=hideout_repositories.production.view())


@hideout_router.post("/client/hideout/production/scavcase/recipes")
def hideout_production_scav_recipes() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(data=hideout_repositories.scavcase_production.view())
