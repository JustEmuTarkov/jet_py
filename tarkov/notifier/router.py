import asyncio
from typing import Optional

import orjson
from dependency_injector.wiring import Provide, inject
from fastapi import Request
from fastapi.params import Cookie, Depends
from fastapi.responses import PlainTextResponse

from server import logger
from server.container import AppContainer
from server.utils import get_request_url_root, make_router
from tarkov.models import TarkovSuccessResponse
from .notifier import NotifierService

notifier_router = make_router(tags=["NotifierService"])


@notifier_router.post("/client/notifier/channel/create")
def client_notifier_channel_create(
    request: Request,
    profile_id: Optional[str] = Cookie(alias="PHPSESSID", default=None),
) -> TarkovSuccessResponse[dict]:
    url_root = get_request_url_root(request).rstrip("/")
    notifier_server_url = f"{url_root}/notifierServer/get/{profile_id}"
    response = {
        "notifier": {
            "server": f"{url_root}/",
            "channel_id": "testChannel",
            "url": notifier_server_url,
        },
        "notifierServer": notifier_server_url,
    }
    return TarkovSuccessResponse(data=response)


@notifier_router.get("/notifierServer/get/{profile_id}")
@inject
async def notifierserver_get(
    profile_id: str,
    notifier: NotifierService = Depends(Provide[AppContainer.notifier.service]),
) -> PlainTextResponse:
    for _ in range(90):
        if notifier.has_notifications(profile_id):
            notifications = notifier.get_notifications_view(profile_id)
            logger.debug(f"New notifications for profile {profile_id}")
            logger.debug(notifications)
            response = "\n".join(
                [
                    orjson.dumps(notification).decode("utf8")
                    for notification in notifications
                ]
            )
            logger.debug(f"NotifierService response: {response}")
            return PlainTextResponse(
                content=response,
                media_type="application/json",
            )
        await asyncio.sleep(1)

    return PlainTextResponse(
        content=orjson.dumps({"type": "ping", "eventId": "ping"}),
        media_type="application/json",
    )
