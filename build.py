import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--console',
    '--icon=small_logo.ico',
    '--distpath=./',
    '--hiddenimport=ujson',
    '--hiddenimport=server.utils',
])
