from flask import request

from server import logger
from server.utils import make_router
from tarkov.models import TarkovSuccessResponse

flea_market_router = make_router(tags=['FleaMarket'])


@flea_market_router.post('/client/ragfair/find')
def find() -> TarkovSuccessResponse:
    logger.debug(request.data)
    return TarkovSuccessResponse(data={
        'categories': {},
        'offers': [],
        'offersCount': 10,
        'selectedCategory': '5b5f78dc86f77409407a7f8e'
    })
