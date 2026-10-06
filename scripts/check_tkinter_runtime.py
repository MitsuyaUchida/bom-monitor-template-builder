"""Exit successfully only if Tcl can initialize from this Python installation."""

import sys
import tkinter


try:
    tkinter.Tcl()
except Exception:
    sys.exit(1)
