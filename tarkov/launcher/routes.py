import zlib

from fastapi.params import Body
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from server.utils import get_request_url_root, make_router
from tarkov.exceptions import NotFoundError
from tarkov.launcher.accounts import account_service
from tarkov.launcher.models import Account

launcher_router = make_router(tags=["Launcher"])


@launcher_router.get("/launcher/server/connect")
async def connect(request: Request) -> dict:
    return {
        "backendUrl": get_request_url_root(request).rstrip("/"),
        "name": "Jet Py",
        "editions": ["Edge Of Darkness"],
    }


@launcher_router.post("/launcher/profile/login")
def login(
    email: str = Body(..., embed=True),  # type: ignore
    password: str = Body(..., embed=True),  # type: ignore
) -> PlainTextResponse:
    try:
        account_service.find(email=email, password=password)
        return PlainTextResponse(content=zlib.compress("OK".encode("utf8")))
    except NotFoundError:
        return PlainTextResponse(content=zlib.compress("FAILED".encode("utf8")))


@launcher_router.post("/launcher/profile/get")
async def get_profile(
    email: str = Body(..., embed=True),  # type: ignore
    password: str = Body(..., embed=True),  # type: ignore
) -> Account:
    return account_service.find(email, password)


@launcher_router.post(
    "/launcher/profile/register",
    response_class=PlainTextResponse,
)
def register_account(
    email: str = Body(..., embed=True),  # type: ignore
    password: str = Body(..., embed=True),  # type: ignore
    edition: str = Body(..., embed=True),  # type: ignore
) -> PlainTextResponse:
    try:
        account_service.find(email=email, password=password)
        return PlainTextResponse(content=zlib.compress("FAILED".encode("utf8")))
    except NotFoundError:
        account_service.create_account(
            email=email,
            password=password,
            edition=edition,
        )
        return PlainTextResponse(content=zlib.compress("OK".encode("utf8")))
