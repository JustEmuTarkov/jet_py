import json
import zlib
from functools import wraps
from typing import Callable

import ujson
from flask import make_response, request


class ZlibMiddleware:
    def __init__(self, /, send_browser_headers=False):
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

                request.data = request_body

            data = function(*args, **kwargs)

            data_json = json.dumps(data)
            compressed_data = zlib.compress(data_json.encode('utf8'), zlib.Z_DEFAULT_COMPRESSION)

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
            decorators.append(memoize_once)

        return compose(*decorators)

    return wrapper


def memoize_once(function: Callable):
    """
    Memorizes first function call result and returns only it.
    Useful for static content - files or responses.

    This function doesn't take any argument it gets into consideration -
    e.g. if won't re-cache if it will be called with different arguments.

    """
    was_called = False
    result = None

    @wraps(function)
    def wrapper(*args, **kwargs):
        nonlocal result, was_called
        if not was_called:
            was_called = True
            result = function(*args, **kwargs)
        return result

    return wrapper
