import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import List, Tuple

from core import mod_loader
from core.app import app
from core.logger import logger
from core.module_lib import PackageTopologicalSorter, ModuleMeta

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    root_dir = Path().absolute()
else:
    root_dir = Path().absolute().parent

if __name__ == '__main__':
    logger.debug(f'Root directory is: {str(root_dir)}')
    #  Load all the packages in root/mods dir
    packages = mod_loader.load_packages(root_dir / 'mods')

    logger.debug('Packages and metas:')
    for meta, package in packages.items():
        logger.debug(f'\t{meta}, {package}')

    logger.debug('Discovered packages:')
    for meta, package in packages.items():
        logger.debug(f'\t{meta.name} version {meta.version}')

    sorter = PackageTopologicalSorter(list(packages.keys()))
    load_order = sorter.get_load_order()
    logger.debug(f'Load order: {[load_order]}')
    logger.debug(f'Load order: {[mod.name for mod in load_order]}')


    def get_module_index(meta_module):
        meta, module = meta_module
        return load_order.index(meta)


    #  Sort packages by their order
    modules_in_order: List[Tuple[ModuleMeta, ModuleType]] = sorted(packages.items(), key=get_module_index)

    #  Execute packages __main__.py files in order
    for meta, package in modules_in_order:
        package = package
        path_to_main = Path(next(iter(package.__path__))) / '__main__.py'

        spec = importlib.util.spec_from_file_location(meta.name, path_to_main)
        main = importlib.util.module_from_spec(spec)
        logger.debug(f'Executing {path_to_main}')
        spec.loader.exec_module(package)

    app.run(ssl_context='adhoc')
