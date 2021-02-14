import zlib
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.datastructures import MutableHeaders


class ZLibRequest(Request):
    # pylint: disable=too-many-ancestors, attribute-defined-outside-init
    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            body = await super().body()
            try:
                self._body = zlib.decompress(body)
                headers = MutableHeaders(raw=self.scope["headers"])
                headers["Content-Length"] = str(len(self._body))
            except zlib.error:
                self._body = body
        return self._body


class ZLibRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = ZLibRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler
