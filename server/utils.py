import random
import string
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.requests import Request

from server.requests import ZLibRoute
from server.responses import ZLibORJSONResponse


def atomic_write(str_: str, path: Path, *, encoding: str = "utf8") -> None:
    random_str = "".join(
        random.choices([*string.ascii_lowercase, *string.digits], k=16)
    )
    tmp_path = Path(str(path) + random_str)

    try:
        with tmp_path.open(mode="w", encoding=encoding) as tmp_file:
            tmp_file.write(str_)

        # tmp_path.rename(path)
        tmp_path.replace(path)
    finally:
        tmp_path.unlink(missing_ok=True)


def get_request_url_root(request: Request) -> str:
    return f'{str(request.base_url).rstrip("/")}:443'


def make_router(**kwargs: Any) -> APIRouter:
    router = APIRouter(**kwargs)
    router.default_response_class = ZLibORJSONResponse
    router.route_class = ZLibRoute
    return router
