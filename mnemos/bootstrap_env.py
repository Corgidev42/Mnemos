"""Préparation environnement macOS / stdin AVANT tout import de tkinter."""
import os
import sys

_TK_MAC_PTY_MASTER = None


def apply_macos_bootstrap():
    """
    À appeler en tout premier depuis le point d’entrée.
    Évite Tcl/Tk 9 + stdin non-TTY sur macOS (console Tk / assertion AppKit).
    """
    global _TK_MAC_PTY_MASTER
    if sys.platform == "darwin":
        os.environ["TK_NO_CONSOLE"] = "1"
        if not os.isatty(0):
            try:
                import pty

                _TK_MAC_PTY_MASTER, slave = pty.openpty()
                os.dup2(slave, 0)
                os.close(slave)
            except OSError:
                _TK_MAC_PTY_MASTER = None
