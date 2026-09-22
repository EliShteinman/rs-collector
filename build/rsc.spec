# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

PROJECT_ROOT = Path(SPECPATH).parent
BINARY_NAME = "rsc"

copyparty_datas, copyparty_binaries, copyparty_hidden = collect_all("copyparty")

analysis = Analysis(
    [str(PROJECT_ROOT / "build" / "entrypoint.py")],
    pathex=[str(PROJECT_ROOT / "src")],
    binaries=copyparty_binaries,
    datas=[(str(PROJECT_ROOT / "config"), "config"), *copyparty_datas],
    hiddenimports=[
        "rs_collector.cli.app",
        "logging.handlers",
        *copyparty_hidden,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "IPython"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name=BINARY_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
