import datetime
import logging
import sys
from logging import LogRecord, StreamHandler
from pathlib import Path
from typing import Optional


if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    root_dir = Path(sys.executable).parent.absolute()
else:
    root_dir = Path(__file__).parent.parent.absolute()

db_dir = root_dir.joinpath("resources", "db")
start_time = datetime.datetime.now()


class LogFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        return f"[{self.formatTime(record)}][{record.levelname}] {record.msg}"

    def formatTime(self, record: LogRecord, datefmt: Optional[str] = None) -> str:
        return super().formatTime(record, datefmt="%H:%M:%S")


logger = logging.Logger("main")

console_handler = StreamHandler()
console_handler.formatter = LogFormatter()
logger.addHandler(console_handler)
