import json
import zlib
from functools import wraps

from flask import make_response


class ZlibMiddleware:
    def __init__(self, send_headers=False):
        self.send_headers = send_headers

    def __call__(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            kwargs['json_data'] = {
                'The meaning of life': 42
            }

            data = function(*args, **kwargs)

            data_json = json.dumps(data)
            compressed_data = zlib.compress(data_json.encode('utf8'), 9)

            response = make_response()

            if self.send_headers:
                response.headers['Content-Encoding'] = 'deflate'

            response.data = compressed_data
            return response

        return wrapper
