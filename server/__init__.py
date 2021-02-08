import datetime
import logging
import sys
from logging import LogRecord, StreamHandler
from pathlib import Path
from typing import List, Optional

import flask
import flask.cli
import werkzeug.serving
from flask import Flask

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    root_dir = Path(sys.executable).parent.absolute()
else:
    root_dir = Path(__file__).parent.parent.absolute()

db_dir = root_dir.joinpath('resources', 'db')
start_time = datetime.datetime.now()

app = Flask(__name__, static_folder=str(root_dir.joinpath('resources', 'static')), static_url_path='/files')


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


def custom_startup_log(*args: str):
    if not args[1].startswith(' * Running on'):
        return
    logger.info(args[1] % args[2:])


# pylint: disable=protected-access
# noinspection PyTypeHints
werkzeug.serving._log = custom_startup_log  # type: ignore


@app.after_request
def after(response):
    request = flask.request
    remote_addr = request.remote_addr
    url = request.url
    method = request.method
    logger.info(msg=f'[{remote_addr}] {url} {method} {response.status_code}')

    return response
