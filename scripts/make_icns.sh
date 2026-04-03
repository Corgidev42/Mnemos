#!/bin/bash
# Génère Majeur.icns à partir de Majeur_icon.png
# iconutil exige un chemin hors workspace (bug connu) → on utilise /tmp

set -e
cd "$(dirname "$0")/.."
SCRIPT_DIR="$(pwd)"
ICON_SRC="${SCRIPT_DIR}/Majeur_icon.png"
ICONSET="/tmp/Majeur.iconset"
ICNS_OUT="${SCRIPT_DIR}/Majeur.icns"

[[ -f "$ICON_SRC" ]] || { echo "❌ Majeur_icon.png introuvable"; exit 1; }

rm -rf "$ICONSET"
mkdir -p "$ICONSET"

# Générer les PNG avec Pillow (alpha requis par iconutil)
python3 - "$ICON_SRC" "$ICONSET" << 'PY'
from PIL import Image
import os, sys
src, iconset = sys.argv[1], sys.argv[2]
img = Image.open(src)
if img.mode != "RGBA":
    img = img.convert("RGBA")
w, h = img.size
size = min(w, h)
left, top = (w - size) // 2, (h - size) // 2
img = img.crop((left, top, left + size, top + size)).resize((1024, 1024), Image.Resampling.LANCZOS)
sizes = [(16,16),(16,32),(32,32),(32,64),(128,128),(128,256),(256,256),(256,512),(512,512),(512,1024)]
names = ["icon_16x16.png","icon_16x16@2x.png","icon_32x32.png","icon_32x32@2x.png",
         "icon_128x128.png","icon_128x128@2x.png","icon_256x256.png","icon_256x256@2x.png",
         "icon_512x512.png","icon_512x512@2x.png"]
for (w,h), n in zip(sizes, names):
    img.resize((w,h), Image.Resampling.LANCZOS).save(os.path.join(iconset, n), "PNG")
print("iconset ok")
PY

iconutil -c icns "$ICONSET" -o "$ICNS_OUT"
rm -rf "$ICONSET"
echo "✅ Majeur.icns créé"
