# -*- coding: utf-8 -*-
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import zipfile

from mnemos import config
from mnemos.paths import get_app_support_dir
from mnemos.updater import http


def parse_version(s):
    s = str(s).strip().lstrip("v")
    try:
        return tuple(int(x) for x in s.split(".")[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


def get_app_bundle_path():
    if not getattr(sys, "frozen", False):
        return None
    path = os.path.abspath(sys.executable)
    for _ in range(10):
        parent = os.path.dirname(path)
        if not parent or parent == path:
            return None
        path = parent
        if path.endswith(".app") and os.path.isdir(path):
            return path
    return None


def auto_update_eligibility():
    if not getattr(sys, "frozen", False):
        return False, "not_bundled"
    app_path = get_app_bundle_path()
    if not app_path or not os.path.isdir(app_path):
        return False, "not_bundled"
    if "/Volumes/" in app_path:
        return False, "from_dmg"
    return True, ""


def can_auto_update():
    return auto_update_eligibility()[0]


def ensure_macos_executables(app_bundle_path):
    macos_dir = os.path.join(app_bundle_path, "Contents", "MacOS")
    if not os.path.isdir(macos_dir):
        return
    for name in os.listdir(macos_dir):
        p = os.path.join(macos_dir, name)
        if os.path.isfile(p):
            try:
                mode = os.stat(p).st_mode
                os.chmod(p, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            except OSError:
                pass


def install_update_self(invoke_on_main, zip_url, tag, callback):
    def _do_install():
        try:
            app_path = get_app_bundle_path()
            if not app_path or not os.path.isdir(app_path):
                invoke_on_main(
                    lambda: callback(
                        False, "Mise à jour auto indisponible (pas en mode .app)",
                    ),
                )
                return

            cache_dir = os.path.join(
                os.path.expanduser("~"),
                "Library", "Caches", config.APP_NAME, "update",
            )
            os.makedirs(cache_dir, exist_ok=True)

            ver = re.sub(r"^v", "", str(tag).strip(), count=1)
            zip_path = os.path.join(
                cache_dir, f"{config.RELEASE_ASSET_PREFIX}-{ver}.zip",
            )

            with http.github_urlopen(zip_url, timeout=180) as resp:
                with open(zip_path, "wb") as f:
                    shutil.copyfileobj(resp, f, length=256 * 1024)
                    f.flush()
                    os.fsync(f.fileno())

            if not zipfile.is_zipfile(zip_path):
                invoke_on_main(
                    lambda: callback(
                        False,
                        "Le téléchargement n’est pas un fichier .zip valide "
                        "(réseau, pare-feu ou fichier release). Réessaie ou "
                        "télécharge le .dmg à la main.",
                    ),
                )
                return

            for fname in os.listdir(cache_dir):
                fp = os.path.join(cache_dir, fname)
                if os.path.isdir(fp):
                    shutil.rmtree(fp, ignore_errors=True)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(cache_dir)

            extracted_app = None
            for folder in (
                config.APP_BUNDLE_APP,
                "Mnémos.app",
                "Table de Rappel.app",
                "Majeur.app",
            ):
                p = os.path.join(cache_dir, folder)
                if os.path.isdir(p):
                    extracted_app = p
                    break
            if not extracted_app:
                try:
                    root_apps = [
                        f for f in os.listdir(cache_dir)
                        if f.endswith(".app")
                        and os.path.isdir(os.path.join(cache_dir, f))
                    ]
                except OSError:
                    root_apps = []
                if len(root_apps) == 1:
                    extracted_app = os.path.join(cache_dir, root_apps[0])
            if not extracted_app:
                invoke_on_main(
                    lambda: callback(
                        False,
                        f"Format du .zip invalide ({config.APP_BUNDLE_APP} manquant)",
                    ),
                )
                return

            ensure_macos_executables(extracted_app)

            log_path = os.path.join(get_app_support_dir(), "updater_last.log")
            try:
                with open(log_path, "a", encoding="utf-8") as lg:
                    lg.write(
                        f"\n--- Préparation mise à jour {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
                        f"  app actuelle : {app_path}\n"
                        f"  bundle extrait : {extracted_app}\n",
                    )
            except OSError:
                log_path = os.path.join(cache_dir, "updater.log")

            tmp_bundle = os.path.join(cache_dir, f"{config.APP_NAME}_ready.app")
            pid = os.getpid()
            script_path = os.path.join(cache_dir, "mnemos_apply_update.sh")
            script = f'''#!/bin/bash
export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
LOG={repr(log_path)}
APP_PATH={repr(app_path)}
NEW_APP={repr(extracted_app)}
CACHE_DIR={repr(cache_dir)}
TMP_BUNDLE={repr(tmp_bundle)}
PID={pid}
exec >>"$LOG" 2>&1
echo ""
echo "======== Mnemos updater $(date) ========"
echo "En attente fin du processus PID=$PID …"
for _ in $(seq 1 600); do
  if ! kill -0 "$PID" 2>/dev/null; then
    break
  fi
  sleep 0.25
done
echo "Processus terminé, pause fichiers…"
sleep 2
if [[ ! -d "$NEW_APP" ]]; then
  echo "ERREUR: bundle extrait introuvable: $NEW_APP"
  rm -rf "$CACHE_DIR"
  exit 1
fi
/usr/bin/xattr -cr "$NEW_APP" 2>/dev/null || true
rm -rf "$TMP_BUNDLE"
echo "ditto -> TMP_BUNDLE …"
if ! /usr/bin/ditto "$NEW_APP" "$TMP_BUNDLE"; then
  echo "ERREUR: ditto vers TMP_BUNDLE a échoué"
  exit 1
fi
echo "Suppression ancienne app …"
if ! rm -rf "$APP_PATH"; then
  echo "ERREUR: rm -rf APP_PATH a échoué (droits ?)"
  rm -rf "$TMP_BUNDLE"
  exit 1
fi
echo "Installation …"
if ! /bin/mv "$TMP_BUNDLE" "$APP_PATH"; then
  echo "ERREUR: mv TMP_BUNDLE -> APP_PATH a échoué"
  echo "Récupération possible: $TMP_BUNDLE ou dossier cache $CACHE_DIR"
  exit 1
fi
/usr/bin/xattr -cr "$APP_PATH" 2>/dev/null || true
if [[ -d "$APP_PATH/Contents/MacOS" ]]; then
  for f in "$APP_PATH/Contents/MacOS/"*; do
    [[ -f "$f" ]] && chmod +x "$f" 2>/dev/null || true
  done
fi
echo "Ouverture …"
/usr/bin/open "$APP_PATH" || echo "AVERTISSEMENT: open a échoué"
echo "OK: mise à jour appliquée"
rm -rf "$CACHE_DIR"
echo "==== fin ===="
exit 0
'''
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script)
            os.chmod(script_path, 0o755)

            try:
                subprocess.Popen(
                    ["/bin/bash", script_path],
                    start_new_session=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
            except OSError as exc:
                invoke_on_main(
                    lambda msg=str(exc): callback(
                        False,
                        f"Impossible de lancer le script de mise à jour : {msg}",
                    ),
                )
                return

            invoke_on_main(lambda: callback(True, "restart"))
        except Exception as e:
            _err = str(e)
            invoke_on_main(lambda msg=_err: callback(False, msg))

    threading.Thread(target=_do_install, daemon=True).start()
