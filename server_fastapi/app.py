import zlib

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, StreamingResponse

import tarkov.profile.routes
import tarkov.routes.friend
import tarkov.routes.hideout
import tarkov.routes.insurance
import tarkov.routes.lang
import tarkov.routes.misc
import tarkov.routes.single_player
import tarkov.trader.routes


class TarkovGZipMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response: StreamingResponse = await call_next(request)
        response_body: bytes = b''
        async for chunk in response.body_iterator:
            response_body += chunk

        compressed = zlib.compress(response_body, zlib.Z_DEFAULT_COMPRESSION)
        response.headers['Content-Length'] = f'{len(compressed)}'
        response.headers['Content-Encoding'] = 'deflate'

        return Response(
            content=compressed,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )


app = FastAPI()
app.add_middleware(TarkovGZipMiddleware)

app.include_router(router=tarkov.routes.friend.router)
app.include_router(router=tarkov.trader.routes.router)
app.include_router(router=tarkov.routes.hideout.router)
app.include_router(router=tarkov.routes.lang.router)
app.include_router(router=tarkov.routes.insurance.router)
app.include_router(router=tarkov.profile.routes.router)
app.include_router(router=tarkov.routes.single_player.router)
app.include_router(router=tarkov.routes.misc.router)
