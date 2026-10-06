"""Point bundled Tkinter at the Tcl/Tk scripts extracted by PyInstaller."""

import os
import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    resource_root = Path(sys._MEIPASS) / "tcl"
    os.environ["TCL_LIBRARY"] = str(resource_root / "tcl8.6")
    os.environ["TK_LIBRARY"] = str(resource_root / "tk8.6")
