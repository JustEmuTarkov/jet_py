import importlib
import importlib.machinery
import importlib.util
from pathlib import Path
from typing import Type, Iterable, List

from core.logger import logger
from core.main import root_dir
from core.package_lib import PackageTopologicalSorter, BasePackage


class PackageManager:
    def __init__(self, packages_path: Path):
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

    def __import_packages(self):
        """
        Imports top-level packages in self.packages_dir directory
        """
        for package in (d for d in self.packages_dir.glob('*') if d.is_dir()):
            package_name = str(package.relative_to(root_dir)).replace('\\', '.')
            package = importlib.import_module(package_name)

            if hasattr(package, 'Package'):
                package = getattr(package, 'Package')
                self.register(package)

    def __load_packages(self):
        """
        Executes packages on_load method
        """
        order = self.__get_load_order()
        for package in order:
            logger.debug(f'Package load: {package.Meta.name}')
            package.on_load()

    def __get_load_order(self) -> Iterable[BasePackage]:
        """
        Sorts packages to load them in correct order
        """
        sorter = PackageTopologicalSorter(self.packages)
        return sorter.get_load_order()
