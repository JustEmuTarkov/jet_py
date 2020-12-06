import sys

from core.app import app
from core.logger import logger
from core.main import root_dir
from core.package_manager import package_manager

if root_dir not in sys.path:
    sys.path.append(str(root_dir))

logger.debug(f'sys.path is: {sys.path}')
package_manager.load_packages()
app.run(ssl_context='adhoc')
