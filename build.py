from pathlib import Path

import PyInstaller.__main__

PyInstaller.__main__.run([
    'core/__main__.py',
    '--onefile',
    '--console',
    '--icon=small_logo.ico',
    '--distpath=./',
])

bundle_path = (Path() / '__main__.exe').absolute()
new_path = bundle_path.parent / 'main.exe'
new_path.unlink(missing_ok=True)
bundle_path.rename(new_path)
