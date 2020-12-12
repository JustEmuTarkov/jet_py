from typing import List, Dict, Union, Set

from server.app import logger


class PackageMeta:
    name: str
    version: str
    dependencies: Union[Set[str], List[str]]


class BasePackage:
    Meta: PackageMeta

    def __init__(self):
        pass

    def on_load(self):
        pass


class UnresolvedPackageError(Exception):
    pass


class NoBasePackageError(Exception):
    pass


class CycleDependencyError(Exception):
    def __init__(self, package: BasePackage, dependencies: List[BasePackage]):
        super().__init__()
        self.package = package
        self.dependencies = dependencies

    def __str__(self):
        dependencies = ', '.join(dep.Meta.name for dep in self.dependencies)
        return f'{self.package.Meta.name}: [{dependencies}]'


class PackageTopologicalSorter:
    def __init__(self, packages: List[BasePackage]):
        self.packages = packages

    def __get_package_with_name(self, name: str):
        try:
            return next(pkg for pkg in self.packages if pkg.Meta.name == name)
        except StopIteration:
            raise UnresolvedPackageError(name)

    def get_load_order(self) -> List[BasePackage]:
        in_order: List[BasePackage] = []
        dependency_graph: Dict[BasePackage, List[BasePackage]] = {
            pkg: [self.__get_package_with_name(name) for name in pkg.Meta.dependencies]
            for pkg in self.packages
        }

        logger.debug(f'Dependency graph: {dependency_graph}')
        pkg_with_no_deps = [pkg for pkg, pkg_deps in dependency_graph.items() if not pkg_deps]
        logger.debug(f'pkg_with_no_deps: {pkg_with_no_deps}')
        if not pkg_with_no_deps and dependency_graph:
            raise NoBasePackageError

        for s in pkg_with_no_deps:
            del dependency_graph[s]

        for dependencies in dependency_graph.values():
            for pkg in pkg_with_no_deps:
                try:
                    dependencies.remove(pkg)
                except ValueError:
                    pass

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
            print(dependency_graph)
            for pkg, deps in dependency_graph.items():
                raise CycleDependencyError(package=pkg, dependencies=deps)

        return in_order
