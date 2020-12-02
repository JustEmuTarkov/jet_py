import PyInstaller.__main__

PyInstaller.__main__.run([
    'core/main.py',
    '--onefile',
    '--console',
    '--icon=small_logo.ico',
])