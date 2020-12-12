import datetime
from pathlib import Path

from server.app import logger

root_dir = Path().absolute()
logger.debug(f'Server root directory is: {root_dir}')

db_dir = root_dir.joinpath('resources', 'db')
start_time = datetime.datetime.now()
