from starlette.requests import Request

from server.utils import get_request_url_root, make_router

launcher_router = make_router(tags=["Launcher"])


@launcher_router.get("/launcher/server/connect")
async def connect(request: Request) -> dict:
    return {
        "backendUrl": get_request_url_root(request).rstrip("/"),
        "name": "Jet Py",
        "editions": ["Edge Of Darkness"],
    }


@launcher_router.post("/launcher/profile/login")
async def login() -> str:
    return "AID8131647517931710690RF"


@launcher_router.post("/launcher/profile/get")
async def get_profile():
    return {
        "id": "AID8131647517931710690RF",
        "nickname": "",
        "email": "",
        "password": "",
        "wipe": False,
        "edition": "Edge Of Darkness",
    }


# async def server_info():
#     return {
#         'ServerName': 'Jet Py',
#         'Editions': ['Edge Of Darkness']
#     }
