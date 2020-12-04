from functools import lru_cache

import ujson

from core.app import app
from core.main import package_manager, root_dir
from core.package_lib import PackageMeta, BasePackage
from core.utils import TarkovResponseStruct, ZlibMiddleware, static_route


@package_manager.register
class Package(BasePackage):
    class Meta(PackageMeta):
        name = 'core'
        version = '0.0.1'
        dependencies = []

    def on_load(self):
        @app.route('/client/locations')
        @static_route
        def client_locations():
            print('Function called for first time')
            locations_base = root_dir / 'resources' / 'db' / 'cacheBase' / 'locations.json'
            locations_base = ujson.load(locations_base.open('r'))

            for file in (root_dir / 'resources' / 'db' / 'locations').glob('*.json'):
                map_name, map_contents = file.stem, ujson.load(file.open('r'))['base']
                locations_base['locations'][map_name] = map_contents

            return locations_base
