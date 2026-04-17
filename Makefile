# ──────────────────────────────────────────────
# Mnemos — Makefile
# ──────────────────────────────────────────────

PYTHON  ?= python3
GUI     := quiz_rappel_gui.py
STATS   := .app_data/stats.json

VERSION := $(shell grep -E '^VERSION = ' mnemos/config.py | cut -d'"' -f2)
DMG     := dist/Mnemos-$(VERSION).dmg
ZIP     := dist/Mnemos-$(VERSION).zip

.PHONY: run check clean clean-build reset dmg tag release publish update-app update-app-yes help

## run : Lance l'application
run:
	@$(PYTHON) $(GUI)

## check : Vérifie la syntaxe Python
check:
	@echo "🔍 Vérification de la syntaxe…"
	@$(PYTHON) -m py_compile $(GUI) && echo "  ✅ $(GUI) OK"
	@$(PYTHON) -m compileall -q mnemos && echo "  ✅ mnemos/ OK"
	@echo "✅ Tout est bon !"

## clean : Supprime les fichiers cache
clean:
	@echo "🧹 Nettoyage…"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Nettoyé"

## clean-build : Supprime les vieux artefacts PyInstaller (Majeur, Table de Rappel, TableDeRappel-*) et tout build/
clean-build:
	@echo "🧹 Suppression des anciens noms dans build/ et dist/…"
	@rm -rf build
	@rm -rf "dist/Table de Rappel" "dist/Table de Rappel.app" 2>/dev/null || true
	@rm -rf dist/Majeur dist/Majeur.app 2>/dev/null || true
	@rm -f dist/Majeur-*.dmg dist/Majeur-*.zip 2>/dev/null || true
	@rm -f dist/TableDeRappel-*.dmg dist/TableDeRappel-*.zip 2>/dev/null || true
	@echo "✅ Fait (les builds Mnemos actuels dans dist/ sont conservés ; supprime-les à la main si besoin)"

## dmg : Crée l'app .app, le .dmg et le .zip (macOS)
dmg:
	@chmod +x scripts/build_dmg.sh scripts/make_icns.sh 2>/dev/null || true
	@./scripts/build_dmg.sh

## tag : Crée et pousse le tag git pour la version courante
tag:
	@git tag -a v$(VERSION) -m "v$(VERSION)" 2>/dev/null || true
	@git push origin v$(VERSION)

## release : Build .dmg/.zip + publie sur GitHub
release: dmg
	@echo "📤 Publication sur GitHub…"
	@test -n "$(VERSION)" || { echo "❌ VERSION introuvable dans $(GUI)"; exit 1; }
	@command -v gh >/dev/null 2>&1 || { echo "❌ gh CLI requis : brew install gh && gh auth login"; exit 1; }
	@test -f $(DMG) || { echo "❌ $(DMG) introuvable"; exit 1; }
	@test -f $(ZIP) || { echo "❌ $(ZIP) introuvable"; exit 1; }
	@if gh release view v$(VERSION) >/dev/null 2>&1; then \
		gh release upload v$(VERSION) $(DMG) $(ZIP) --clobber; \
	else \
		gh release create v$(VERSION) $(DMG) $(ZIP) --title "v$(VERSION)" \
			--notes "Mnemos v$(VERSION) — Mise à jour automatique disponible."; \
	fi
	@echo "✅ Release v$(VERSION) : https://github.com/Corgidev42/Mnemos/releases/tag/v$(VERSION)"

## publish : tag + release (commit/push d'abord !)
publish: tag release

## update-app : Dernière release GitHub → remplace /Applications/Mnemos.app (fermer l’app ; macOS)
update-app:
	@test "$$(uname)" = "Darwin" || { echo "❌ macOS uniquement"; exit 1; }
	@$(PYTHON) tools/apply_github_release_to_app.py

## update-app-yes : idem update-app sans question de confirmation
update-app-yes:
	@test "$$(uname)" = "Darwin" || { echo "❌ macOS uniquement"; exit 1; }
	@$(PYTHON) tools/apply_github_release_to_app.py --yes

## reset : Remet les statistiques à zéro
reset:
	@echo "⚠️  Réinitialisation des stats…"
	@rm -f $(STATS) 2>/dev/null && echo "✅ Stats réinitialisées" || echo "ℹ️  Pas de fichier stats trouvé"

## help : Affiche cette aide
help:
	@echo ""
	@echo "  Mnemos — Commandes disponibles"
	@echo "  ────────────────────────────────────────"
	@grep -E '^## ' Makefile | sed 's/## /  /' | sort
	@echo ""
