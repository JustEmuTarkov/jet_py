import sys

from server import app, logger, root_dir
from server.package_lib import PackageManager

if root_dir not in sys.path:
    sys.path.append(str(root_dir))

mods_dir = root_dir.joinpath('mods')

logger.debug(f'Searching for packages in: {mods_dir}')
package_manager = PackageManager(mods_dir)
package_manager.load_packages()

app.run(ssl_context='adhoc', port=443)
