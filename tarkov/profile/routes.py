from __future__ import annotations

from typing import List, Optional, Union

import ujson
from fastapi import APIRouter
from fastapi.params import Cookie
from starlette.requests import Request

from server import root_dir
from server.utils import get_request_url_root
from tarkov.inventory_dispatcher import DispatcherManager
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile import Profile

router = APIRouter(prefix='', tags=['Profile'])


@router.post('/client/game/profile/items/moving')
def client_game_profile_item_move(
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None)  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if profile_id is None:
        return TarkovErrorResponse.profile_id_is_none()
    dispatcher = DispatcherManager(profile_id)
    response = dispatcher.dispatch()
    return TarkovSuccessResponse(
        data=response.dict(exclude_defaults=False, exclude_none=True, exclude_unset=False)
    )


@router.post('/client/game/profile/list')
def client_game_profile_list(
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None)  # type: ignore
) -> Union[TarkovSuccessResponse[List[dict]], TarkovErrorResponse]:
    if profile_id is None:
        return TarkovErrorResponse.profile_id_is_none()

    with Profile(profile_id) as profile:
        pmc_profile = profile.get_profile()

        profile_dir = root_dir.joinpath('resources', 'profiles', profile.profile_id)
        scav_profile = ujson.load((profile_dir / 'character_scav.json').open('r'))

        return TarkovSuccessResponse(data=[
            pmc_profile,
            scav_profile,
        ])


@router.post('/client/game/profile/select')
def client_game_profile_list_select(request: Request):
    return {
        'status': 'ok',
        'notifier': {
            'server': get_request_url_root(request),
            'channel_id': 'testChannel',
        },
    }


@router.post('/client/profile/status')
def client_profile_status(
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None)  # type: ignore
) -> Union[TarkovSuccessResponse[List[dict]], TarkovErrorResponse]:
    if profile_id is None:
        return TarkovErrorResponse.profile_id_is_none()

    response = []
    for profile_type in ('scav', 'pmc'):
        response.append({
            'profileid': f'{profile_type}{profile_id}',
            'status': 'Free',
            'sid': '',
            'ip': '',
            'port': 0
        })

    return TarkovSuccessResponse(data=response)
