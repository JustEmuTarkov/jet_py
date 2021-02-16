from __future__ import annotations

from typing import List, Union

import ujson
from fastapi.params import Depends
from starlette.requests import Request

from server import root_dir
from server.requests import ZLibRequest
from server.utils import get_request_url_root, make_router
from tarkov.dependencies import with_profile
from tarkov.inventory_dispatcher import DispatcherManager
from tarkov.inventory_dispatcher.manager import DispatcherResponse
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile import Profile
from tarkov.profile.models import ProfileModel

profile_router = make_router(tags=["Profile"])


@profile_router.post(
    "/client/game/profile/items/moving",
    response_model=TarkovSuccessResponse[DispatcherResponse],
    response_model_exclude_none=True,
    response_model_exclude_unset=False,
)
async def client_game_profile_item_move(
        request: ZLibRequest,
        profile: Profile = Depends(with_profile),  # type:
) -> Union[TarkovSuccessResponse[DispatcherResponse], TarkovErrorResponse]:
    data = await request.json()

    dispatcher = DispatcherManager(profile)
    response = dispatcher.dispatch(data["data"])
    return TarkovSuccessResponse(data=response)


@profile_router.post("/client/game/profile/list")
def client_game_profile_list(
        profile: Profile = Depends(with_profile),  # type: ignore
) -> Union[TarkovSuccessResponse[List[dict]], TarkovErrorResponse]:
    pmc_profile = profile.get_profile()
    profile_dir = root_dir.joinpath("resources", "profiles", profile.profile_id)
    scav_profile = ujson.load((profile_dir / "character_scav.json").open("r"))
    return TarkovSuccessResponse(
        data=[
            ProfileModel.parse_obj(pmc_profile).dict(
                exclude_unset=False, exclude_defaults=False, exclude_none=True
            ),
            scav_profile,
        ]
    )


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

    return TarkovSuccessResponse(data=response)
