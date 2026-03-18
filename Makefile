# ──────────────────────────────────────────────
# Table de Rappel — Makefile
# ──────────────────────────────────────────────

PYTHON  ?= python3
GUI     := quiz_rappel_gui.py
CLI     := quiz_rappel.py
STATS   := stats_rappel.csv

.PHONY: run cli check clean reset dmg help

## run : Lance le quiz (interface graphique)
run:
	@$(PYTHON) $(GUI)

## cli : Lance la version terminal
cli:
	@$(PYTHON) $(CLI)

## check : Vérifie la syntaxe des fichiers Python
check:
	@echo "🔍 Vérification de la syntaxe…"
	@$(PYTHON) -m py_compile $(GUI) && echo "  ✅ $(GUI) OK"
	@$(PYTHON) -m py_compile $(CLI) && echo "  ✅ $(CLI) OK"
	@echo "✅ Tout est bon !"

## clean : Supprime les fichiers cache Python
clean:
	@echo "🧹 Nettoyage…"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Nettoyé"

## dmg : Crée l'app .app et le .dmg (macOS)
dmg:
	@pip install -q pyinstaller 2>/dev/null || true
	@chmod +x build_dmg.sh && ./build_dmg.sh

## reset : Remet les statistiques à zéro
reset:
	@echo "⚠️  Réinitialisation des stats…"
	@if [ -f $(STATS) ]; then \
		head -1 $(STATS) > $(STATS).tmp && mv $(STATS).tmp $(STATS); \
		echo "✅ Stats réinitialisées (header conservé)"; \
	else \
		echo "ℹ️  Pas de fichier stats trouvé"; \
	fi

## help : Affiche cette aide
help:
	@echo ""
	@echo "  Table de Rappel — Commandes disponibles"
	@echo "  ────────────────────────────────────────"
	@grep -E '^## ' Makefile | sed 's/## /  /' | sort
	@echo ""
