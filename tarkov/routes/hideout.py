from server.utils import make_router
from tarkov.lib import hideout
from tarkov.models import TarkovSuccessResponse

hideout_router = make_router(tags=['Hideout'])


@hideout_router.post('/client/hideout/areas')
def hideout_areas() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=hideout.hideout_database['areas']
    )


@hideout_router.post('/client/hideout/settings')
def hideout_settings() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=hideout.hideout_database['settings']
    )


@hideout_router.post('/client/hideout/production/recipes')
def client_hideout_production_recipes() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=hideout.hideout_database['production']
    )


@hideout_router.post('/client/hideout/production/scavcase/recipes')
def hideout_production_scav_recipes() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=hideout.hideout_database['scavcase']
    )
