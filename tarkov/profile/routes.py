from __future__ import annotations

from typing import Optional

import ujson
from fastapi import APIRouter
from fastapi.params import Cookie
from flask import request

from server import root_dir
from tarkov.inventory_dispatcher import DispatcherManager
from tarkov.profile import Profile

router = APIRouter(prefix='', tags=['Profile'])


@router.post('/client/game/profile/items/moving')
def client_game_profile_item_move(
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None)
):
    dispatcher = DispatcherManager(profile_id)
    response = dispatcher.dispatch()
    return response.dict(exclude_defaults=False, exclude_none=True, exclude_unset=False)


@router.post('/client/game/profile/list')
def client_game_profile_list(
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None)
):
    with Profile(profile_id) as profile:
        pmc_profile = profile.get_profile()

        profile_dir = root_dir.joinpath('resources', 'profiles', profile.profile_id)
        scav_profile = ujson.load((profile_dir / 'character_scav.json').open('r'))

        return [
            pmc_profile,
            scav_profile,
        ]


@router.post('/client/game/profile/select')
def client_game_profile_list_select():
    return {
        'status': 'ok',
        'notifier': {
            'server': f'{request.url_root}/',
            'channel_id': 'testChannel',
        },
    }


@router.post('/client/profile/status')
def client_profile_status():
    session_id = request.cookies['PHPSESSID']
    response = []
    for profile_type in ('scav', 'pmc'):
        response.append({
            'profileid': f'{profile_type}{session_id}',
            'status': 'Free',
            'sid': '',
            'ip': '',
            'port': 0
        })

    return response
