import importlib
import os
import string
from pathlib import Path

from core.app import app
from core.logger import logger

print('Loading Core Modules')


@app.route('/credits')
def _credits():
    return 'credits'


def local_load_libs(name):
    # logger.debug(f"Loading: {name}")
    curr_loc_arr = __file__.split('\\')[0:-1]
    curr_loc_arr.append(name)
    path = '\\'.join(curr_loc_arr)
    spec = importlib.util.spec_from_file_location('.'.join(curr_loc_arr), f"{path}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return


local_load_libs('routes')

