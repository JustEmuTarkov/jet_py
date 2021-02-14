import asyncio
from typing import Dict, List, Optional, Union

import orjson
from fastapi.params import Cookie, Param
from starlette.requests import Request
from starlette.responses import PlainTextResponse

import tarkov.profile
from server.utils import get_request_url_root, make_router
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.notifier.notifier import notifier_instance
from tarkov.notifier.requests import GetAllAttachmentsRequest, MailDialogViewRequest

notifier_router = make_router(tags=["Notifier"])


@notifier_router.get(
    "/notifierServer/get/{profile_id}", response_class=PlainTextResponse
)
async def notifierserver_get(profile_id: str) -> bytes:
    for _ in range(15):  # Poll for 15 seconds
        if notifier_instance.has_notifications(profile_id):
            notifications = notifier_instance.get_notifications(profile_id)
            response = "\n".join(
                [
                    orjson.dumps(notification).decode("utf8")
                    for notification in notifications
                ]
            )
            return response.encode("utf8")

        await asyncio.sleep(1)
    return orjson.dumps(notifier_instance.get_empty_notification())


@notifier_router.post("/client/mail/dialog/list")
def mail_dialog_list(
    profile_id: Optional[str] = Cookie(alias="PHPSESSID", default=None)  # type: ignore
) -> Union[TarkovSuccessResponse[List[Dict]], TarkovErrorResponse]:
    if not profile_id:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        return TarkovSuccessResponse(data=profile.notifier.view_dialogue_preview_list())


@notifier_router.post("/client/mail/dialog/info")
def mail_dialog_info(
    dialogue_id: str = Param(alias="dialogId", default=None),  # type: ignore
    profile_id: Optional[str] = Cookie(alias="PHPSESSID", default=None),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if not dialogue_id:
        return TarkovErrorResponse(errmsg="No dialogue_id was provided")

    if not profile_id:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        dialogue_preview = profile.notifier.view_dialog_preview(dialogue_id=dialogue_id)
        return TarkovSuccessResponse(data=dialogue_preview)


@notifier_router.post("/client/mail/dialog/view")
async def mail_dialog_view(
    request: MailDialogViewRequest,
    profile_id: Optional[str] = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if not profile_id:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        return TarkovSuccessResponse(
            data=profile.notifier.view_dialog(
                dialogue_id=request.dialogue_id, time_=request.time
            )
        )


@notifier_router.post("/client/mail/dialog/getAllAttachments")
def mail_dialog_all_attachments(
    request: GetAllAttachmentsRequest,
    profile_id: Optional[str] = Cookie(alias="PHPSESSID", default=None),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if profile_id is None:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        return TarkovSuccessResponse(
            data=profile.notifier.all_attachments_view(dialogue_id=request.dialogue_id)
        )


@notifier_router.post("/client/notifier/channel/create")
def client_notifier_channel_create(
    request: Request,
    profile_id: Optional[str] = Cookie(alias="PHPSESSID", default=None),  # type: ignore
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
