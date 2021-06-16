from typing import List, Union

from dependency_injector.wiring import Provide, inject
from fastapi.params import Body, Cookie, Depends
from fastapi.requests import Request

from server import logger
from server.container import AppContainer
from server.utils import get_request_url_root, make_router
from tarkov.inventory_dispatcher import DispatcherManager
from tarkov.inventory_dispatcher.manager import DispatcherResponse
from tarkov.launcher.accounts import AccountService
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile.dependencies import with_profile
from tarkov.profile.profile import Profile
from tarkov.profile.profile_manager import ProfileManager
from tarkov.profile.service import ProfileService

profile_router = make_router(tags=["Profile"])


@profile_router.post(
    "/client/game/profile/items/moving",
    response_model=TarkovSuccessResponse[DispatcherResponse],
    response_model_exclude_none=True,
    response_model_exclude_unset=False,
)
@inject
def client_game_profile_item_move(
    profile: Profile = Depends(with_profile),
    body: dict = Body(...),
) -> Union[TarkovSuccessResponse[DispatcherResponse], TarkovErrorResponse]:
    dispatcher = DispatcherManager(profile)
    response = dispatcher.dispatch(body["data"])
    return TarkovSuccessResponse(data=response)


@profile_router.post("/client/game/profile/list")
@inject
async def client_game_profile_list(
    profile_id: str = Cookie(..., alias="PHPSESSID"),
    profile_manager: ProfileManager = Depends(Provide[AppContainer.profile.manager]),
) -> Union[TarkovSuccessResponse[List[dict]], TarkovErrorResponse]:
    try:
        async with profile_manager.locks[profile_id]:
            profile = profile_manager.get_profile(profile_id)
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
    profile: Profile = Depends(with_profile),
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

    return TarkovSuccessResponse(data=response)


@profile_router.post("/client/game/profile/nickname/reserved")
@inject
def nickname_reserved(
    profile_id: str = Cookie(..., alias="PHPSESSID"),
    account_service: AccountService = Depends(
        Provide[AppContainer.launcher.account_service]
    ),
) -> TarkovSuccessResponse[str]:
    account = account_service.get_account(profile_id)
    return TarkovSuccessResponse(data=account.nickname)


@profile_router.post("/client/game/profile/nickname/validate")
@inject
def nickname_validate(
    nickname: str = Body(..., embed=True),
    account_service: AccountService = Depends(
        Provide[AppContainer.launcher.account_service]
    ),
) -> Union[TarkovSuccessResponse, TarkovErrorResponse]:
    if len(nickname) < 3:
        return TarkovErrorResponse(errmsg="Nickname is too short", err=256)

    if account_service.is_nickname_taken(nickname):
        return TarkovErrorResponse(errmsg="Nickname is taken", err=255)

    return TarkovSuccessResponse(data={"status": "ok"})


@profile_router.post("/client/game/profile/create")
@inject
def create_profile(
    profile_id: str = Cookie(..., alias="PHPSESSID"),
    side: str = Body(..., embed=True),
    nickname: str = Body(..., embed=True),
    profile_service: ProfileService = Depends(Provide[AppContainer.profile.service]),
) -> TarkovSuccessResponse[dict]:
    profile = profile_service.create_profile(
        profile_id=profile_id,
        nickname=nickname,
        side=side,
    )
    return TarkovSuccessResponse(data={"uid": profile.id})
