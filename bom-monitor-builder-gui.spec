# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys
import os


ROOT = Path(SPECPATH).resolve()
TCL_SOURCE = Path(os.environ["TCL_LIBRARY"])
TK_SOURCE = Path(os.environ["TK_LIBRARY"])
datas = [
    (str(ROOT / "profiles"), "profiles"),
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "config"), "config"),
    (str(TCL_SOURCE), "tcl/tcl8.6"),
    (str(TK_SOURCE), "tcl/tk8.6"),
]
binaries = [
    (str(Path(sys.base_prefix) / "DLLs" / "_tkinter.pyd"), "."),
    (str(Path(sys.base_prefix) / "DLLs" / "tcl86t.dll"), "."),
    (str(Path(sys.base_prefix) / "DLLs" / "tk86t.dll"), "."),
]

a = Analysis(
    [str(ROOT / "src" / "bom_monitor_builder" / "gui_main.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=["_tkinter", "tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox", "tkinter.scrolledtext"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / "pyinstaller_runtime" / "tkinter_paths.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="bom-monitor-builder-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
