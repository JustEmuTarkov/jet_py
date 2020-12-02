from copy import copy
from typing import List, Dict


class ModuleMeta:
    name: str
    version: str
    dependencies: List[str]


class UnresolvedModuleException(Exception):
    pass


class PackageTopologicalSorter:
    def __init__(self, modules: List[ModuleMeta]):
        self.modules = modules

    def get_load_order(self):
        dependency_graph: Dict[ModuleMeta, List[str]] = {meta: copy(meta.dependencies) for meta in self.modules}

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
            else:
                meta_names = list(meta.name for meta in dependency_graph.keys())

                for meta, dependencies in dependency_graph.items():
                    if any(dependency not in meta_names for dependency in dependencies):
                        unresolved_dependencies = list(d for d in dependencies if d not in meta_names)
                        raise UnresolvedModuleException(
                            f'Unresolved dependencies for module {meta.name}: {unresolved_dependencies}'
                        )

        return load_order
