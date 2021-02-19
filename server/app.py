import typing
import zlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from server import root_dir
from tarkov.launcher.routes import launcher_router
from tarkov.mail.routes import mail_router
from tarkov.notifier.router import notifier_router
from tarkov.profile.routes import profile_router
from tarkov.fleamarket.routes import flea_market_router
from tarkov.routes.friend import friend_router
from tarkov.routes.hideout import hideout_router
from tarkov.routes.insurance import insurance_router
from tarkov.routes.lang import lang_router
from tarkov.routes.match import match_router
from tarkov.routes.misc import misc_router
from tarkov.routes.single_player import singleplayer_router
from tarkov.trader.routes import trader_router


class TarkovGZipMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response: StreamingResponse = typing.cast(StreamingResponse, await call_next(request))
        response_body: bytes = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Compression should apply only to json responses
        if "application/json" in response.headers["Content-Type"]:
            response_body = zlib.compress(response_body, zlib.Z_DEFAULT_COMPRESSION)
            response.headers["Content-Length"] = f"{len(response_body)}"
            response.headers["Content-Encoding"] = "deflate"

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


app = FastAPI()

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

app.mount(
    "/files",
    StaticFiles(directory=str(root_dir.joinpath("resources", "static"))),
    name="static",
)
