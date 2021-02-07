from flask import Blueprint, request

from server import logger
from server.utils import game_response_middleware

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/ragfair/find', methods=['POST', 'GET'])
@game_response_middleware()
def find():
    logger.debug(request.data)
    response = {
        'categories': {},
        'offers': [],
        'offersCount': 10,
        'selectedCategory': '5b5f78dc86f77409407a7f8e'
    }
    return response