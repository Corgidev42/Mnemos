# -*- coding: utf-8 -*-
"""Entrée après bootstrap : importe Tk uniquement ici."""
from mnemos.bootstrap_env import apply_macos_bootstrap


def main():
    apply_macos_bootstrap()
    from mnemos.ui.app import run_app

    run_app()
