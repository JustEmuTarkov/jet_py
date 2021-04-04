import time
from typing import Callable

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import Response

import tarkov
from server import logger, root_dir
from server.container import AppContainer
from server.package_lib import PackageManager
from tarkov.bots.router import bots_router
from tarkov.fleamarket.routes import flea_market_router
from tarkov.launcher.routes import launcher_router
from tarkov.mail.routes import mail_router
from tarkov.notifier.router import notifier_router
from tarkov.profile.routes import profile_router
from tarkov.routes.friend import friend_router
from tarkov.routes.hideout import hideout_router
from tarkov.routes.insurance import insurance_router
from tarkov.routes.lang import lang_router
from tarkov.routes.match import match_router
from tarkov.routes.misc import misc_router
from tarkov.routes.single_player import singleplayer_router
from tarkov.trader.routes import trader_router

app = FastAPI()
app.container = AppContainer()
app.container.wire(packages=[tarkov])

app.include_router(mail_router)
app.include_router(notifier_router)

app.include_router(trader_router)
app.include_router(profile_router)

app.include_router(friend_router)
app.include_router(hideout_router)
app.include_router(lang_router)
app.include_router(insurance_router)
app.include_router(singleplayer_router)
app.include_router(misc_router)
app.include_router(flea_market_router)
app.include_router(match_router)
app.include_router(launcher_router)
app.include_router(bots_router)

app.mount(
    "/files",
    StaticFiles(directory=str(root_dir.joinpath("resources", "static"))),
    name="static",
)


@app.middleware("http")
async def log_response_time(request: Request, call_next: Callable) -> Response:
    start_time = time.time()
    response = await call_next(request)
    response_time = round(time.time() - start_time, 3)
    logger.debug(f"Response time: {response_time}s")
    return response


package_manager = PackageManager(root_dir.joinpath("mods"))
package_manager.load_packages()
