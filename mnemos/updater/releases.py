# -*- coding: utf-8 -*-
import re

from mnemos import config


def release_asset_matches(name, ext):
    if not name.endswith(ext):
        return False
    return any(marker in name for marker in config.ASSET_NAME_MARKERS)


def is_macos_bundle_update_zip(name):
    if not release_asset_matches(name, ".zip"):
        return False
    lower = name.lower()
    if "windows" in lower or "linux" in lower:
        return False
    return True


def pick_macos_bundle_zip_url(assets, tag_name=""):
    if tag_name:
        ver = re.sub(r"^v", "", str(tag_name).strip(), count=1)
        want = f"{config.RELEASE_ASSET_PREFIX}-{ver}.zip"
        for asset in assets or []:
            name = asset.get("name", "") or ""
            if name != want:
                continue
            url = asset.get("browser_download_url")
            if url and is_macos_bundle_update_zip(name):
                return url
    best = None
    for asset in assets or []:
        name = asset.get("name", "") or ""
        url = asset.get("browser_download_url")
        if not url or not is_macos_bundle_update_zip(name):
            continue
        score = 0
        if re.search(r"-\d+\.\d+\.\d+\.zip$", name):
            score += 100
        if name.startswith("Mnemos-"):
            score += 20
        elif name.startswith("Mnémos-"):
            score += 10
        cand = (score, name, url)
        if best is None or cand[:2] > best[:2]:
            best = cand
    return best[2] if best else None
