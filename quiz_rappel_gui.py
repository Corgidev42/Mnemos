#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mnémos — point d’entrée (Makefile, PyInstaller, habitudes locales).
Bootstrap macOS / stdin avant tout import de tkinter ; logique dans mnemos/.
"""

from mnemos.bootstrap_env import apply_macos_bootstrap

apply_macos_bootstrap()

# Réexport pour scripts / grep (source de vérité : mnemos.config.VERSION)
from mnemos import config as _config

VERSION = _config.VERSION


def main():
    from mnemos.ui.app import run_app

    run_app()


if __name__ == "__main__":
    main()
