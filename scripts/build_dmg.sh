#!/bin/bash
# Build Mnemos .app et .dmg
# Usage: ./scripts/build_dmg.sh
#
# Prérequis :
#   pip install pyinstaller pillow
#   (optionnel) brew install create-dmg  — pour un .dmg avec lien Applications

set -e
cd "$(dirname "$0")/.."

# Signature ad hoc + nettoyage xattr : évite le faux message macOS
# « L'application est endommagée » sur les bundles PyInstaller non notariés.
sign_macos_app() {
  local app="$1"
  [ -d "$app" ] || return 0
  if command -v codesign &>/dev/null; then
    echo "🔏 Signature ad hoc : $app"
    codesign --force --deep --sign - "$app" || true
  fi
  xattr -cr "$app" 2>/dev/null || true
}

APP_NAME="Mnemos"
DIST="dist"
DMG_DIR="$DIST/dmg"
DMG_FILE="$DIST/Mnemos-$(grep -E '^VERSION = ' quiz_rappel_gui.py | cut -d'"' -f2).dmg"

echo "🔨 Build de $APP_NAME…"
echo ""

# 0. Générer l'icône .icns si possible
if [ -f scripts/make_icns.sh ]; then
  chmod +x scripts/make_icns.sh
  ./scripts/make_icns.sh 2>/dev/null || echo "⚠️  Icône .icns non générée (Pillow requis)"
fi

# 1. PyInstaller — génère le .app (console=False dans le .spec)
echo "📦 PyInstaller…"
if [ -d venv ]; then
  if [ -x venv/bin/python3 ]; then
    PY=venv/bin/python3
  elif [ -x venv/bin/python ]; then
    PY=venv/bin/python
  else
    echo "❌ venv sans python3/python exécutable"
    exit 1
  fi
  "$PY" -m pip install -q pyinstaller pillow 2>/dev/null || true
  "$PY" -m PyInstaller --noconfirm --clean Mnemos.spec
else
  command -v pyinstaller >/dev/null 2>&1 && pyinstaller --noconfirm --clean Mnemos.spec || python3 -m PyInstaller --noconfirm --clean Mnemos.spec
fi

# PyInstaller onedir crée dist/Mnemos/ ; sur macOS c'est affiché comme .app
if [ -d "$DIST/$APP_NAME.app" ]; then
    APP_PATH="$DIST/$APP_NAME.app"
elif [ -d "$DIST/$APP_NAME" ]; then
    if [ -f "$DIST/$APP_NAME/$APP_NAME" ] || [ -f "$DIST/$APP_NAME/Mnemos" ]; then
        mv "$DIST/$APP_NAME" "$DIST/$APP_NAME.app"
        APP_PATH="$DIST/$APP_NAME.app"
    else
        APP_PATH="$DIST/$APP_NAME"
    fi
else
    echo "❌ App non trouvée dans $DIST/"
    ls -la "$DIST/" 2>/dev/null || true
    exit 1
fi

echo "✅ App créée : $APP_PATH"
sign_macos_app "$APP_PATH"
echo ""

# 2. Créer le .dmg
echo "💿 Création du .dmg…"
mkdir -p "$DMG_DIR"
rm -rf "$DMG_DIR"/*
cp -R "$APP_PATH" "$DMG_DIR/"
sign_macos_app "$DMG_DIR/$APP_NAME.app"
rm -f "$DMG_FILE"

if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "$APP_NAME" \
        --window-pos 200 120 \
        --window-size 600 300 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 175 120 \
        --hide-extension "$APP_NAME.app" \
        --app-drop-link 425 120 \
        "$DMG_FILE" \
        "$DMG_DIR/"
else
    hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_DIR" -ov -format UDZO "$DMG_FILE"
fi

# 3. Créer le .zip pour la mise à jour auto
VERSION=$(grep -E '^VERSION = ' quiz_rappel_gui.py | cut -d'"' -f2)
ZIP_FILE="$DIST/Mnemos-${VERSION}.zip"
echo "📦 Création du .zip (mise à jour auto)…"
rm -f "$ZIP_FILE"
(cd "$DIST" && zip -r "Mnemos-${VERSION}.zip" "Mnemos.app")

echo ""
echo "✅ Terminé !"
echo "   📱 App : $APP_PATH"
echo "   💿 DMG : $DMG_FILE"
echo "   📦 ZIP : $ZIP_FILE"
echo ""
