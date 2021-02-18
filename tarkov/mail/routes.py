from typing import Dict, List, Optional, Union

from fastapi.params import Cookie, Param

import tarkov.profile
from server.utils import make_router
from tarkov.mail.requests import GetAllAttachmentsRequest, MailDialogViewRequest
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse

mail_router = make_router(tags=["Notifier"])


@mail_router.post("/client/mail/dialog/list")
def mail_dialog_list(
    profile_id: Optional[str] = Cookie(alias="PHPSESSID", default=None)  # type: ignore
) -> Union[TarkovSuccessResponse[List[Dict]], TarkovErrorResponse]:
    if not profile_id:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        return TarkovSuccessResponse(data=profile.notifier.view_dialogue_preview_list())


@mail_router.post("/client/mail/dialog/info")
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


@mail_router.post("/client/mail/dialog/view")
async def mail_dialog_view(
    request: MailDialogViewRequest,
    profile_id: Optional[str] = Cookie(..., alias="PHPSESSID"),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if not profile_id:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        return TarkovSuccessResponse(
            data=profile.notifier.view_dialog(dialogue_id=request.dialogue_id, time_=request.time)
        )


@mail_router.post("/client/mail/dialog/getAllAttachments")
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
