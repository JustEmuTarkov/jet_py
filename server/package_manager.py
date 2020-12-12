from server.app import logger
from server.main import root_dir
from server.package_loader import PackageManager


mods_dir = root_dir / 'mods'
logger.debug(f'Searching for packages in: {mods_dir}')
package_manager = PackageManager(mods_dir)
