"""Écran préférences."""
from mnemos.ui._quiz_shared import *  # noqa: F403, F401


class PreferencesMixin:
    def show_preferences(self):
        """Réglages : délais d'auto-avance après bonne / mauvaise réponse (ms, 0 = off)."""
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="⚙️ Préférences", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(25, 8))
        tk.Label(
            self.container,
            text="Délai avant passage automatique (en millisecondes). "
                 "0 = désactivé : tu dois cliquer ou valider avec Entrée.",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY, wraplength=640,
        ).pack(pady=(0, 20))

        card = self.make_card(self.container)
        card.pack(padx=80, fill="x", pady=5)

        def row(parent, label, default_ms):
            fr = tk.Frame(parent, bg=BG_CARD)
            fr.pack(fill="x", pady=10)
            tk.Label(
                fr, text=label, font=FONT_BODY, bg=BG_CARD,
                fg=FG_PRIMARY, wraplength=520, justify="left",
            ).pack(anchor="w")
            sp = tk.Spinbox(
                fr, from_=0, to=120000, increment=100, width=10,
                font=FONT_BODY, bg=BG_INPUT, fg=FG_PRIMARY,
                insertbackground=FG_PRIMARY, buttonbackground=BTN_BG,
            )
            sp.delete(0, "end")
            sp.insert(0, str(default_ms))
            sp.pack(anchor="w", pady=(6, 0))
            return sp

        sp_ok = row(
            card,
            "Après une bonne réponse (avant la question suivante). "
            "Par défaut 1200 ms (1,2 s).",
            self.preferences.get(
                "auto_advance_correct_ms", DEFAULT_AUTO_ADVANCE_CORRECT_MS,
            ),
        )
        sp_bad = row(
            card,
            "Après une mauvaise réponse. 0 par défaut : pas d’auto-avance.",
            self.preferences.get(
                "auto_advance_wrong_ms", DEFAULT_AUTO_ADVANCE_WRONG_MS,
            ),
        )

        def _save_prefs():
            try:
                ok_ms = int(sp_ok.get().strip() or "0")
                bad_ms = int(sp_bad.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Préférences", "Valeurs invalides (entiers).")
                return
            self.preferences = save_preferences({
                "auto_advance_correct_ms": ok_ms,
                "auto_advance_wrong_ms": bad_ms,
            })
            messagebox.showinfo("Préférences", "Réglages enregistrés.")

        btn_bar = tk.Frame(self.container, bg=BG_DARK)
        btn_bar.pack(pady=(22, 12))
        self.make_button(btn_bar, "💾  Enregistrer", _save_prefs, accent=True).pack(
            side="left", padx=5,
        )
        self.make_button(btn_bar, "⬅  Retour au menu", self.show_main_menu).pack(
            side="left", padx=5,
        )

