import time
import traceback
from typing import Callable

from fastapi import FastAPI
import fastapi.exception_handlers
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from fastapi.responses import Response
from starlette.responses import JSONResponse

import tarkov
from server import logger, root_dir
from server.container import AppContainer
from server.package_lib import PackageManager
from tarkov.bots.router import bots_router
from tarkov.fleamarket.routes import flea_market_router
from tarkov.launcher.router import launcher_router
from tarkov.mail.routes import mail_router
from tarkov.notifier.router import notifier_router
from tarkov.offraid.router import offraid_router
from tarkov.profile.routes import profile_router
from tarkov.routes.friend import friend_router
from tarkov.routes.hideout import hideout_router
from tarkov.routes.insurance import insurance_router
from tarkov.routes.lang import lang_router
from tarkov.routes.match import match_router
from tarkov.routes.misc import misc_router
from tarkov.routes.single_player import singleplayer_router
from tarkov.trader.router import trader_router


class FastAPIWithContainer(FastAPI):
    container: AppContainer


container = AppContainer()
container.wire(packages=[tarkov])
container.offraid.config.from_yaml("./config/offraid.yaml")
container.insurance_config.from_yaml("./config/insurance.yaml")

app = FastAPIWithContainer()
app.container = container

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
app.include_router(offraid_router)

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


@app.exception_handler(RequestValidationError)
async def request_validation_exc_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    traceback.print_tb(tb=exc.__traceback__)
    return await fastapi.exception_handlers.request_validation_exception_handler(
        request,
        exc,
    )


package_manager = PackageManager(root_dir.joinpath("mods"))
package_manager.load_packages()
