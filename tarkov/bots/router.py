from __future__ import annotations

from typing import List, TYPE_CHECKING

import ujson
from dependency_injector.wiring import Provide, inject
from fastapi.params import Depends
from fastapi.requests import Request

from server import db_dir, logger
from server.utils import make_router
from tarkov.bots.container import BotContainer
from tarkov.models import TarkovSuccessResponse

if TYPE_CHECKING:
    from tarkov.bots.generator import BotGenerator

bots_router = make_router(tags=["Bots"])


@bots_router.get("/singleplayer/settings/bot/difficulty/{bot_type}/{difficulty}")
def bot_difficulty_settings(bot_type: str, difficulty: str) -> dict:
    if bot_type == "core":
        return ujson.load(db_dir.joinpath("base", "botCore.json").open(encoding="utf8"))

    bot_file = db_dir.joinpath(
        "bots", bot_type, "difficulty", f"{difficulty}.json"
    ).open(encoding="utf8")

    return ujson.load(bot_file)


@bots_router.get("/singleplayer/settings/bot/limit/{bot_type}")
def settings_bot_limit(bot_type: str) -> int:  # pylint: disable=unused-argument
    return 30


@bots_router.post("/client/game/bot/generate")
@inject
async def generate_bots(
    request: Request,
    bot_generator: BotGenerator = Depends(Provide[BotContainer.bot_generator]),
) -> TarkovSuccessResponse[List[dict]]:
    bots: List[dict] = []
    request_data: dict = await request.json()

    logger.debug(request_data)
    for condition in request_data["conditions"]:
        bot_limit = condition["Limit"]

        for _ in range(bot_limit):
            bot = bot_generator.generate(bot_role="assault")
            bots.append(bot)

    return TarkovSuccessResponse(data=bots)
