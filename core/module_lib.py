from copy import copy
from typing import List, Dict


class PackageMeta:
    name: str
    version: str
    dependencies: List[str]


class UnresolvedPackageException(Exception):
    pass


class PackageTopologicalSorter:
    def __init__(self, modules: List[PackageMeta]):
        self.modules = modules

    def get_load_order(self):
        dependency_graph: Dict[PackageMeta, List[str]] = {meta: copy(meta.dependencies) for meta in self.modules}

        # Construct sets of package names and package dependencies names
        package_names = set(meta.name for meta in dependency_graph.keys())
        package_dependencies_names = set(dep for meta in dependency_graph.keys() for dep in meta.dependencies)

        # If we have dependencies that are not in list of self.modules then raise an exception
        if not package_names.issuperset(package_dependencies_names):
            unresolved_modules = package_dependencies_names.difference(package_names)
            unresolved_modules_str = '\n'.join(unresolved_modules)
            raise UnresolvedPackageException(
                f'Unresolved dependencies: {unresolved_modules_str}'
            )

        load_order = []
        while dependency_graph:
            for meta, dependencies in dependency_graph.items():
                if not dependencies:
                    for deps in dependency_graph.values():
                        if meta.name in deps:
                            deps.remove(meta.name)

                    load_order.append(meta)
                    del dependency_graph[meta]
                    break

        return load_order
