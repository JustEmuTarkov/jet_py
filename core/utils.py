import json
import zlib
from functools import wraps, lru_cache

import ujson
from flask import make_response, request


class ZlibMiddleware:
    def __init__(self, /, send_browser_headers=False):
        self.send_headers = send_browser_headers

    def __call__(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if request.data:
                request_body = ujson.loads(zlib.decompress(request))
                request.body = None
                print(request_body)
                print(request)

            # data decompression preparing happends here
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


def route_decorator(**kwargs):
    def wrapper(function):
        decorators = [function]
        use_struct = kwargs.get('use_tarkov_response_struct', True)
        if use_struct:
            decorators.append(TarkovResponseStruct())

        decorators.append(ZlibMiddleware(send_browser_headers=True))

        is_static = kwargs.get('is_static', False)
        if is_static:
            decorators.append(lru_cache(1))

        return compose(*decorators)

    return wrapper
