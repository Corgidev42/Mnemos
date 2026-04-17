# -*- coding: utf-8 -*-
import json
import os
import tempfile
import threading

from mnemos import config
from mnemos.updater import http, releases


def check_for_update(invoke_on_main, callback):
    def _do_check():
        try:
            api = f"https://api.github.com/repos/{config.GITHUB_REPO}/releases/latest"
            with http.github_urlopen(
                api, timeout=15, accept="application/vnd.github+json",
            ) as resp:
                data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "v0.0.0")
            from mnemos.updater import install as _install
            current = _install.parse_version(config.VERSION)
            latest = _install.parse_version(tag)
            if latest > current:
                zip_url = releases.pick_macos_bundle_zip_url(
                    data.get("assets", []), tag_name=tag,
                )
                dmg_url = None
                for asset in data.get("assets", []):
                    name = asset.get("name", "")
                    aurl = asset.get("browser_download_url")
                    if releases.release_asset_matches(name, ".dmg"):
                        dmg_url = aurl
                invoke_on_main(
                    lambda: callback(True, {
                        "tag": tag, "zip_url": zip_url, "dmg_url": dmg_url,
                        "body": data.get("body", ""),
                    }),
                )
            else:
                invoke_on_main(lambda: callback(True, {"up_to_date": True}))
        except Exception as e:
            _err = str(e)
            invoke_on_main(lambda msg=_err: callback(False, msg))

    threading.Thread(target=_do_check, daemon=True).start()


def download_and_open_dmg(url, invoke_on_main, callback):
    def _do_download():
        try:
            dest = os.path.join(
                tempfile.gettempdir(), f"{config.APP_NAME}_update.dmg")
            with http.github_urlopen(url, timeout=300) as resp:
                with open(dest, "wb") as f:
                    import shutil
                    shutil.copyfileobj(resp, f, length=256 * 1024)
                    f.flush()
                    os.fsync(f.fileno())
            os.system(f'open "{dest}"')
            invoke_on_main(
                lambda: callback(
                    True,
                    f"Le .dmg a été ouvert. Glisse « {config.APP_NAME} » dans Applications.",
                ),
            )
        except Exception as e:
            _err = str(e)
            invoke_on_main(lambda msg=_err: callback(False, msg))

    threading.Thread(target=_do_download, daemon=True).start()
