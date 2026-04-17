# -*- coding: utf-8 -*-
import os

from mnemos.paths import app_resource_dir

try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


def icon_path():
    base = app_resource_dir()
    for name in (
        "Mnemos_icon.png",
        "Majeur_icon.png",
        "TableDeRappel_icon.png",
    ):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            return p
    return os.path.join(base, "Mnemos_icon.png")


def load_logo_photo(width=80):
    if not _HAS_PIL:
        return None
    path = icon_path()
    if not os.path.isfile(path):
        return None
    try:
        img = Image.open(path)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        w, h = img.size
        s = min(w, h)
        img = img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
        img = img.resize((width, width), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None
