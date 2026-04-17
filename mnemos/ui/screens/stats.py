"""Statistiques et historique de sessions."""
from mnemos.ui._quiz_shared import *  # noqa: F403, F401


class StatsMixin:
    def show_stats_view(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="📊 Statistiques", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(20, 5))

        main_tf = tk.Frame(self.container, bg=BG_DARK)
        main_tf.pack(fill="x", padx=40, pady=(0, 6))

        def main_tab_lbl(text, val):
            act = self._stats_main_tab == val
            bg = TAB_ACTIVE_BG if act else BG_DARK
            fg = TAB_ACTIVE_FG if act else FG_SECONDARY
            lb = tk.Label(
                main_tf, text=text, font=FONT_BODY_BOLD,
                bg=bg, fg=fg, cursor="hand2", padx=14, pady=5,
            )
            lb.pack(side="left", padx=(0, 8))
            lb.bind(
                "<Button-1>",
                lambda e, v=val: self._switch_stats_main_tab(v),
            )
            lb.bind("<Enter>", lambda e, l=lb, a=act: l.configure(
                bg=TAB_ACTIVE_BG if not a else l.cget("bg")))
            lb.bind("<Leave>", lambda e, l=lb, b=bg: l.configure(bg=b))

        main_tab_lbl("Par paire", "pairs")
        main_tab_lbl("Sessions (temps, score, erreurs)", "sessions")

        if self._stats_main_tab == "pairs":
            tk.Label(
                self.container,
                text="Temps moyen (s) : par lettre du mot (N→M) et par chiffre du "
                     "nombre (M→N). Colonne # = position dans la table de rappel. "
                     "Clique sur un en-tête pour trier ; un second clic inverse.",
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY, wraplength=720,
            ).pack(pady=(0, 8))

            tab_frame = tk.Frame(self.container, bg=BG_DARK)
            tab_frame.pack(fill="x", padx=40, pady=(0, 5))

            current_tab = (
                self._stats_sort_tab
                if self._stats_sort_column == "total"
                else None
            )

            def make_tab(text, val):
                is_active = current_tab == val
                bg = TAB_ACTIVE_BG if is_active else BG_DARK
                fg = TAB_ACTIVE_FG if is_active else FG_SECONDARY
                btn = tk.Label(
                    tab_frame, text=text, font=FONT_BODY_BOLD,
                    bg=bg, fg=fg, cursor="hand2", padx=15, pady=6,
                    relief="flat",
                )
                btn.pack(side="left", padx=(0, 2))
                if is_active:
                    tk.Frame(tab_frame, bg=FG_ACCENT, height=3).pack(
                        side="left", fill="x", padx=(0, 2),
                    )
                btn.bind("<Button-1>", lambda e: self._switch_stats_tab(val))
                btn.bind("<Enter>", lambda e, b=btn, ia=is_active: b.configure(
                    bg=TAB_ACTIVE_BG if not ia else b.cget("bg")))
                btn.bind("<Leave>", lambda e, b=btn, bg_=bg: b.configure(bg=bg_))

            make_tab("🔻 Moins connus", "worst")
            make_tab("🔺 Plus connus", "best")
            tk.Label(
                tab_frame,
                text="(Tri par score total · autres colonnes = tri libre)",
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(side="left", padx=(12, 0))

            reset_btn = tk.Label(
                tab_frame, text="🗑 Tout à zéro", font=FONT_SMALL,
                bg=BG_DARK, fg=FG_RED, cursor="hand2", padx=10,
            )
            reset_btn.pack(side="right")
            reset_btn.bind("<Button-1>", lambda e: self._confirm_reset_stats())

            sync_btn = tk.Label(
                tab_frame, text="↻ Sync table", font=FONT_SMALL,
                bg=BG_DARK, fg=FG_ACCENT, cursor="hand2", padx=10,
            )
            sync_btn.pack(side="right", padx=(0, 4))
            sync_btn.bind("<Button-1>", lambda e: self._sync_stats_to_table())

            self.stats_list_frame = tk.Frame(self.container, bg=BG_DARK)
            self.stats_list_frame.pack(fill="both", expand=True, padx=40, pady=5)
            self._render_stats_list()
        else:
            tk.Label(
                self.container,
                text="Chaque session terminée enregistre la durée totale, le score, "
                     "les erreurs et le mode (dont « Toute la table »). Les lignes "
                     "sont triées du plus récent au plus ancien.",
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY, wraplength=720,
            ).pack(pady=(0, 8))
            self.stats_list_frame = tk.Frame(self.container, bg=BG_DARK)
            self.stats_list_frame.pack(fill="both", expand=True, padx=40, pady=5)
            self._render_session_runs_list()

        io = tk.Frame(self.container, bg=BG_DARK)
        io.pack(pady=(4, 2))
        self.make_button(
            io, "📤  Exporter sauvegarde complète…",
            self._export_full_backup_file, width=28,
        ).pack(side="left", padx=6)
        self.make_button(
            io, "📥  Importer sauvegarde complète…",
            self._import_full_backup_file, width=30,
        ).pack(side="left", padx=6)

        self.make_button(
            self.container, "⬅  Retour au menu", self.show_main_menu,
        ).pack(pady=(5, 15))

    def _switch_stats_main_tab(self, tab):
        self._stats_main_tab = tab
        self.show_stats_view()

    def _confirm_reset_stats(self):
        if messagebox.askyesno(
            "Réinitialiser",
            "Remettre toutes les stats à zéro ? Cette action est irréversible.",
        ):
            for key in self.stats:
                self.stats[key] = _default_stats_row()
            save_stats(self.stats, self.table)
            self.show_stats_view()

    def _sync_stats_to_table(self):
        """Supprime toute entrée de stats qui ne correspond plus à un couple de la table."""
        valid_bn = {_norm_pair(p) for p in self.table}
        removed = 0
        for k in list(self.stats.keys()):
            if _norm_pair(k) not in valid_bn:
                del self.stats[k]
                removed += 1
        save_stats(self.stats, self.table)
        messagebox.showinfo(
            "Synchroniser",
            f"{removed} entrée(s) hors table supprimée(s)."
            if removed
            else "Déjà aligné : aucune entrée hors table.",
        )
        self.show_stats_view()

    def _clear_stats_one_pair(self, pair):
        n, m = pair
        if not messagebox.askyesno(
            "Effacer les stats",
            f"Remettre à zéro les statistiques pour {n} → {m} ?",
        ):
            return
        self.stats[pair] = _default_stats_row()
        save_stats(self.stats, self.table)
        self.show_stats_view()

    def _switch_stats_tab(self, tab):
        self._stats_sort_tab = tab
        self._stats_sort_column = "total"
        self._stats_sort_desc = tab == "best"
        self.show_stats_view()

    def _stats_header_clicked(self, col):
        if self._stats_sort_column == col:
            self._stats_sort_desc = not self._stats_sort_desc
        else:
            self._stats_sort_column = col
            self._stats_sort_desc = False
        if self._stats_sort_column == "total":
            self._stats_sort_tab = "best" if self._stats_sort_desc else "worst"
        self.show_stats_view()

    def _stats_sort_key(self, item, table_index_map):
        """Clé de tri (tuple) pour une ligne (pair, vals)."""
        (n, m), vals = item
        s_nm, s_mn, t_nm, t_mn = vals
        col = self._stats_sort_column
        tie_n, tie_m = str(n), str(m).lower()
        if col == "total":
            return (s_nm + s_mn, tie_n, tie_m)
        if col == "idx":
            return (table_index_map.get((n, m), 10**9), tie_n, tie_m)
        if col == "nombre":
            v = _parse_nombre_int(n)
            if v is not None:
                return (0, v, tie_n, tie_m)
            return (1, tie_n, tie_m)
        if col == "mot":
            return (tie_m, tie_n)
        if col == "s_nm":
            return (s_nm, tie_n, tie_m)
        if col == "s_mn":
            return (s_mn, tie_n, tie_m)
        if col == "t_nm":
            return (t_nm, tie_n, tie_m)
        if col == "t_mn":
            return (t_mn, tie_n, tie_m)
        return (0, tie_n, tie_m)

    def _render_stats_list(self):
        for w in self.stats_list_frame.winfo_children():
            w.destroy()

        table_index_map = {p: i for i, p in enumerate(self.table)}
        items = list(self.stats.items())
        tri = sorted(
            items,
            key=lambda it: self._stats_sort_key(it, table_index_map),
            reverse=self._stats_sort_desc,
        )

        canvas = tk.Canvas(self.stats_list_frame, bg=BG_DARK,
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.stats_list_frame, orient="vertical",
                                  command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._bind_mousewheel(canvas)

        def add_sort_hdr(parent, col_id, title, width):
            if self._stats_sort_column == col_id:
                title = f"{title} {'▼' if self._stats_sort_desc else '▲'}"
            lab = tk.Label(
                parent, text=title, font=FONT_SMALL, bg=BTN_BG,
                fg=FG_ACCENT if self._stats_sort_column == col_id else FG_SECONDARY,
                width=width, anchor="center", cursor="hand2",
            )
            lab.pack(side="left")
            lab.bind("<Button-1>", lambda e, c=col_id: self._stats_header_clicked(c))

        hdr = tk.Frame(inner, bg=BTN_BG, pady=5)
        hdr.pack(fill="x", pady=(0, 2))
        add_sort_hdr(hdr, "idx", "#", 4)
        add_sort_hdr(hdr, "total", "Tot.", 4)
        add_sort_hdr(hdr, "nombre", "Nombre", 7)
        add_sort_hdr(hdr, "mot", "Mot", 12)
        add_sort_hdr(hdr, "s_nm", "N→M", 5)
        add_sort_hdr(hdr, "s_mn", "M→N", 5)
        add_sort_hdr(hdr, "t_nm", "s/lettre", 9)
        add_sort_hdr(hdr, "t_mn", "s/ch.", 8)
        tk.Label(
            hdr, text=" ", font=FONT_SMALL, bg=BTN_BG,
            fg=FG_SECONDARY, width=4, anchor="center",
        ).pack(side="left")

        for i, ((nombre, mot), vals) in enumerate(tri):
            s_nm, s_mn, t_nm, t_mn = vals
            total_score = s_nm + s_mn
            if total_score >= 4:
                row_bg = "#0d2818"
            elif total_score < 0:
                row_bg = "#28181d"
            else:
                row_bg = BG_CARD if i % 2 == 0 else BG_CARD_HOVER

            row = tk.Frame(inner, bg=row_bg, pady=3)
            row.pack(fill="x", pady=1)

            rank = table_index_map.get((nombre, mot), -1)
            idx_txt = str(rank + 1) if rank >= 0 else "—"
            tk.Label(row, text=idx_txt, font=FONT_SMALL,
                     bg=row_bg, fg=FG_SECONDARY, width=4,
                     anchor="center").pack(side="left")
            tk.Label(row, text=str(total_score), font=FONT_SMALL,
                     bg=row_bg, fg=FG_PRIMARY, width=4,
                     anchor="center").pack(side="left")
            tk.Label(row, text=nombre, font=FONT_BODY_BOLD,
                     bg=row_bg, fg=FG_ACCENT, width=7,
                     anchor="center").pack(side="left")
            tk.Label(row, text=mot, font=FONT_BODY,
                     bg=row_bg, fg=FG_PRIMARY, width=12,
                     anchor="w").pack(side="left")

            nm_color = (FG_GREEN if s_nm > 0
                        else (FG_RED if s_nm < 0 else FG_SECONDARY))
            mn_color = (FG_GREEN if s_mn > 0
                        else (FG_RED if s_mn < 0 else FG_SECONDARY))

            tk.Label(row, text=str(s_nm), font=FONT_BODY,
                     bg=row_bg, fg=nm_color, width=5,
                     anchor="center").pack(side="left")
            tk.Label(row, text=str(s_mn), font=FONT_BODY,
                     bg=row_bg, fg=mn_color, width=5,
                     anchor="center").pack(side="left")

            tnm = f"{t_nm:.2f}" if t_nm > 0 else "—"
            tmn = f"{t_mn:.2f}" if t_mn > 0 else "—"
            tk.Label(row, text=tnm, font=FONT_SMALL,
                     bg=row_bg, fg=FG_SECONDARY, width=9,
                     anchor="center").pack(side="left")
            tk.Label(row, text=tmn, font=FONT_SMALL,
                     bg=row_bg, fg=FG_SECONDARY, width=8,
                     anchor="center").pack(side="left")

            del_lbl = tk.Label(
                row, text="✕", font=FONT_SMALL,
                bg=row_bg, fg=FG_RED, width=4, anchor="center",
                cursor="hand2",
            )
            del_lbl.pack(side="left")
            del_lbl.bind(
                "<Button-1>",
                lambda e, p=(nombre, mot): self._clear_stats_one_pair(p),
            )

    def _render_session_runs_list(self):
        for w in self.stats_list_frame.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.stats_list_frame, bg=BG_DARK,
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.stats_list_frame, orient="vertical", command=canvas.yview,
        )
        inner = tk.Frame(canvas, bg=BG_DARK)
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._bind_mousewheel(canvas)

        hdr = tk.Frame(inner, bg=BTN_BG, pady=5)
        hdr.pack(fill="x", pady=(0, 4))
        for title, w in (
            ("Date / heure", 20),
            ("Mode", 14),
            ("Durée (s)", 9),
            ("Score", 10),
            ("Err.", 5),
            ("Type", 9),
        ):
            tk.Label(
                hdr, text=title, font=FONT_SMALL, bg=BTN_BG,
                fg=FG_ACCENT, width=w, anchor="w",
            ).pack(side="left", padx=2)

        ordered = list(reversed(self.session_runs))
        if not ordered:
            tk.Label(
                inner,
                text="Aucune session enregistrée pour l’instant.",
                font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(anchor="w", pady=20)
            return

        for i, run in enumerate(ordered):
            row_bg = BG_CARD if i % 2 == 0 else BG_CARD_HOVER
            row = tk.Frame(inner, bg=row_bg, pady=3)
            row.pack(fill="x", pady=1)
            try:
                dt = datetime.datetime.fromisoformat(str(run.get("at", "")))
                date_s = (
                    f"{dt.day:02d}/{dt.month:02d}/{dt.year} "
                    f"{dt.hour:02d}:{dt.minute:02d}"
                )
            except (TypeError, ValueError):
                date_s = str(run.get("at", ""))[:16]
            kind_fr = SESSION_KIND_LABELS_FR.get(
                str(run.get("kind", "")), str(run.get("kind", "")),
            )
            d = float(run.get("duration_s", 0))
            tq = max(1, int(run.get("total_q", 0)))
            sc = int(run.get("score", 0))
            err = int(run.get("errors", 0))
            fc = bool(run.get("flashcard", False))
            typ = "Flashcards" if fc else "Quiz saisi"
            extra = ""
            if run.get("kind") == "full_table" and run.get("shuffle") is not None:
                extra = " · mélangé" if run.get("shuffle") else " · ordre"
            tk.Label(
                row, text=date_s, font=FONT_SMALL, bg=row_bg,
                fg=FG_PRIMARY, width=20, anchor="w",
            ).pack(side="left", padx=2)
            tk.Label(
                row, text=kind_fr + extra, font=FONT_SMALL, bg=row_bg,
                fg=FG_SECONDARY, width=14, anchor="w", wraplength=120,
            ).pack(side="left", padx=2)
            tk.Label(
                row, text=f"{d:.1f}", font=FONT_SMALL, bg=row_bg,
                fg=FG_ORANGE, width=9, anchor="w",
            ).pack(side="left", padx=2)
            tk.Label(
                row, text=f"{sc}/{tq}", font=FONT_SMALL, bg=row_bg,
                fg=FG_GREEN, width=10, anchor="w",
            ).pack(side="left", padx=2)
            tk.Label(
                row, text=str(err), font=FONT_SMALL, bg=row_bg,
                fg=FG_RED if err else FG_SECONDARY, width=5, anchor="w",
            ).pack(side="left", padx=2)
            tk.Label(
                row, text=typ, font=FONT_SMALL, bg=row_bg,
                fg=FG_SECONDARY, width=9, anchor="w",
            ).pack(side="left", padx=2)

