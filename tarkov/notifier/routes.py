import time
from typing import Dict, List, Optional, Union

import orjson
from fastapi import APIRouter
from fastapi.params import Cookie, Param
from starlette.requests import Request

import tarkov.profile
from server.utils import get_request_url_root
from tarkov.models import TarkovErrorResponse, TarkovSuccessResponse
from tarkov.notifier.notifier import notifier_instance

notifier_router = APIRouter(tags=['Notifier'])


@notifier_router.post('/client/mail/dialog/list')
def mail_dialog_list(
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None)  # type: ignore
) -> Union[TarkovSuccessResponse[List[Dict]], TarkovErrorResponse]:
    if not profile_id:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        return TarkovSuccessResponse(
            data=profile.notifier.view_dialogue_preview_list()
        )


@notifier_router.post('/client/mail/dialog/info')
def mail_dialog_info(
        dialogue_id: str = Param(alias='dialogId', default=None),  # type: ignore
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    if not dialogue_id:
        return TarkovErrorResponse(errmsg='No dialogue_id was provided')

    if not profile_id:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        dialogue_preview = profile.notifier.view_dialog_preview(dialogue_id=dialogue_id)
        return TarkovSuccessResponse(data=dialogue_preview)


@notifier_router.post('/client/mail/dialog/view')
def mail_dialog_view(
        dialogId: str,
        time_: float = Param(alias='time', default=0.0),  # type: ignore
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    dialogue_id: str = dialogId

    if not profile_id:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        return TarkovSuccessResponse(
            data=profile.notifier.view_dialog(dialogue_id=dialogue_id, time_=time_)
        )


@notifier_router.post('/client/mail/dialog/getAllAttachments')
def mail_dialog_all_attachments(
        dialogId: str,
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None),  # type: ignore
) -> Union[TarkovSuccessResponse[dict], TarkovErrorResponse]:
    dialogue_id = dialogId

    if profile_id is None:
        return TarkovErrorResponse.profile_id_is_none()

    with tarkov.profile.Profile(profile_id) as profile:
        return profile.notifier.all_attachments_view(dialogue_id=dialogue_id)


@notifier_router.get('/notifierServer/get/{profile_id}')
def notifierserver_get(profile_id: str) -> Union[dict, str]:
    for _ in range(15):  # Poll for 15 seconds
        if notifier_instance.has_notifications(profile_id):
            notifications = notifier_instance.get_notifications(profile_id)
            response = '\n'.join([orjson.dumps(notification).decode('utf8') for notification in notifications])
            return response

        time.sleep(1)

    return notifier_instance.get_empty_notification()


@notifier_router.post('/client/notifier/channel/create')
def client_notifier_channel_create(
        request: Request,
        profile_id: Optional[str] = Cookie(alias='PHPSESSID', default=None),  # type: ignore
) -> TarkovSuccessResponse[dict]:
    url_root = get_request_url_root(request).rstrip('/')
    notifier_server_url = f'{url_root}/notifierServer/get/{profile_id}'
    response = {
        'notifier': {
            'server': f'{url_root}/',
            'channel_id': 'testChannel',
            'url': notifier_server_url,
        },
        'notifierServer': notifier_server_url
    }
    return TarkovSuccessResponse(
        data=response
    )
