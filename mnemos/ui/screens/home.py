"""Accueil, sauvegarde complète, plan PDF, à propos, file MAJ."""
from mnemos.ui._quiz_shared import *  # noqa: F403, F401


class HomeMixin:
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

    # --------------------------------------------------------
    # Écran : Menu principal
    # --------------------------------------------------------
    def show_main_menu(self):
        self.clear()
        self.unbind("<Return>")
        for key in ("r", "f", "p"):
            self.unbind(key)

        # Stats résumé
        total = len(self.stats)
        bien_connus = sum(1 for v in self.stats.values() if v[0] + v[1] >= 4)
        en_cours = sum(1 for v in self.stats.values() if 0 < v[0] + v[1] < 4)
        a_revoir = sum(
            1 for v in self.stats.values()
            if v[0] + v[1] <= 0 and (v[0] != 0 or v[1] != 0)
        )
        non_vus = sum(
            1 for v in self.stats.values() if v[0] == 0 and v[1] == 0
        )

        stats_frame = self.make_card(self.container, padx=14, pady=8)
        stats_frame.pack(pady=(16, 10), padx=20, fill="x")

        # Barre de maîtrise
        bar_canvas = tk.Canvas(stats_frame, height=10, bg=BTN_BG,
                               highlightthickness=0)
        bar_canvas.pack(fill="x", pady=(0, 6))
        self.after(50, lambda: self._draw_mastery_bar(
            bar_canvas, total, bien_connus, en_cours, a_revoir, non_vus))

        stats_inner = tk.Frame(stats_frame, bg=BG_CARD)
        stats_inner.pack()

        for label, value, color in [
            ("Total", total, FG_PRIMARY),
            ("Maîtrisés", bien_connus, FG_GREEN),
            ("En cours", en_cours, FG_YELLOW),
            ("À revoir", a_revoir, FG_RED),
            ("Non vus", non_vus, FG_SECONDARY),
        ]:
            col = tk.Frame(stats_inner, bg=BG_CARD, padx=10)
            col.pack(side="left")
            tk.Label(col, text=str(value),
                     font=("Helvetica", 15, "bold"),
                     bg=BG_CARD, fg=color).pack()
            tk.Label(col, text=label, font=FONT_SMALL,
                     bg=BG_CARD, fg=FG_SECONDARY).pack()

        # ---- Colonnes : modes (s’étire) | plan hebdo (grille 2 colonnes) ----
        mid = tk.Frame(self.container, bg=BG_DARK)
        mid.pack(fill="both", expand=True, padx=20, pady=(0, 4))
        mid.rowconfigure(0, weight=1)
        mid.columnconfigure(0, weight=3, minsize=280)
        mid.columnconfigure(1, weight=2, minsize=340)

        left_col = tk.Frame(mid, bg=BG_DARK)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        modes_frame = tk.Frame(left_col, bg=BG_DARK)
        modes_frame.pack(fill="both", expand=True)

        modes = [
            ("1", "📦  Quiz par bloc", self.show_bloc_config),
            ("2", "🎯  Focus points faibles", self.start_focus_mode),
            ("3", "🎲  Quiz aléatoire", self.start_random_mode),
            ("4", "📋  Toute la table", self.start_full_mode),
        ]
        for key, text, cmd in modes:
            row = tk.Frame(modes_frame, bg=BG_DARK)
            row.pack(fill="x", pady=4)
            tk.Label(
                row, text=key, font=FONT_BODY_BOLD, bg=BG_INPUT,
                fg=FG_ACCENT, width=2, pady=4,
            ).pack(side="left", padx=(0, 6))
            self.make_button(row, text, cmd, fill_x=True).pack(
                side="left", fill="both", expand=True,
            )
            if key == "4":
                self._build_full_table_runs_home_panel(modes_frame)

        for key, _, cmd in modes:
            self.bind(key, lambda e, c=cmd: c())
        self.bind("p", lambda e: self._show_conseil_dialog())

        right_col = tk.Frame(mid, bg=BG_DARK)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._build_home_weekly_plan_panel(right_col)

        # ---- Boutons secondaires ----
        bottom_frame = tk.Frame(self.container, bg=BG_DARK)
        bottom_frame.pack(pady=(12, 8))
        self.make_button(
            bottom_frame, "📊  Statistiques", self.show_stats_view, width=22,
        ).pack(side="left", padx=4)
        self.make_button(
            bottom_frame, "📖  Parcourir la table", self.show_table_view,
            width=22,
        ).pack(side="left", padx=4)
        self.make_button(
            bottom_frame, "⚙️  Préférences", self.show_preferences, width=16,
        ).pack(side="left", padx=4)
        self.make_button(
            bottom_frame,
            "💡  Conseil",
            self._show_conseil_dialog,
            width=18,
        ).pack(side="left", padx=4)

        io_row = tk.Frame(self.container, bg=BG_DARK)
        io_row.pack(pady=(0, 4))
        self.make_button(
            io_row,
            "📤  Exporter tout (sauvegarde)…",
            self._export_full_backup_file,
            width=28,
        ).pack(side="left", padx=5)
        self.make_button(
            io_row,
            "📥  Importer tout (restauration)…",
            self._import_full_backup_file,
            width=30,
        ).pack(side="left", padx=5)

        # Pied : logo en bas à gauche (clic = À propos) · raccourcis · mise à jour
        footer_row = tk.Frame(self.container, bg=BG_DARK)
        footer_row.pack(side="bottom", fill="x", padx=12, pady=(0, 10))

        logo_img = _load_logo_photo(52)
        if logo_img:
            self._logo_ref = logo_img
            logo_lbl = tk.Label(footer_row, image=logo_img, bg=BG_DARK)
            logo_lbl.pack(side="left", anchor="w")
            logo_lbl.bind("<Button-1>", lambda e: self._show_about())
            logo_lbl.config(cursor="hand2")

        right_foot = tk.Frame(footer_row, bg=BG_DARK)
        right_foot.pack(side="right")
        upd_lbl = tk.Label(
            right_foot, text="🔄 Vérifier les mises à jour",
            font=FONT_SMALL, bg=BG_DARK, fg=FG_ACCENT, cursor="hand2",
        )
        upd_lbl.pack(side="right", padx=(12, 0))
        upd_lbl.bind("<Button-1>", lambda e: self._check_update())
        tk.Label(
            right_foot,
            text="Raccourcis : 1-4 = modes · P = conseil · Échap = menu · Entrée = valider",
            font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(side="right")

    def _open_weekly_plan_pdf(self):
        """Ouvre le PDF du plan de révision dans l’application par défaut (Aperçu, etc.)."""
        path = os.path.abspath(_weekly_plan_pdf_path())
        if not os.path.isfile(path):
            messagebox.showerror(
                APP_NAME,
                "Le fichier du plan hebdomadaire est introuvable.\n"
                "Réinstalle l’application ou contacte le support.",
            )
            return
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", path], start_new_session=True)
            elif sys.platform == "win32":
                os.startfile(path)  # noqa: S606
            else:
                subprocess.Popen(["xdg-open", path], start_new_session=True)
        except OSError as exc:
            messagebox.showerror(
                APP_NAME,
                f"Impossible d’ouvrir le PDF :\n{exc}",
            )

    def _build_home_weekly_plan_panel(self, parent):
        """Plan : titre + bouton éditer visibles, L–Me | Je–Di en deux colonnes."""
        for w in parent.winfo_children():
            w.destroy()

        plan_card = self.make_card(parent, padx=10, pady=8)
        plan_card.pack(fill="both", expand=True)

        head = tk.Frame(plan_card, bg=BG_CARD)
        head.pack(fill="x", pady=(0, 4))
        tk.Label(
            head, text="Plan de la semaine",
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_ACCENT,
        ).pack(side="left", anchor="w")
        self.make_button(
            head, "✏️  Modifier", self._open_weekly_plan_editor,
            accent=True, width=14,
        ).pack(side="right", padx=(8, 0))

        tk.Label(
            plan_card,
            text="Jour actuel surligné · texte éditable (bouton ci-dessus).",
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
            wraplength=400, justify="left",
        ).pack(anchor="w", pady=(0, 6))

        cols = tk.Frame(plan_card, bg=BG_CARD)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        left_wrap = tk.Frame(cols, bg=BG_CARD)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        right_wrap = tk.Frame(cols, bg=BG_CARD)
        right_wrap.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        today_i = datetime.date.today().weekday()
        days = load_weekly_plan_days()

        def day_cell(par, i, wrap_len):
            label = WEEKDAY_LABELS_FR[i]
            is_today = i == today_i
            wrap_bg = "#2a2040" if is_today else BG_INPUT
            border = FG_GOLD if is_today else BORDER_ACCENT
            thick = 2 if is_today else 1

            cell = tk.Frame(
                par, bg=wrap_bg, padx=1, pady=1,
                highlightthickness=thick, highlightbackground=border,
            )
            cell.pack(fill="x", pady=3)

            inner = tk.Frame(cell, bg=BG_CARD, padx=6, pady=4)
            inner.pack(fill="x")

            title = f"● {label}" if is_today else label
            title_fg = FG_GOLD if is_today else FG_PRIMARY
            tk.Label(
                inner, text=title, font=FONT_BODY_BOLD,
                bg=BG_CARD, fg=title_fg,
            ).pack(anchor="w")

            body = days[i] if i < len(days) else ""
            tk.Label(
                inner, text=body or "—",
                font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
                wraplength=wrap_len, justify="left", anchor="w",
            ).pack(anchor="w", pady=(1, 0))

        for i in range(0, 3):
            day_cell(left_wrap, i, 210)
        for i in range(3, 7):
            day_cell(right_wrap, i, 210)

    def _open_weekly_plan_editor(self):
        """Fenêtre modale : un champ par jour, sauvegarde dans App Support."""
        editor = tk.Toplevel(self)
        editor.title("Modifier le plan hebdomadaire")
        editor.configure(bg=BG_DARK)
        editor.transient(self)
        if sys.platform == "darwin":
            editor.attributes("-topmost", True)
            editor.after(400, lambda ed=editor: ed.attributes("-topmost", False))
        editor.grab_set()
        editor.geometry("640x520")
        editor.minsize(520, 400)
        editor.focus_force()

        tk.Label(
            editor, text="Plan hebdomadaire",
            font=FONT_TITLE, bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(16, 6))
        tk.Label(
            editor,
            text="Un bloc par jour (Lundi → Dimanche). Les changements sont enregistrés sur ce Mac.",
            font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
            wraplength=580,
        ).pack(pady=(0, 10))

        outer = tk.Frame(editor, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=18, pady=6)

        canvas = tk.Canvas(outer, bg=BG_DARK, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)
        inner.bind(
            "<Configure>",
            lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._bind_mousewheel(canvas)

        current = load_weekly_plan_days()
        text_widgets = []
        for i, day_name in enumerate(WEEKDAY_LABELS_FR):
            block = tk.Frame(inner, bg=BG_CARD, padx=10, pady=8,
                             highlightthickness=1, highlightbackground=BORDER_ACCENT)
            block.pack(fill="x", pady=6)
            tk.Label(
                block, text=day_name, font=FONT_BODY_BOLD,
                bg=BG_CARD, fg=FG_ACCENT,
            ).pack(anchor="w")
            t = tk.Text(
                block, height=3, width=72, font=FONT_BODY,
                bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                relief="flat", wrap="word",
            )
            t.pack(fill="x", pady=(6, 0))
            t.insert("1.0", current[i] if i < len(current) else "")
            text_widgets.append(t)

        def _save_plan():
            out = [tw.get("1.0", "end").strip() for tw in text_widgets]
            save_weekly_plan_days(out)
            messagebox.showinfo("Plan", "Plan enregistré.", parent=editor)
            editor.destroy()
            if self.container.winfo_children():
                self.show_main_menu()

        bar = tk.Frame(editor, bg=BG_DARK)
        bar.pack(pady=(10, 14))
        self.make_button(bar, "💾  Enregistrer", _save_plan, accent=True).pack(
            side="left", padx=6,
        )
        self.make_button(bar, "Annuler", editor.destroy).pack(side="left", padx=6)

    def _show_conseil_dialog(self):
        """Méthode Scan / Sensation / Action ; option pour ouvrir le PDF du plan."""
        win = tk.Toplevel(self)
        win.title("Conseil")
        win.configure(bg=BG_DARK)
        win.transient(self)
        win.geometry("620x480")
        win.minsize(480, 360)

        tk.Label(
            win, text="💡  Conseil",
            font=FONT_TITLE, bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(14, 6))

        frame = tk.Frame(win, bg=BG_DARK)
        frame.pack(fill="both", expand=True, padx=16, pady=6)

        txt = tk.Text(
            frame, wrap="word", font=FONT_BODY,
            bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
            relief="flat", padx=10, pady=10,
        )
        scroll = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.insert("1.0", _conseil_full_text())
        txt.configure(state="disabled")
        self._bind_mousewheel(txt)

        bottom = tk.Frame(win, bg=BG_DARK)
        bottom.pack(pady=(8, 12))
        pdf_path = os.path.abspath(_weekly_plan_pdf_path())
        if os.path.isfile(pdf_path):
            self.make_button(
                bottom, "📄  Ouvrir le PDF du plan (aperçu)",
                self._open_weekly_plan_pdf, width=32,
            ).pack(side="left", padx=6)
        self.make_button(bottom, "Fermer", win.destroy, width=12).pack(
            side="left", padx=6,
        )

    def _show_about(self):
        """Affiche version, pitch et chemin de l'app."""
        app_path = _get_app_bundle_path()
        path_info = app_path if app_path else sys.executable
        messagebox.showinfo(
            "À propos",
            f"{APP_NAME} v{VERSION}\n\n"
            f"Système majeur — mémoriser les associations nombre ↔ image.\n\n"
            f"Chemin : {path_info}\n\n"
            f"Menu : lien « Vérifier les mises à jour ».",
        )

    def _invoke_main(self, fn):
        """Exécute fn sur le thread Tk (obligatoire après du code réseau / worker)."""
        self._main_thread_queue.put(fn)

    def _pump_main_thread_queue(self):
        try:
            while True:
                fn = self._main_thread_queue.get_nowait()
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(80, self._pump_main_thread_queue)

    def _check_update(self):
        """Vérifie les mises à jour et affiche une boîte de dialogue."""
        check_for_update(self._invoke_main, self._on_update_result)

    def _on_update_result(self, ok, result):
        """Appelé sur le thread Tk après la requête GitHub."""
        if not ok:
            messagebox.showerror("Erreur", f"Impossible de vérifier : {result}")
            return
        if result.get("up_to_date"):
            messagebox.showinfo("À jour", f"Tu as déjà la dernière version (v{VERSION}).")
            return
        tag = result.get("tag", "")
        zip_url = result.get("zip_url")
        dmg_url = result.get("dmg_url")

        can_auto, auto_reason = _auto_update_eligibility()
        use_auto = bool(zip_url) and can_auto
        if use_auto:
            msg = (
                f"Une nouvelle version ({tag}) est disponible. "
                f"Mise à jour automatique ?"
            )
        elif not zip_url:
            msg = (
                f"Une nouvelle version ({tag}) est disponible. "
                f"Aucun fichier .zip sur la release (maj auto impossible). "
                f"Télécharger le .dmg pour installer à la main ?"
            )
        elif auto_reason == "from_dmg":
            msg = (
                f"Une nouvelle version ({tag}) est disponible. "
                f"Tu lances l’app depuis le disque image : copie « {APP_NAME} » "
                f"dans Applications, puis rouvre-la depuis le dossier Applications "
                f"pour activer la mise à jour automatique. "
                f"Télécharger le .dmg maintenant ?"
            )
        else:
            msg = (
                f"Une nouvelle version ({tag}) est disponible. "
                f"La mise à jour automatique ne fonctionne qu’avec l’application "
                f"« {APP_NAME}.app » installée (pas en lançant le script Python). "
                f"Télécharger le .dmg ?"
            )
        if not messagebox.askyesno("Mise à jour disponible", msg):
            return

        if use_auto:
            _install_update_self(
                self._invoke_main, zip_url, tag, self._on_download_result,
            )
        elif dmg_url:
            download_and_open_dmg(
                dmg_url, self._invoke_main, self._on_download_result,
            )
        else:
            messagebox.showinfo(
                "Mise à jour disponible",
                f"Version {tag} disponible sur GitHub.",
            )

    def _on_download_result(self, success, message):
        """Appelé sur le thread Tk après téléchargement / install."""
        if success:
            if message == "restart":
                support = _get_app_support_dir()
                messagebox.showinfo(
                    "Mise à jour",
                    "La nouvelle version a été téléchargée. L’app va se fermer, "
                    "puis le remplacement dans Applications et la réouverture se "
                    "font en arrière-plan (quelques secondes).\n\n"
                    "Si l’app ne revient pas, ouvre le fichier "
                    "« updater_last.log » dans :\n"
                    f"{support}",
                )
                self._on_quit()
            else:
                messagebox.showinfo("Téléchargement terminé", message)
        else:
            messagebox.showerror("Erreur", f"Échec : {message}")

