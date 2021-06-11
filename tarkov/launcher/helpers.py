from typing import List
from server import db_dir


def available_editions() -> List[str]:
    editions_dirs = [d for d in db_dir.joinpath("profile").glob("*") if d.is_dir()]
    return [d.name for d in editions_dirs]