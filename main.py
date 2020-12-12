import sys

from server.app import app, logger
from server.main import root_dir
from server.package_lib import PackageManager

if root_dir not in sys.path:
    sys.path.append(str(root_dir))

logger.debug(f'sys.path is: {sys.path}')
mods_dir = root_dir.joinpath('mods')

logger.debug(f'Searching for packages in: {mods_dir}')
package_manager = PackageManager(mods_dir)
package_manager.load_packages()

app.run(ssl_context='adhoc')
