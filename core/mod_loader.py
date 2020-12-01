import importlib
import importlib.util
import importlib.machinery
import pathlib


def load_mods():
    root_dir = pathlib.Path().absolute().parent
    folders = (root_dir / 'mods').glob('*')
    folders = (folder for folder in folders if folder.is_dir())

    for mod in folders:
        spec = importlib.util.spec_from_file_location(mod.name, mod / '__init__.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
