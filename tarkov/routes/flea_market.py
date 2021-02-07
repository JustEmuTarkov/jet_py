from flask import Blueprint, request

from server import logger
from utils import tarkov_response, zlib_middleware

blueprint = Blueprint(__name__, __name__)


@blueprint.route('/client/ragfair/find', methods=['POST', 'GET'])
@zlib_middleware
@tarkov_response
def find():
    logger.debug(request.data)
    response = {
        'categories': {},
        'offers': [],
        'offersCount': 10,
        'selectedCategory': '5b5f78dc86f77409407a7f8e'
    }
    return response
