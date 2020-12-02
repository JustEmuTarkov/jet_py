import argparse
import json
from pathlib import Path


def dump_database(from_: Path, to: Path):
    db = {}
    db_path = from_

    for file in db_path.glob('**/*.json'):
        parts = str(file.relative_to(db_path)).split('\\')

        if file.is_file():
            db_ref = db
            for part in parts[:-1]:
                try:
                    db_ref = db_ref[part]
                except KeyError:
                    db_ref[part] = {}
                    db_ref = db_ref[part]

            last = parts[-1]
            db_ref['_'.join(last.split('.')[:-1])] = json.load(file.open('r', encoding='utf8'))

    json.dump(db, to.open('w'), separators=(',', ':'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dumps the jet db folder into one .json file.')
    parser.add_argument('--from', dest='from_', type=str, help='Path to the db folder', required=True)
    parser.add_argument('--to', type=str, help='Path to file (It will be created or re-written)', default='db.json')

    args = parser.parse_args()
    dump_database(Path(args.from_), Path(args.to))
