from flask import Blueprint, request

from server import logger
from utils import route_decorator

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/ragfair/find', methods=['POST', 'GET'])
@route_decorator()
def find():
    logger.debug(request.data)
    response = {
        'categories': {},
        'offers': [],
        'offersCount': 10,
        'selectedCategory': '5b5f78dc86f77409407a7f8e'
    }
    return response
