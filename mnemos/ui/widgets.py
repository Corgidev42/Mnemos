"""Widgets Tk réutilisables (mixins QuizApp)."""
from mnemos.ui._quiz_shared import *  # noqa: F403, F401


class WidgetsMixin:
    def make_button(self, parent, text, command, accent=False, width=25,
                    danger=False, fill_x=False):
        if danger:
            bg, fg, hover_bg = FG_RED, "#ffffff", "#fda4af"
        elif accent:
            bg, fg, hover_bg = BTN_ACCENT, BTN_ACCENT_FG, "#8b5cf6"
        else:
            bg, fg, hover_bg = BTN_BG, FG_PRIMARY, BTN_HOVER

        kw = dict(
            text=text,
            font=FONT_BODY_BOLD, bg=bg, fg=fg,
            cursor="hand2", pady=8, padx=6,
            relief="flat", anchor="center",
            highlightthickness=1, highlightbackground=BORDER_ACCENT,
        )
        if not fill_x:
            kw["width"] = width
        btn = tk.Label(parent, **kw)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg, highlightbackground=FG_ACCENT))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg, highlightbackground=BORDER_ACCENT))
        return btn

    def make_card(self, parent, padx=24, pady=18, **kwargs):
        """Carte avec bordure subtile et padding généreux (padx/pady surchargeables)."""
        card = tk.Frame(parent, bg=BG_CARD, padx=padx, pady=pady,
                        highlightthickness=1, highlightbackground=BORDER_ACCENT, **kwargs)
        return card

    def _add_flashcard_option(self, parent, *, bg=BG_CARD):
        """Case à cocher : session en flashcards au lieu du quiz saisi."""
        tk.Checkbutton(
            parent,
            text="  Mode flashcards (retourner la carte, auto-évaluation)",
            variable=self.session_flashcard_var,
            font=FONT_BODY_BOLD, bg=bg, fg=FG_PRIMARY,
            selectcolor=CHECK_BG, activebackground=bg,
            activeforeground=CHECK_ON, highlightthickness=0,
            anchor="w",
        ).pack(anchor="w", pady=(12, 4))

    def _launch_flashcard_from_questions(self):
        """Démarre une session flashcard à partir de self.questions déjà construite."""
        self.fc_cards = list(self.questions)
        self.fc_idx = 0
        self.fc_revealed = False
        self.fc_score = 0
        self.fc_streak = 0
        self.fc_best_streak = 0
        self.fc_results = []
        self.fc_quiz_start = time.time()
        self._show_flashcard()

    def _record_session_run(
        self, *, total_q, score, errors_count, duration_s, flashcard,
    ):
        """Enregistre une session terminée (temps, score, erreurs, mode)."""
        if total_q <= 0:
            return
        kind = getattr(self, "_session_kind", None) or "bloc"
        if kind not in _VALID_SESSION_KINDS:
            kind = "bloc"
        meta = getattr(self, "_full_table_meta", None) or {}
        run = {
            "at": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "kind": kind,
            "duration_s": round(float(duration_s), 1),
            "total_q": int(total_q),
            "score": int(score),
            "errors": int(errors_count),
            "flashcard": bool(flashcard),
            "sens": str(meta.get("sens", "")),
            "shuffle": bool(meta.get("shuffle", False)),
        }
        row = _normalize_session_run(run)
        if not row:
            return
        self.session_runs.append(row)
        self.session_runs = self.session_runs[-500:]
        save_session_runs(self.session_runs)

    @staticmethod
    def _format_session_run_summary_line(run):
        """Résumé d’une session pour l’accueil ou la liste stats."""
        mois = (
            "janv.", "févr.", "mars", "avr.", "mai", "juin",
            "juil.", "août", "sept.", "oct.", "nov.", "déc.",
        )
        try:
            dt = datetime.datetime.fromisoformat(str(run.get("at", "")))
            date_s = f"{dt.day} {mois[dt.month - 1]} {dt.year}, {dt.hour:02d}:{dt.minute:02d}"
        except (TypeError, ValueError):
            date_s = str(run.get("at", ""))[:19]
        d = float(run.get("duration_s", 0))
        tq = int(run.get("total_q", 0))
        sc = int(run.get("score", 0))
        err = int(run.get("errors", 0))
        fc = bool(run.get("flashcard", False))
        mode_lbl = "flashcards" if fc else "quiz"
        kind_fr = SESSION_KIND_LABELS_FR.get(
            str(run.get("kind", "")), str(run.get("kind", "")),
        )
        return (
            f"{date_s} · {kind_fr} · {mode_lbl} · {d:.0f}s · {sc}/{tq} · {err} err."
        )

    def _build_full_table_runs_home_panel(self, parent):
        """Résumé des dernières sessions « Toute la table » (détail dans Statistiques)."""
        box = tk.Frame(parent, bg=BG_DARK)
        box.pack(fill="x", pady=(10, 4))
        inner = self.make_card(box, padx=12, pady=10)
        inner.pack(fill="x")
        tk.Label(
            inner,
            text="Dernières sessions « Toute la table »",
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_ACCENT,
        ).pack(anchor="w")
        ft_runs = [r for r in self.session_runs if r.get("kind") == "full_table"]
        runs = list(reversed(ft_runs[-5:]))
        if not runs:
            tk.Label(
                inner,
                text="Aucune session enregistrée pour l’instant.",
                font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
                wraplength=520, justify="left",
            ).pack(anchor="w", pady=(6, 4))
        else:
            for run in runs:
                tk.Label(
                    inner,
                    text=self._format_session_run_summary_line(run),
                    font=FONT_SMALL, bg=BG_CARD, fg=FG_PRIMARY,
                    wraplength=520, justify="left",
                ).pack(anchor="w", pady=(2, 0))
        tk.Label(
            inner,
            text="Historique complet : menu Statistiques → onglet « Sessions ».",
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
            wraplength=520, justify="left",
        ).pack(anchor="w", pady=(6, 0))

    def _build_full_backup_payload(self):
        """Données pour une sauvegarde JSON complète."""
        return {
            "mnemos_full_backup_version": FULL_BACKUP_VERSION,
            "app": APP_NAME,
            "app_version": VERSION,
            "table": [[n, m] for n, m in self.table],
            "stats": {
                _stats_key(n, m): [
                    int(v[0]), int(v[1]), float(v[2]), float(v[3]),
                ]
                for (n, m), v in self.stats.items()
            },
            "preferences": {
                k: int(self.preferences.get(k, DEFAULT_PREFERENCES[k]))
                for k in DEFAULT_PREFERENCES
            },
            "weekly_plan": list(load_weekly_plan_days()),
            "manual_weak": sorted([list(p) for p in self.manual_weak]),
            "session_runs": list(self.session_runs),
        }

    def _export_full_backup_file(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter une sauvegarde complète",
            defaultextension=".json",
            filetypes=[("JSON Mnemos", "*.json")],
        )
        if not path:
            return
        try:
            payload = self._build_full_backup_payload()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            messagebox.showinfo(
                "Export réussi",
                "Sauvegarde enregistrée (table, stats, plan, préférences, "
                f"points faibles, {len(self.session_runs)} session(s)) :\n{path}",
            )
        except OSError as e:
            messagebox.showerror("Export", str(e))

    def _import_full_backup_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Importer une sauvegarde",
            filetypes=[("JSON", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            messagebox.showerror("Import", str(e))
            return
        if not isinstance(data, dict):
            messagebox.showerror("Import", "Format JSON invalide.")
            return
        if int(data.get("mnemos_full_backup_version", 0)) >= 1:
            if not messagebox.askyesno(
                "Restaurer la sauvegarde",
                "Remplacer sur ce Mac : la table, les stats, le plan hebdomadaire, "
                "les préférences, les points faibles manuels et l’historique des "
                "sessions par le contenu de ce fichier ?\n\n"
                "Cette action ne peut pas être annulée (pense à exporter d’abord "
                "une copie si tu veux conserver l’état actuel).",
            ):
                return
            try:
                rows = data.get("table")
                if not isinstance(rows, list):
                    raise ValueError("Champ « table » manquant ou invalide.")
                new_table = _sort_table_pairs(_pairs_from_json_rows(rows))
                st = data.get("stats")
                if isinstance(st, dict) and st:
                    norm_map = _norm_map_from_stats_json_obj(st)
                else:
                    norm_map = None
                merged = merged_stats_for_imported_table(
                    new_table, norm_map, self.stats,
                )
                self.table = new_table
                self.stats = merged
                prefs = data.get("preferences")
                out = dict(DEFAULT_PREFERENCES)
                if isinstance(prefs, dict):
                    for k in DEFAULT_PREFERENCES:
                        if k in prefs:
                            try:
                                out[k] = max(
                                    0, min(120_000, int(prefs[k])),
                                )
                            except (TypeError, ValueError):
                                pass
                self.preferences = save_preferences(out)
                wp = data.get("weekly_plan")
                if isinstance(wp, list) and len(wp) >= 7:
                    save_weekly_plan_days(
                        [str(wp[i]).strip() for i in range(7)],
                    )
                else:
                    save_weekly_plan_days(list(DEFAULT_WEEKLY_PLAN_DAYS))
                mw = data.get("manual_weak")
                valid = {(n, m) for n, m in new_table}
                if isinstance(mw, list):
                    s = set()
                    for item in mw:
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            p = (str(item[0]).strip(), str(item[1]).strip())
                            if p in valid:
                                s.add(p)
                    self.manual_weak = save_manual_weak_set(s, new_table)
                else:
                    self.manual_weak = save_manual_weak_set(set(), new_table)
                sr = data.get("session_runs")
                new_runs = []
                if isinstance(sr, list):
                    for item in sr:
                        row = _normalize_session_run(item)
                        if row:
                            new_runs.append(row)
                self.session_runs = new_runs[-500:]
                save_session_runs(self.session_runs)
                self._persist_table()
            except (ValueError, TypeError, KeyError) as e:
                messagebox.showerror("Import", str(e))
                return
            messagebox.showinfo("Import", "Sauvegarde restaurée.")
            self.show_main_menu()
            return
        if int(data.get("mnemos_export_version", 0)) >= 2 and "table" in data:
            if not messagebox.askyesno(
                "Fichier table + stats",
                "Ce fichier est une exportation « table + stats » seulement "
                "(sans plan ni historique de sessions). Importer uniquement la "
                "table et les statistiques ?",
            ):
                return
            try:
                new_table, norm_stats_map = parse_imported_table_file(path)
            except (OSError, json.JSONDecodeError, ValueError) as e:
                messagebox.showerror("Import", str(e))
                return
            new_table = _sort_table_pairs(list(new_table))
            merged = merged_stats_for_imported_table(
                new_table, norm_stats_map, self.stats,
            )
            self.table = new_table
            self.stats = merged
            self.manual_weak = save_manual_weak_set(
                {p for p in self.manual_weak if p in set(new_table)},
                new_table,
            )
            self._persist_table()
            messagebox.showinfo(
                "Import",
                f"{len(new_table)} paires et stats mises à jour.",
            )
            self.show_main_menu()
            return
        messagebox.showerror(
            "Import",
            "Fichier non reconnu : attendu une sauvegarde complète "
            f"(mnemos_full_backup_version ≥ {FULL_BACKUP_VERSION}) ou un export "
            f"table Mnemos (mnemos_export_version ≥ {TABLE_EXPORT_VERSION}).",
        )

    @staticmethod
    def _bind_mousewheel(widget):
        """Défilement molette sur le widget (Canvas, Text, etc.) — pas de bind global."""

        def _on_mousewheel(event):
            if sys.platform == "win32":
                # Windows : delta multiple de 120 par cran ; ancien code scrollait trop fort.
                step = int(-event.delta / 120)
                if step == 0:
                    step = -1 if event.delta > 0 else 1
                widget.yview_scroll(step, "units")
            elif sys.platform == "darwin":
                d = event.delta
                if abs(d) > 100:
                    widget.yview_scroll(int(-d / 40), "units")
                elif abs(d) > 8:
                    widget.yview_scroll(int(-d / 12), "units")
                else:
                    widget.yview_scroll(-1 if d > 0 else 1, "units")
            else:
                if event.delta:
                    widget.yview_scroll(int(-event.delta / 120), "units")

        widget.bind("<MouseWheel>", _on_mousewheel)
        widget.bind("<Button-4>", lambda e: widget.yview_scroll(-2, "units"))
        widget.bind("<Button-5>", lambda e: widget.yview_scroll(2, "units"))
