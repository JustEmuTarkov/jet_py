import sys

from server.app import app, logger
from server.main import root_dir
from server.package_manager import package_manager

if root_dir not in sys.path:
    sys.path.append(str(root_dir))

logger.debug(f'sys.path is: {sys.path}')
package_manager.load_packages()
app.run(ssl_context='adhoc')
