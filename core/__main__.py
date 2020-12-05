from core.app import app
from core.package_manager import package_manager
import ujson
import core.utils

package_manager.load_packages()
app.run(ssl_context='adhoc')

