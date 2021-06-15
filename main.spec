# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden_imports_starlette = collect_submodules("starlette")
hidden_imports_uvicorn = collect_submodules("uvicorn")
hidden_imports_dependency_injector = collect_submodules("dependency_injector")

a = Analysis(
    ['main.py'],
    binaries=[],
    datas=[],
    hiddenimports=[
        *hidden_imports_starlette,
        *hidden_imports_uvicorn,
        *hidden_imports_dependency_injector,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon='small_logo.ico',
)
