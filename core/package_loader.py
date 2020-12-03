import importlib
import importlib.machinery
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Dict

from core.logger import logger
from core.main import root_dir
from core.package_lib import PackageMeta


def load_packages(path: Path) -> Dict[PackageMeta, ModuleType]:
    folders = (folder for folder in path.glob('*') if folder.is_dir())

    packages: Dict[PackageMeta, ModuleType] = {}

    for pkg_path in folders:
        logger.debug(f'Trying to load module {pkg_path}')

        relative_path = pkg_path.relative_to(root_dir)
        # package_name = str(relative_path).replace('\\', '.')
        # print(package_name)
        logger.debug(f'Relative path: {pkg_path.relative_to(root_dir)}')

        # package = importlib.import_module(package_name)
        # print(dir(package))
        # print(package.__path__)
        spec = importlib.util.spec_from_file_location(pkg_path.name, pkg_path / '__init__.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        packages[module.Meta] = module

    return packages