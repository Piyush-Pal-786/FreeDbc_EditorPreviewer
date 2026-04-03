# -*- mode: python ; coding: utf-8 -*-
"""
build.spec  —  PyInstaller specification for FreeDBC Editor & Previewer.

Usage (from project root):
    pip install pyinstaller
    pyinstaller build.spec

Output: dist/FreeDBC_EditorPreviewer   (or .exe on Windows)
"""

# Resolve the customtkinter package location dynamically at spec-evaluation time.
#
# Why: A hardcoded relative path like '.venv/Lib/site-packages/customtkinter'
# only exists in a local Windows virtual-environment.  On GitHub Actions runners
# (Windows, macOS, Linux) packages are installed directly into the system/hosted
# Python, so that path does not exist and PyInstaller aborts with:
#   "Unable to find '...venv/Lib/site-packages/customtkinter'"
#
# importlib.util.find_spec() asks Python's own import machinery where it would
# load the package from — this is always correct regardless of whether packages
# live in a venv, a conda env, a system install, or a CI-hosted toolcache.
import importlib.util as _ilu

_ctk_spec = _ilu.find_spec("customtkinter")
_ctk_path = str(_ctk_spec.submodule_search_locations[0])

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('sample_dbc', 'sample_dbc'),
        # Bundle CustomTkinter's theme/asset data so the UI renders correctly.
        # _ctk_path is resolved dynamically above — works on any OS / env type.
        (_ctk_path, 'customtkinter'),
    ],
    hiddenimports=[
        'customtkinter',
        'cantools',
        'openpyxl',
        'openpyxl.cell._writer',
        'packaging',
        'bitstruct',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FreeDBC_EditorPreviewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # no black terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # uncomment once you have an icon
)
