import datetime
import logging
from logging import LogRecord, StreamHandler
from pathlib import Path
from typing import List, Optional

import flask
import flask.cli
import werkzeug.serving
from flask import Flask

app = Flask(__name__)


class LogFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        return f'[{self.formatTime(record)}][{record.levelname}] {record.msg}'

    def formatTime(self, record: LogRecord, datefmt: Optional[str] = None) -> str:
        return super().formatTime(record, datefmt='%H:%M:%S')


logger = logging.Logger('main')

console_handler = StreamHandler()
console_handler.formatter = LogFormatter()
logger.addHandler(console_handler)


# pylint: disable=unused-argument
def show_server_banner(env, debug, app_import_path, eager_loading):
    pass


flask.cli.show_server_banner = show_server_banner


def custom_startup_log(*args):
    args: List[str]
    if not args[1].startswith(' * Running on'):
        return
    logger.info(args[1] % args[2:])


# pylint: disable=protected-access
werkzeug.serving._log = custom_startup_log


@app.after_request
def after(response):
    request = flask.request
    remote_addr = request.remote_addr
    url = request.url
    method = request.method
    logger.info(msg=f'[{remote_addr}] {url} {method} {response.status_code}')

    return response


root_dir = Path().absolute()
logger.debug(f'Server root directory is: {root_dir}')

db_dir = root_dir.joinpath('resources', 'db')
start_time = datetime.datetime.now()
