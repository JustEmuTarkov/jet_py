from fastapi import APIRouter

from tarkov.lib import hideout
from tarkov.models import TarkovSuccessResponse

router = APIRouter(prefix='', tags=['Hideout'])


@router.post('/client/hideout/areas')
def hideout_areas() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=hideout.hideout_database['areas']
    )


@router.post('/client/hideout/settings')
def hideout_settings() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=hideout.hideout_database['settings']
    )


@router.post('/client/hideout/production/recipes')
def client_hideout_production_recipes() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=hideout.hideout_database['production']
    )


@router.post('/client/hideout/production/scavcase/recipes')
def hideout_production_scav_recipes() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=hideout.hideout_database['scavcase']
    )
