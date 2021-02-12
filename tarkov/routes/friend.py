from fastapi import APIRouter

router = APIRouter(prefix='', tags=['Friends'])


@router.post('/client/friend/list')
def client_friend_list():
    return {
        'Friends': [],
        'Ignore': [],
        'InIgnoreList': []
    }


@router.post('/client/friend/request/list/inbox')
def client_friend_request_list_inbox():
    return []


@router.post('/client/friend/request/list/outbox')
def client_friend_request_list_outbox():
    return []
