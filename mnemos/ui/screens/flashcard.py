"""Session flashcards."""
from mnemos.ui._quiz_shared import *  # noqa: F403, F401


class FlashcardMixin:
    def _show_flashcard(self):
        self.clear()
        for key in ("<space>", "<Return>", "<Right>", "r", "f"):
            self.unbind(key)

        if not self.fc_revealed:
            self.fc_card_t0 = time.time()
            self.fc_session_segment_t0 = time.time()
            if hasattr(self, "fc_response_elapsed_s"):
                del self.fc_response_elapsed_s

        mode, nombre, mot = self.fc_cards[self.fc_idx]
        total = len(self.fc_cards)
        idx = self.fc_idx + 1

        top_bar = tk.Frame(self.container, bg=BG_DARK)
        top_bar.pack(fill="x", padx=40, pady=(18, 0))
        tk.Label(
            top_bar, text=f"🃏 Flashcard {idx}/{total}",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_MAUVE,
        ).pack(side="left")
        done_prev = idx - 1
        if done_prev > 0:
            tk.Label(
                top_bar,
                text=f"  Réussies : {self.fc_score}/{done_prev}",
                font=FONT_BODY, bg=BG_DARK, fg=FG_GREEN,
            ).pack(side="left", padx=(12, 0))
        if self.fc_streak >= 2:
            tk.Label(
                top_bar, text=f"  🔥 {self.fc_streak}",
                font=FONT_STREAK, bg=BG_DARK, fg=FG_ORANGE,
            ).pack(side="left", padx=(8, 0))

        self.fc_session_timer_lbl = tk.Label(
            top_bar, text="⏳ Session : 0.0s",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_ORANGE,
        )
        self.fc_session_timer_lbl.pack(side="right", padx=(8, 0))
        self.fc_card_timer_lbl = tk.Label(
            top_bar, text="⏱ Carte : 0.0s",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
        )
        self.fc_card_timer_lbl.pack(side="right")
        self._update_flashcard_timers()

        bar = tk.Canvas(self.container, height=4, bg=BTN_BG,
                        highlightthickness=0)
        bar.pack(fill="x", padx=60, pady=(8, 10))
        self.after(50, lambda: self._draw_progress(bar, idx, total))

        card = tk.Frame(
            self.container, bg=FG_MAUVE, padx=3, pady=3,
        )
        card.pack(padx=120, pady=16, fill="x")

        inner = tk.Frame(card, bg=BG_CARD, padx=30, pady=30)
        inner.pack(fill="both", expand=True)

        hint = (
            "Quel mot correspond ?" if mode == "nombre->mot" else
            "Quel nombre correspond ?"
        )
        tk.Label(
            inner, text=hint, font=FONT_SMALL,
            bg=BG_CARD, fg=FG_SECONDARY,
        ).pack(pady=(0, 8))

        if mode == "nombre->mot":
            tk.Label(
                inner, text=nombre, font=FONT_BIG,
                bg=BG_CARD, fg=FG_ACCENT,
            ).pack(pady=(5, 10))
            if self.fc_revealed:
                tk.Label(
                    inner, text="↕", font=FONT_BODY,
                    bg=BG_CARD, fg=FG_SECONDARY,
                ).pack()
                tk.Label(
                    inner, text=mot, font=FONT_BIG,
                    bg=BG_CARD, fg=FG_GREEN,
                ).pack(pady=(10, 10))
            else:
                tk.Label(
                    inner, text="???", font=FONT_QUESTION,
                    bg=BG_CARD, fg=FG_SECONDARY,
                ).pack(pady=(10, 10))
        else:
            tk.Label(
                inner, text=mot, font=FONT_BIG,
                bg=BG_CARD, fg=FG_GREEN,
            ).pack(pady=(5, 10))
            if self.fc_revealed:
                tk.Label(
                    inner, text="↕", font=FONT_BODY,
                    bg=BG_CARD, fg=FG_SECONDARY,
                ).pack()
                tk.Label(
                    inner, text=nombre, font=FONT_BIG,
                    bg=BG_CARD, fg=FG_ACCENT,
                ).pack(pady=(10, 10))
            else:
                tk.Label(
                    inner, text="???", font=FONT_QUESTION,
                    bg=BG_CARD, fg=FG_SECONDARY,
                ).pack(pady=(10, 10))

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=12)

        if not self.fc_revealed:
            btn = self.make_button(
                btn_frame, "Retourner (Espace)",
                self._reveal_flashcard, accent=True, width=24,
            )
            btn.pack()
            btn.focus_set()
            self.bind("<space>", lambda e: self._reveal_flashcard())
            self.bind("<Return>", lambda e: self._reveal_flashcard())
        else:
            ok_btn = self.make_button(
                btn_frame, "✓  J’avais bon",
                lambda: self._flashcard_self_rate(True), accent=True, width=18,
            )
            ok_btn.pack(side="left", padx=6)
            bad_btn = self.make_button(
                btn_frame, "✗  Je me suis trompé",
                lambda: self._flashcard_self_rate(False), danger=True, width=22,
            )
            bad_btn.pack(side="left", padx=6)
            ok_btn.focus_set()
            self.bind("r", lambda e: self._flashcard_self_rate(True))
            self.bind("f", lambda e: self._flashcard_self_rate(False))
            self.bind("<Return>", lambda e: self._flashcard_self_rate(True))

            weak_var = tk.BooleanVar(value=(nombre, mot) in self.manual_weak)
            tk.Checkbutton(
                self.container,
                text="🎯 Point faible (inclus au focus)",
                variable=weak_var,
                command=lambda p=(nombre, mot), v=weak_var: self._persist_weak_toggle(
                    p, v.get(),
                ),
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
                selectcolor=CHECK_BG, activebackground=BG_DARK,
                activeforeground=FG_ORANGE, highlightthickness=0,
            ).pack(pady=(10, 0))

            tk.Label(
                self.container,
                text="Raccourcis : R = bon · F = raté · Entrée = bon",
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(pady=(4, 0))

        self.make_button(
            self.container, "⬅  Retour au menu", self.show_main_menu,
        ).pack(pady=(14, 10))

    def _fc_session_elapsed_s(self):
        """Durée de session = temps sur la face question (sans l’écran d’auto-évaluation)."""
        acc = float(getattr(self, "fc_session_accumulated_s", 0.0))
        if not getattr(self, "fc_revealed", True) and hasattr(
            self, "fc_session_segment_t0",
        ):
            acc += time.time() - self.fc_session_segment_t0
        return acc

    def _update_flashcard_timers(self):
        if hasattr(self, "fc_session_timer_lbl") and self.fc_session_timer_lbl.winfo_exists():
            self.fc_session_timer_lbl.configure(
                text=f"⏳ Session : {self._fc_session_elapsed_s():.1f}s",
            )
        if hasattr(self, "fc_card_timer_lbl") and self.fc_card_timer_lbl.winfo_exists():
            if getattr(self, "fc_revealed", False) and hasattr(
                self, "fc_response_elapsed_s",
            ):
                card_s = self.fc_response_elapsed_s
            else:
                t0 = getattr(self, "fc_card_t0", self.fc_quiz_start)
                card_s = time.time() - t0
            self.fc_card_timer_lbl.configure(
                text=f"⏱ Carte : {card_s:.1f}s",
            )
        if (
            hasattr(self, "fc_session_timer_lbl")
            and self.fc_session_timer_lbl.winfo_exists()
        ) or (
            hasattr(self, "fc_card_timer_lbl")
            and self.fc_card_timer_lbl.winfo_exists()
        ):
            self.after(100, self._update_flashcard_timers)

    def _reveal_flashcard(self):
        if not self.fc_revealed and hasattr(self, "fc_session_segment_t0"):
            self.fc_session_accumulated_s = float(
                getattr(self, "fc_session_accumulated_s", 0.0),
            ) + (time.time() - self.fc_session_segment_t0)
        if not self.fc_revealed and hasattr(self, "fc_card_t0"):
            # Temps mesuré jusqu’au retournement (sans la phase où la réponse est visible).
            self.fc_response_elapsed_s = time.time() - self.fc_card_t0
        self.fc_revealed = True
        self._show_flashcard()

    def _flashcard_self_rate(self, correct):
        mode, nombre, mot = self.fc_cards[self.fc_idx]
        elapsed = float(
            getattr(
                self, "fc_response_elapsed_s", time.time() - self.fc_card_t0,
            ),
        )
        self._apply_answer_stats(mode, nombre, mot, correct, elapsed)
        self.fc_results.append(
            (mode, nombre, mot, "(flashcard)", correct, elapsed))
        if correct:
            self.fc_score += 1
            self.fc_streak += 1
            self.fc_best_streak = max(self.fc_best_streak, self.fc_streak)
        else:
            self.fc_streak = 0

        last = self.fc_idx >= len(self.fc_cards) - 1
        if last:
            self._show_flashcard_end()
        else:
            self.fc_idx += 1
            self.fc_revealed = False
            self._show_flashcard()

    def _show_flashcard_end(self):
        self.clear()
        for key in ("<space>", "<Return>", "<Right>", "r", "f"):
            self.unbind(key)

        total = len(self.fc_cards)
        good = self.fc_score
        total_s = self._fc_session_elapsed_s()
        if total > 0:
            err_count = sum(1 for r in self.fc_results if not r[4])
            self._record_session_run(
                total_q=total,
                score=good,
                errors_count=err_count,
                duration_s=total_s,
                flashcard=True,
            )
        tk.Label(
            self.container, text="🃏 Session terminée", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_MAUVE,
        ).pack(pady=(50, 12))
        tk.Label(
            self.container,
            text=f"Tu as indiqué {good} bonne(s) réponse(s) sur {total}.",
            font=FONT_BODY, bg=BG_DARK, fg=FG_PRIMARY,
        ).pack(pady=(0, 8))
        tk.Label(
            self.container,
            text=f"⏳ Temps total de la session : {total_s:.1f}s",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(0, 8))
        if self.fc_best_streak >= 2:
            tk.Label(
                self.container,
                text=f"Meilleure série : 🔥 {self.fc_best_streak}",
                font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_ORANGE,
            ).pack(pady=(0, 16))
        row = tk.Frame(self.container, bg=BG_DARK)
        row.pack(pady=20)
        self.make_button(
            row, "⬅  Menu principal", self.show_main_menu, accent=True, width=22,
        ).pack(side="left", padx=8)

