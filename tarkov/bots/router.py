from typing import List

import ujson
from starlette.requests import Request

from server import db_dir, logger
from server.utils import make_router
from tarkov.bots.bots import BotGenerator
from tarkov.models import TarkovSuccessResponse

bots_router = make_router(tags=["Bots"])


@bots_router.get("/singleplayer/settings/bot/difficulty/{type_}/{difficulty}")
def bot_difficulty_settings(type_: str, difficulty: str) -> dict:
    if type_ == "core":
        return ujson.load(db_dir.joinpath("base", "botCore.json").open(encoding="utf8"))

    bot_file = db_dir.joinpath("bots", type_, "difficulty", f"{difficulty}.json").open(encoding="utf8")

    return ujson.load(bot_file)


@bots_router.get("/singleplayer/settings/bot/limit/{bot_type}")
def settings_bot_limit(bot_type: str) -> int:  # pylint: disable=unused-argument
    return 30


@bots_router.post("/client/game/bot/generate")
async def generate_bots(request: Request) -> TarkovSuccessResponse[List[dict]]:
    bots: List[dict] = []
    request_data: dict = await request.json()

    logger.debug(request_data)
    for condition in request_data["conditions"]:
        # TODO: FixMe
        bot_generator = BotGenerator(bot_role="assault")  # condition["Role"]
        bot_limit = condition["Limit"]

        for _ in range(bot_limit):
            bot = bot_generator.generate()
            bots.append(bot)

    return TarkovSuccessResponse(data=bots)
