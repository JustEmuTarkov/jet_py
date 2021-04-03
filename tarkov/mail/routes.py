from typing import Dict, List, Union

from fastapi.params import Body, Depends

from server.utils import make_router
from tarkov.dependencies import profile_manager
from tarkov.mail.requests import GetAllAttachmentsRequest, MailDialogViewRequest
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.profile import Profile

mail_router = make_router(tags=["Notifier"])


@mail_router.post("/client/mail/dialog/list")
def mail_dialog_list(
    profile: Profile = Depends(profile_manager.with_profile),  # type: ignore
) -> Union[TarkovSuccessResponse[List[Dict]], TarkovErrorResponse]:
    return TarkovSuccessResponse(data=profile.mail.view.view_dialogue_preview_list())


@mail_router.post("/client/mail/dialog/info")
async def mail_dialog_info(
    dialogue_id: str = Body(..., alias="dialogId", embed=True),  # type: ignore
    profile: Profile = Depends(profile_manager.with_profile),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    dialogue_preview = profile.mail.view.view_dialog_preview(dialogue_id=dialogue_id)
    return TarkovSuccessResponse(data=dialogue_preview)


@mail_router.post("/client/mail/dialog/view")
def mail_dialog_view(
    request: MailDialogViewRequest,
    profile: Profile = Depends(profile_manager.with_profile),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    return TarkovSuccessResponse(
        data=profile.mail.view.view_dialog(dialogue_id=request.dialogue_id, time_=request.time)
    )


@mail_router.post("/client/mail/dialog/getAllAttachments")
def mail_dialog_all_attachments(
    request: GetAllAttachmentsRequest,
    profile: Profile = Depends(profile_manager.with_profile),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    return TarkovSuccessResponse(data=profile.mail.view.all_attachments_view(dialogue_id=request.dialogue_id))
