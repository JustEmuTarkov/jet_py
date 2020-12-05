import sys
from pathlib import Path

from core.app import app
from core.main import root_dir
from core.package_manager import package_manager

if root_dir not in sys.path:
    sys.path.append(str(root_dir))


package_manager.load_packages()
app.run(ssl_context='adhoc')

