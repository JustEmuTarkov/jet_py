from __future__ import annotations

from typing import List, Union

import ujson
from fastapi.params import Body, Cookie, Depends
from starlette.requests import Request

from server import logger, root_dir
from server.utils import get_request_url_root, make_router
from tarkov.dependencies import with_profile
from tarkov.inventory_dispatcher import DispatcherManager
from tarkov.inventory_dispatcher.manager import DispatcherResponse
from tarkov.launcher.accounts import account_service
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile import Profile
from tarkov.profile.models import ProfileModel
from tarkov.profile.service import profile_service

profile_router = make_router(tags=["Profile"])


@profile_router.post(
    "/client/game/profile/items/moving",
    response_model=TarkovSuccessResponse[DispatcherResponse],
    response_model_exclude_none=True,
    response_model_exclude_unset=False,
)
def client_game_profile_item_move(
    profile: Profile = Depends(with_profile),  # type: ignore
    body: dict = Body(...),  # type: ignore
) -> Union[TarkovSuccessResponse[DispatcherResponse], TarkovErrorResponse]:
    dispatcher = DispatcherManager(profile)
    response = dispatcher.dispatch(body["data"])
    return TarkovSuccessResponse(data=response)


@profile_router.post("/client/game/profile/list")
def client_game_profile_list(
    profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> Union[TarkovSuccessResponse[List[dict]], TarkovErrorResponse]:
    try:
        with Profile(profile_id) as profile:
            return TarkovSuccessResponse(
                data=[
                    profile.pmc.dict(exclude_none=True),
                    profile.scav.dict(exclude_none=True),
                ]
            )
    except Profile.ProfileDoesNotExistsError as error:
        logger.exception(error)
        return TarkovSuccessResponse(data=[])


@profile_router.post("/client/game/profile/select")
def client_game_profile_list_select(request: Request) -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data={
            "status": "ok",
            "notifier": {
                "server": get_request_url_root(request),
                "channel_id": "testChannel",
            },
        }
    )


@profile_router.post("/client/profile/status")
def client_profile_status(
    profile: Profile = Depends(with_profile),  # type: ignore
) -> Union[TarkovSuccessResponse[List[dict]], TarkovErrorResponse]:
    response = []
    for profile_type in ("scav", "pmc"):
        response.append(
            {
                "profileid": f"{profile_type}{profile.profile_id}",
                "status": "Free",
                "sid": "",
                "ip": "",
                "port": 0,
            }
        )
    print(response)

    return TarkovSuccessResponse(data=response)


@profile_router.post("/client/game/profile/nickname/reserved")
def nickname_reserved(
    profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> TarkovSuccessResponse[str]:
    account = account_service.get_account(profile_id)
    return TarkovSuccessResponse(data=account.nickname)


@profile_router.post("/client/game/profile/nickname/validate")
def nickname_validate(
    nickname: str = Body(..., embed=True),  # type: ignore
) -> Union[TarkovSuccessResponse, TarkovErrorResponse]:
    if len(nickname) < 3:
        return TarkovErrorResponse(errmsg="Nickname is too short", err=256)

    if account_service.is_nickname_taken(nickname):
        return TarkovErrorResponse(errmsg="Nickname is taken", err=255)

    return TarkovSuccessResponse(data={"status": "ok"})


@profile_router.post("/client/game/profile/create")
def create_profile(
    profile_id: str = Cookie(..., alias="PHPSESSID"),  # type: ignore
    side: str = Body(..., embed=True),  # type: ignore
    nickname: str = Body(..., embed=True),  # type: ignore
) -> TarkovSuccessResponse[dict]:
    profile = profile_service.create_profile(nickname=nickname, side=side, profile_id=profile_id)
    return TarkovSuccessResponse(data={"uid": profile.id})
