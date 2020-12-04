import importlib
import importlib.machinery
import importlib.util
from pathlib import Path
from typing import Optional, Type, Iterable

from core.logger import logger
from core.package_lib import PackageMeta, PackageTopologicalSorter, BasePackage


class PackageManager:
    def __init__(self, packages_path: Optional[Path]):
        self.packages_dir = packages_path
        self.packages = []

    def register(self, package: Type[PackageMeta]):
        logger.debug(f'Package import: {package.Meta.name}')
        package_instance = package()
        self.packages.append(package_instance)
        return package

    def load_packages(self):
        self.__discover_packages()
        self.__load_packages()

    def __discover_packages(self):
        packages_paths = (path for path in self.packages_dir.glob('**/*') if PackageManager.__is_like_package(path))
        for package_path in packages_paths:
            relative_path = package_path.relative_to(self.packages_dir)
            relative_path = str(relative_path).replace('\\', '.')
            spec = importlib.util.spec_from_file_location(relative_path, package_path / '__init__.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        print(self.__get_load_order())

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
