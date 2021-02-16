from typing import Literal, Optional, Union

import ujson
from fastapi.params import Cookie, Depends

from fastapi import Request
from server import db_dir
from server.utils import make_router
from tarkov.dependencies import with_profile
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile import Profile

match_router = make_router(tags=["Match"])


@match_router.post("/client/match/group/status")
def group_status() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data={
            "players": [],
            "invite": [],
            "group": [],
        }
    )


@match_router.post("/client/match/group/exit_from_menu")
def exit_from_menu() -> TarkovSuccessResponse[Literal[None]]:
    return TarkovSuccessResponse(data=None)


@match_router.post("/client/match/available")
def available() -> TarkovSuccessResponse[Literal[True]]:
    return TarkovSuccessResponse(data=True)


# {
#     'location': 'Interchange',
#     'savage': False,
#     'entryPoint': 'MallNW',
#     'dt': 'PAST',
#     'servers': [
#         {
#             'ping': -1,
#             'ip': 'https://127.0.0.1:5000/',
#             'port': '5000'
#         }
#     ],
#     'keyId': ''
# }
@match_router.post("/client/match/join")
async def join(
    request: Request,
    profile: Profile = Depends(with_profile),  # type: ignore
) -> Union[TarkovSuccessResponse[list], TarkovErrorResponse]:
    request_data: dict = await request.json()
    return TarkovSuccessResponse(
        data=[
            {
                "profileid": profile.pmc_profile.id,
                "status": "busy",
                "sid": "",
                "ip": "127.0.0.1",
                "port": 9909,
                "version": "live",
                "location``": request_data["location"],
                "gamemode": "deathmatch",
                "shortid": "TEST",
            }
        ]
    )


@match_router.post("/client/match/exit")
def exit_() -> TarkovSuccessResponse[Literal[None]]:
    return TarkovSuccessResponse(data=None)


@match_router.post("/client/getMetricsConfig")
def get_metrics_config() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(
        data=ujson.load(
            db_dir.joinpath("base", "matchMetrics.json").open(encoding="utf8")
        )
    )
