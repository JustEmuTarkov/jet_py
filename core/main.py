import sys
from pathlib import Path

from core.package_loader import PackageManager

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    root_dir = Path().absolute()
else:
    root_dir = Path().absolute().parent

package_manager = PackageManager(root_dir / 'mods')
