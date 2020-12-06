import importlib
import importlib.machinery
import importlib.util
import pkgutil
import sys
from importlib.machinery import SourceFileLoader, FileFinder
from pathlib import Path
from pkgutil import ModuleInfo
from typing import Optional, Type, Iterable, List

from core.logger import logger
from core.main import root_dir
from core.package_lib import PackageTopologicalSorter, BasePackage


class PackageManager:
    def __init__(self, packages_path: Optional[Path]):
        self.packages_dir = packages_path
        self.packages: List[BasePackage] = []

    def register(self, package: Type[BasePackage]):
        logger.debug(f'Package import: {package.Meta.name}')
        package_instance = package()
        self.packages.append(package_instance)
        return package

    def load_packages(self):
        self.__import_packages()
        self.__load_packages()

    @staticmethod
    def get_module_name(module_info: ModuleInfo) -> str:
        path = module_info.module_finder.path
        module_name = module_info.name
        if type(path) == str:
            path = Path(path)

        if path.stem == '__init__':
            rel_path = path.parent.relative_to(root_dir)
        else:
            rel_path = path.relative_to(root_dir)

        rel_path_str = str(rel_path)
        module_rel_path = rel_path_str.replace('\\', '.')
        return '.'.join([module_rel_path, module_name])

    def __import_packages(self):
        packages_dir = str(self.packages_dir)
        for module_info in pkgutil.iter_modules([packages_dir]):
            module_info: ModuleInfo

            finder: FileFinder = module_info.module_finder
            module_spec = finder.find_spec(module_info.name)

            module = importlib.util.module_from_spec(spec=module_spec)
            loader: Optional[SourceFileLoader] = module_spec.loader
            if not loader:
                continue

            module_name = PackageManager.get_module_name(module_info=module_info)

            sys.modules[module_name] = module

            module = importlib.import_module(module_name)

            logger.debug(f'Trying to load module "{module_name}" from path {finder.path}')
            loader.exec_module(module)

            if hasattr(module, 'Package'):
                package = getattr(module, 'Package')
                self.register(package)

    def __load_packages(self):
        order = self.__get_load_order()
        for package in order:
            logger.debug(f'Package load: {package.Meta.name}')
            package.on_load()

    @staticmethod
    def __is_like_package(path: Path):
        return path.is_dir() and (path / '__init__.py').exists()

    def __get_load_order(self) -> Iterable[BasePackage]:
        sorter = PackageTopologicalSorter(self.packages)
        return sorter.get_load_order()
