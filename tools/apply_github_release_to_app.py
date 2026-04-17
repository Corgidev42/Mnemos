#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Équivalent CLI de la mise à jour auto macOS : dernière release GitHub,
zip « bundle » Mnemos-*.zip, remplacement de l’app dans /Applications.

À lancer avec l’app fermée. Droits d’écriture sur le dossier cible requis
(souvent sans sudo si tu as installé Mnemos toi-même dans Applications).
"""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import zipfile

# Racine du dépôt (tools/ -> parent)
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from mnemos import config
from mnemos.updater import http, releases
from mnemos.updater.install import ensure_macos_executables, parse_version


def _bundle_version(app_path: str) -> str:
    plist_path = os.path.join(app_path, "Contents", "Info.plist")
    with open(plist_path, "rb") as f:
        pl = plistlib.load(f)
    return str(pl.get("CFBundleShortVersionString") or pl.get("CFBundleVersion") or "0.0.0")


def _fetch_latest() -> tuple[str, str, list]:
    api = f"https://api.github.com/repos/{config.GITHUB_REPO}/releases/latest"
    with http.github_urlopen(
        api, timeout=45, accept="application/vnd.github+json",
    ) as resp:
        data = json.loads(resp.read().decode())
    tag = str(data.get("tag_name") or "v0.0.0")
    assets = data.get("assets") or []
    zip_url = releases.pick_macos_bundle_zip_url(assets, tag_name=tag)
    return tag, zip_url or "", assets


def _find_extracted_app(cache_dir: str) -> str | None:
    for folder in (
        config.APP_BUNDLE_APP,
        "Mnémos.app",
        "Table de Rappel.app",
        "Majeur.app",
    ):
        p = os.path.join(cache_dir, folder)
        if os.path.isdir(p):
            return p
    try:
        root_apps = [
            f
            for f in os.listdir(cache_dir)
            if f.endswith(".app") and os.path.isdir(os.path.join(cache_dir, f))
        ]
    except OSError:
        root_apps = []
    if len(root_apps) == 1:
        return os.path.join(cache_dir, root_apps[0])
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Installe la dernière release Mnemos depuis GitHub (zip bundle).",
    )
    parser.add_argument(
        "--app",
        default=os.path.join("/Applications", config.APP_BUNDLE_APP),
        help="Chemin du bundle à remplacer (défaut : /Applications/Mnemos.app)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche seulement ce qui serait fait",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Ne pas demander de confirmation",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Réinstaller même si la version locale est déjà ≥ release",
    )
    args = parser.parse_args()

    if sys.platform != "darwin":
        print("❌ Ce script est prévu pour macOS.", file=sys.stderr)
        return 1

    app_path = os.path.abspath(args.app)
    if not os.path.isdir(app_path):
        print(
            f"❌ Bundle introuvable : {app_path}\n"
            "   Installe Mnemos dans Applications (glisser le .app) puis réessaie.",
            file=sys.stderr,
        )
        return 1

    try:
        tag, zip_url, _assets = _fetch_latest()
    except Exception as e:
        print(f"❌ Lecture release GitHub : {e}", file=sys.stderr)
        return 1

    if not zip_url:
        print(
            "❌ Aucun zip de mise à jour macOS sur la dernière release "
            f"({config.RELEASE_ASSET_PREFIX}-X.Y.Z.zip attendu).",
            file=sys.stderr,
        )
        return 1

    ver_remote = re.sub(r"^v", "", tag.strip(), count=1)
    try:
        cur_s = _bundle_version(app_path)
    except (OSError, KeyError, TypeError, ValueError) as e:
        print(f"❌ Lecture version installée : {e}", file=sys.stderr)
        return 1

    cur_t = parse_version(cur_s)
    new_t = parse_version(ver_remote)
    if not args.force and new_t <= cur_t:
        print(
            f"✅ Déjà à jour (installé {cur_s}, dernière release {ver_remote}). "
            "Utilise --force pour réinstaller quand même.",
        )
        return 0

    print(f"📦 Release : {tag}")
    print(f"   Installé : {cur_s}  →  Distant : {ver_remote}")
    print(f"   Cible : {app_path}")
    if args.dry_run:
        print("   (dry-run) Téléchargement / installation non effectués.")
        return 0

    if not args.yes:
        try:
            ans = input("Remplacer cette app par la release distante ? [o/N] ").strip().lower()
        except EOFError:
            ans = ""
        if ans not in ("o", "oui", "y", "yes"):
            print("Annulé.")
            return 1

    cache_dir = os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Caches",
        config.APP_NAME,
        "cli_update",
    )
    os.makedirs(cache_dir, exist_ok=True)
    zip_path = os.path.join(cache_dir, f"{config.RELEASE_ASSET_PREFIX}-{ver_remote}.zip")

    print("⬇️  Téléchargement…")
    try:
        with http.github_urlopen(zip_url, timeout=300) as resp:
            with open(zip_path, "wb") as f:
                shutil.copyfileobj(resp, f, length=256 * 1024)
                f.flush()
                os.fsync(f.fileno())
    except Exception as e:
        print(f"❌ Téléchargement : {e}", file=sys.stderr)
        return 1

    if not zipfile.is_zipfile(zip_path):
        print("❌ Le fichier téléchargé n’est pas un zip valide.", file=sys.stderr)
        return 1

    for fname in os.listdir(cache_dir):
        fp = os.path.join(cache_dir, fname)
        if fname.endswith(".zip"):
            continue
        if os.path.isdir(fp):
            shutil.rmtree(fp, ignore_errors=True)

    print("📂 Extraction…")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(cache_dir)

    extracted = _find_extracted_app(cache_dir)
    if not extracted:
        print(
            f"❌ Zip sans bundle reconnu ({config.APP_BUNDLE_APP} attendu à la racine).",
            file=sys.stderr,
        )
        return 1

    ensure_macos_executables(extracted)

    tmp_bundle = os.path.join(cache_dir, f"{config.APP_NAME}_cli_ready.app")
    if os.path.exists(tmp_bundle):
        shutil.rmtree(tmp_bundle, ignore_errors=True)

    print("🔧 ditto → bundle temporaire…")
    try:
        subprocess.run(
            ["/usr/bin/ditto", extracted, tmp_bundle],
            check=True,
        )
    except subprocess.CalledProcessError:
        print("❌ ditto a échoué.", file=sys.stderr)
        return 1

    subprocess.run(["/usr/bin/xattr", "-cr", tmp_bundle], capture_output=True)

    print("🗑  Suppression de l’ancienne app…")
    try:
        shutil.rmtree(app_path)
    except OSError as e:
        print(f"❌ Impossible de supprimer {app_path} : {e}", file=sys.stderr)
        shutil.rmtree(tmp_bundle, ignore_errors=True)
        return 1

    print("📲 Installation…")
    try:
        os.rename(tmp_bundle, app_path)
    except OSError as e:
        print(f"❌ mv vers {app_path} : {e}", file=sys.stderr)
        print(f"   Bundle laissé dans : {tmp_bundle}", file=sys.stderr)
        return 1

    subprocess.run(["/usr/bin/xattr", "-cr", app_path], capture_output=True)
    ensure_macos_executables(app_path)

    shutil.rmtree(cache_dir, ignore_errors=True)

    print("🚀 Ouverture de Mnemos…")
    subprocess.Popen(["/usr/bin/open", app_path], start_new_session=True)
    print(f"✅ Mnemos {ver_remote} installé dans {app_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
