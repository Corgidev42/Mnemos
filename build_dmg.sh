#!/bin/bash
# Build Table de Rappel .app et .dmg
# Usage: ./build_dmg.sh
#
# Prérequis :
#   pip install pyinstaller
#   (optionnel) brew install create-dmg  — pour un .dmg avec lien Applications

set -e
cd "$(dirname "$0")"

APP_NAME="Table de Rappel"
DIST="dist"
DMG_DIR="$DIST/dmg"
DMG_FILE="$DIST/TableDeRappel-$(grep -E '^VERSION = ' quiz_rappel_gui.py | cut -d'"' -f2).dmg"

echo "🔨 Build de $APP_NAME…"
echo ""

# 1. PyInstaller — génère le .app (console=False dans le .spec)
echo "📦 PyInstaller…"
pyinstaller --noconfirm --clean TableDeRappel.spec

# PyInstaller onedir crée dist/Table de Rappel/ ; sur macOS c'est affiché comme .app
# ou dist/Table de Rappel.app selon la version
if [ -d "$DIST/$APP_NAME.app" ]; then
    APP_PATH="$DIST/$APP_NAME.app"
elif [ -d "$DIST/$APP_NAME" ]; then
    # Dossier onedir sans .app : sur macOS on le renomme pour la distribution
    if [ -f "$DIST/$APP_NAME/$APP_NAME" ] || [ -f "$DIST/$APP_NAME/Table de Rappel" ]; then
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
echo ""

# 2. Créer le .dmg
echo "💿 Création du .dmg…"
mkdir -p "$DMG_DIR"
rm -rf "$DMG_DIR"/*
cp -R "$APP_PATH" "$DMG_DIR/"

# Supprimer l'ancien .dmg
rm -f "$DMG_FILE"

# Utiliser create-dmg si installé, sinon hdiutil
if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "Table de Rappel" \
        --window-pos 200 120 \
        --window-size 600 300 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 175 120 \
        --hide-extension "$APP_NAME.app" \
        --app-drop-link 425 120 \
        "$DMG_FILE" \
        "$DMG_DIR/"
else
    # Fallback : hdiutil (natif macOS)
    hdiutil create -volname "Table de Rappel" -srcfolder "$DMG_DIR" -ov -format UDZO "$DMG_FILE"
fi

echo ""
echo "✅ Terminé !"
echo "   📱 App : $APP_PATH"
echo "   💿 DMG : $DMG_FILE"
echo ""
echo "Pour publier : uploade $DMG_FILE sur GitHub Releases avec le tag v$(grep -E '^VERSION = ' quiz_rappel_gui.py | cut -d'"' -f2)"
