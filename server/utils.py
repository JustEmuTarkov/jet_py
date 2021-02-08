import zlib
from functools import wraps
from typing import Callable, Optional

import ujson
from flask import make_response, request


class _ZlibMiddleware:
    def __init__(self, /, send_browser_headers=False) -> None:
        self.send_headers = send_browser_headers

    def __call__(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if request.data:
                data: bytes = request.data
                data = zlib.decompress(data)
                if data:
                    request_body = ujson.loads(data)
                else:
                    request_body = {}

                request.data = request_body  # type: ignore

            data: dict = function(*args, **kwargs)
            data_json: str = ujson.dumps(data)

            compressed_data = zlib.compress(data_json.encode('utf8'), zlib.Z_DEFAULT_COMPRESSION)

            response = make_response()

            if self.send_headers:
                response.headers['Content-Encoding'] = 'deflate'
                response.headers['Content-Type'] = 'application/json'

            response.data = compressed_data
            return response

        return wrapper


def zlib_middleware(function: Optional[Callable] = None, /, send_browser_headers=True) -> Callable:
    middleware = _ZlibMiddleware(send_browser_headers=send_browser_headers)
    if function is None:
        return middleware
    else:
        return middleware(function)


class TarkovError(Exception):
    def __init__(self, err: int, errmsg: str):
        super().__init__(self)
        self.err = err
        self.errmsg = errmsg


class TarkovResponseStruct:
    def __init__(self):
        pass

    def __call__(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                data = function(*args, **kwargs)
                return {
                    'err': 0,
                    'errmsg': None,
                    'data': data,
                }
            except TarkovError as e:
                return {
                    'err': e.err,
                    'errmsg': e.errmsg,
                    'data': None,
                }

        return wrapper


def tarkov_response(function: Optional[Callable]):
    middleware = TarkovResponseStruct()
    if function is None:
        return middleware
    else:
        return middleware(function)
