from server.utils import make_router
from tarkov.models import TarkovSuccessResponse

friend_router = make_router(tags=['Friends'])


@friend_router.post('/client/friend/list')
def client_friend_list() -> TarkovSuccessResponse[dict]:
    return TarkovSuccessResponse(data={
        'Friends': [],
        'Ignore': [],
        'InIgnoreList': []
    })


@friend_router.post('/client/friend/request/list/inbox')
def client_friend_request_list_inbox() -> TarkovSuccessResponse[list]:
    return TarkovSuccessResponse(data=[])


@friend_router.post('/client/friend/request/list/outbox')
def client_friend_request_list_outbox() -> TarkovSuccessResponse[list]:
    return TarkovSuccessResponse(data=[])
