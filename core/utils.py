import json
import zlib
from functools import wraps, lru_cache

from flask import make_response


class ZlibMiddleware:
    def __init__(self, /, send_browser_headers=False):
        self.send_headers = send_browser_headers

    def __call__(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            data = function(*args, **kwargs)

            data_json = json.dumps(data)
            compressed_data = zlib.compress(data_json.encode('utf8'), 9)

            response = make_response()

            if self.send_headers:
                response.headers['Content-Encoding'] = 'deflate'
                response.headers['Content-Type'] = 'application/json'

            response.data = compressed_data
            return response

        return wrapper


class TarkovError(Exception):
    def __init__(self, err: int, errmsg: str):
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


def compose(function, *decorators):
    wrapped = function
    for deco in decorators:
        wrapped = deco(wrapped)
    return wrapped


def static_route(function):
    return compose(
        function,
        TarkovResponseStruct(),
        ZlibMiddleware(send_browser_headers=True),
        lru_cache(1),
    )
