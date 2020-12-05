import datetime
import sys
from pathlib import Path

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    root_dir = Path().absolute()
else:
    root_dir = Path().absolute().parent
db_dir = root_dir / 'resources' / 'db'
start_time = datetime.datetime.now()
