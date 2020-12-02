import logging
from logging import StreamHandler, LogRecord
from typing import Optional


class LogFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        return f'[{self.formatTime(record)}][{record.levelname}] {record.msg}'

    def formatTime(self, record: LogRecord, datefmt: Optional[str] = None) -> str:
        return super().formatTime(record, datefmt='%H:%M:%S')


logger = logging.Logger('main')

console_handler = StreamHandler()
console_handler.formatter = LogFormatter()
logger.addHandler(console_handler)
