from __future__ import annotations

import importlib
from pathlib import Path
from typing import Dict, Iterable, List, Set, Type, Union

from server import logger, root_dir


class PackageMeta:
    name: str = ""
    version: str = ""
    dependencies: Union[Set[str], List[str]] = []


class PackageBase:
    Meta: PackageMeta

    def __init__(self) -> None:
        pass

    def on_load(self) -> None:
        pass

    def __str__(self) -> str:
        return f"{self.Meta.name} - {self.Meta.version}"


class UnresolvedPackageError(Exception):
    pass


class NoBasePackageError(Exception):
    pass


class CycleDependencyError(Exception):
    def __init__(self, package: PackageType, dependencies: PackageTypeList):
        super().__init__()
        self.package = package
        self.dependencies = dependencies

    def __str__(self) -> str:
        dependencies = ", ".join(dep.Meta.name for dep in self.dependencies)
        return f"{self.package.Meta.name}: [{dependencies}]"


PackageType = Type[PackageBase]
PackageTypeList = List[PackageType]


class PackageTopologicalSorter:
    def __init__(self, packages: PackageTypeList):
        self.packages = packages

    def __get_package_with_name(self, name: str) -> PackageType:
        try:
            return next(pkg for pkg in self.packages if pkg.Meta.name == name)
        except StopIteration as error:
            raise UnresolvedPackageError(name) from error

    def get_load_order(self) -> PackageTypeList:
        in_order: PackageTypeList = []

        dependency_graph: Dict[PackageType, PackageTypeList] = {
            pkg: [self.__get_package_with_name(name) for name in pkg.Meta.dependencies]
            for pkg in self.packages
        }

        logger.debug(f"Dependency graph: {dependency_graph}")
        pkg_with_no_deps = [
            pkg for pkg, pkg_deps in dependency_graph.items() if not pkg_deps
        ]
        logger.debug(f"pkg_with_no_deps: {pkg_with_no_deps}")
        if not pkg_with_no_deps and dependency_graph:
            raise NoBasePackageError

        dependency_graph = {
            pkg: [d for d in deps if d not in pkg_with_no_deps]
            for pkg, deps in dependency_graph.items()
            if pkg not in pkg_with_no_deps
        }

        while pkg_with_no_deps:
            pkg = pkg_with_no_deps.pop()
            in_order.append(pkg)
            for package, dependencies in dependency_graph.items():
                try:
                    dependencies.remove(pkg)
                except ValueError:
                    pass
                if not dependencies:
                    pkg_with_no_deps.append(package)
                    del dependency_graph[package]
                    break

        if dependency_graph:
            logger.debug(dependency_graph)
            for pkg, deps in dependency_graph.items():
                raise CycleDependencyError(package=pkg, dependencies=deps)

        return in_order


class PackageManager:
    def __init__(self, packages_path: Path):
        self.packages_dir = packages_path
        self.packages: List[Type[PackageBase]] = []

    def register(self, package: Type[PackageBase]) -> None:
        self.packages.append(package)

    def load_packages(self) -> None:
        self.__import_packages()
        self.__load_packages()

    def __import_packages(self) -> None:
        """
        Imports top-level packages in self.packages_dir directory
        """
        for module_path in (d for d in self.packages_dir.glob("*") if d.is_dir()):
            module_name = ".".join(module_path.relative_to(root_dir).parts)

            module = importlib.import_module(module_name)
            if hasattr(module, "Package"):
                package: Type[PackageBase] = getattr(module, "Package")
                logger.debug(f"Package import: {package.Meta.name}")
                self.register(package)

    def __load_packages(self) -> None:
        """
        Executes packages on_load method
        """
        order = self.__get_load_order()
        for package in order:
            package_instance = package()
            logger.debug(f"Package load: {str(package_instance)}")
            package_instance.on_load()

    def __get_load_order(self) -> Iterable[Type[PackageBase]]:
        """
        Sorts packages to load them in correct order
        """
        sorter = PackageTopologicalSorter(self.packages)
        return sorter.get_load_order()
