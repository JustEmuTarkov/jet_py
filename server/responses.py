import typing
import zlib

from fastapi.responses import ORJSONResponse


class ZLibORJSONResponse(ORJSONResponse):
    media_type = 'application/json'

    def init_headers(self, headers: typing.Mapping[str, str] = None) -> None:
        if not headers:
            headers = {}
        headers['Content-Encoding'] = 'deflate'  # type: ignore
        super().init_headers(headers)

    def render(self, content: dict) -> bytes:
        self.init_headers({'Content-Encoding': 'deflate'})
        content = zlib.compress(super().render(content))
        return content
