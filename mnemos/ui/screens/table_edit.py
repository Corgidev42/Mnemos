"""Édition table, import/export table, plan hebdo fichier."""
from mnemos.ui._quiz_shared import *  # noqa: F403, F401


class TableEditMixin:
    def _show_edit_table(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="✏️ Modifier la table", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(20, 5))
        tk.Label(
            self.container,
            text="Ajoute ou supprime des paires, ou modifie un mot. "
                 "Chaque nombre ne peut exister qu’une seule fois. "
                 "Sauvegarde au clic sur 💾 ou « Tout sauvegarder ».",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
            wraplength=720, justify="left",
        ).pack(pady=(0, 8))

        add_bar = tk.Frame(self.container, bg=BG_CARD, padx=12, pady=10,
                           highlightthickness=1, highlightbackground=BORDER_ACCENT)
        add_bar.pack(fill="x", padx=40, pady=(0, 8))
        tk.Label(
            add_bar, text="Nouvelle paire :", font=FONT_BODY_BOLD,
            bg=BG_CARD, fg=FG_PRIMARY,
        ).pack(side="left", padx=(0, 8))
        add_n = tk.Entry(
            add_bar, font=FONT_BODY, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY, relief="flat", width=10, justify="center",
        )
        add_n.pack(side="left", ipady=4)
        tk.Label(add_bar, text="→", bg=BG_CARD, fg=FG_SECONDARY).pack(
            side="left", padx=6)
        add_m = tk.Entry(
            add_bar, font=FONT_BODY, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY, relief="flat", width=22,
        )
        add_m.pack(side="left", ipady=4, padx=(0, 10))
        self.make_button(
            add_bar, "➕  Ajouter", lambda: self._add_new_table_row(add_n, add_m),
            width=14,
        ).pack(side="left")

        # Scrollable edit area
        edit_outer = tk.Frame(self.container, bg=BG_DARK)
        edit_outer.pack(fill="both", expand=True, padx=40, pady=5)

        canvas = tk.Canvas(edit_outer, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(edit_outer, orient="vertical",
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

        # Header row
        hdr = tk.Frame(inner, bg=BTN_BG, pady=6)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="Nombre", font=FONT_BODY_BOLD, bg=BTN_BG,
                 fg=FG_PRIMARY, width=10, anchor="center").pack(side="left")
        tk.Label(hdr, text="Mot actuel", font=FONT_BODY_BOLD, bg=BTN_BG,
                 fg=FG_PRIMARY, width=20, anchor="center").pack(side="left")
        tk.Label(hdr, text="Nouveau mot", font=FONT_BODY_BOLD, bg=BTN_BG,
                 fg=FG_PRIMARY, width=20, anchor="center").pack(side="left")
        tk.Label(hdr, text="Actions", font=FONT_BODY_BOLD, bg=BTN_BG,
                 fg=FG_PRIMARY, width=10, anchor="center").pack(side="left")

        self._edit_entries = {}  # index ligne -> StringVar

        for idx, (nombre, mot) in enumerate(self.table):
            row_bg = BG_CARD if idx % 2 == 0 else BG_CARD_HOVER
            row = tk.Frame(inner, bg=row_bg, pady=4)
            row.pack(fill="x", pady=1)

            tk.Label(row, text=nombre, font=FONT_BODY_BOLD,
                     bg=row_bg, fg=FG_ACCENT, width=10,
                     anchor="center").pack(side="left")

            tk.Label(row, text=mot, font=FONT_BODY,
                     bg=row_bg, fg=FG_PRIMARY, width=20,
                     anchor="center").pack(side="left")

            var = tk.StringVar(value=mot)
            self._edit_entries[idx] = var
            entry = tk.Entry(
                row, textvariable=var, font=FONT_BODY,
                bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                relief="flat", width=20, justify="center",
            )
            entry.pack(side="left", padx=5, ipady=3)

            save_btn = tk.Label(
                row, text="💾", font=FONT_BODY,
                bg=BTN_BG, fg=FG_GREEN, relief="flat",
                cursor="hand2", width=3, anchor="center", pady=3,
            )
            save_btn.bind(
                "<Button-1>",
                lambda e, i=idx, v=var, r=row, rb=row_bg: self._save_one_entry(
                    i, v, r, rb,
                ),
            )
            save_btn.bind("<Enter>", lambda e, b=save_btn: b.configure(bg=BTN_HOVER))
            save_btn.bind("<Leave>", lambda e, b=save_btn: b.configure(bg=BTN_BG))
            save_btn.pack(side="left", padx=4)

            del_btn = tk.Label(
                row, text="🗑", font=FONT_BODY,
                bg=BTN_BG, fg=FG_RED, relief="flat",
                cursor="hand2", width=3, anchor="center", pady=3,
            )
            del_btn.bind(
                "<Button-1>",
                lambda e, i=idx: self._delete_table_row_at(i),
            )
            del_btn.bind("<Enter>", lambda e, b=del_btn: b.configure(bg=BTN_HOVER))
            del_btn.bind("<Leave>", lambda e, b=del_btn: b.configure(bg=BTN_BG))
            del_btn.pack(side="left", padx=2)

        # Bottom buttons
        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=(10, 12))
        self.make_button(
            btn_frame, "💾  Tout sauvegarder", self._save_all_entries,
            accent=True,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_frame, "📤  Exporter tout…", self._export_full_backup_file,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_frame, "📥  Importer tout…", self._import_full_backup_file,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_frame, "⬅  Retour à la table", self.show_table_view,
        ).pack(side="left", padx=5)

    def _reset_stats_on_mot_change(self, nombre, old_mot, new_mot):
        """Nouvelle association nombre ↔ mot : les stats passées ne s'appliquent plus."""
        old_key = (nombre, old_mot)
        new_key = (nombre, new_mot)
        self.stats.pop(old_key, None)
        self.stats[new_key] = _default_stats_row()
        self.manual_weak.discard(old_key)
        self.manual_weak = save_manual_weak_set(self.manual_weak, self.table)

    def _add_new_table_row(self, n_entry, m_entry):
        """Ajoute une paire (nombre unique) et retrie la table."""
        n = n_entry.get().strip()
        m = m_entry.get().strip()
        if not n or not m:
            messagebox.showwarning(
                "Table", "Renseigne le nombre et le mot.",
            )
            return
        if any(p[0] == n for p in self.table):
            messagebox.showwarning(
                "Table", f"Le nombre « {n} » existe déjà dans la table.",
            )
            return
        self.table.append((n, m))
        self.stats[(n, m)] = _default_stats_row()
        self.table = _sort_table_pairs(self.table)
        n_entry.delete(0, "end")
        m_entry.delete(0, "end")
        self._persist_table()
        self._show_edit_table()

    def _delete_table_row_at(self, idx):
        """Supprime une ligne après confirmation."""
        if idx < 0 or idx >= len(self.table):
            return
        nombre, mot = self.table[idx]
        if not messagebox.askyesno(
            "Supprimer",
            f"Retirer la paire {nombre} → {mot} ?\n"
            "Les stats de cette paire seront effacées.",
        ):
            return
        pair = self.table.pop(idx)
        self.stats.pop(pair, None)
        self.manual_weak.discard(pair)
        self.manual_weak = save_manual_weak_set(self.manual_weak, self.table)
        self._persist_table()
        self._show_edit_table()

    def _save_one_entry(self, idx, var, row_frame, row_bg_normal):
        """Sauvegarde un seul mot modifié (ligne idx)."""
        if idx < 0 or idx >= len(self.table):
            return
        new_mot = var.get().strip()
        if not new_mot:
            return

        nombre, old_mot = self.table[idx]
        if new_mot != old_mot:
            self.table[idx] = (nombre, new_mot)
            self._reset_stats_on_mot_change(nombre, old_mot, new_mot)
            row_frame.configure(bg=FG_GREEN)
            self.after(
                400,
                lambda rf=row_frame, rb=row_bg_normal: rf.configure(bg=rb),
            )

        self._persist_table()

    def _save_all_entries(self):
        """Sauvegarde toutes les modifications de la table."""
        changes = 0
        for idx, (nombre, old_mot) in enumerate(list(self.table)):
            var = self._edit_entries.get(idx)
            if var:
                new_mot = var.get().strip()
                if new_mot and new_mot != old_mot:
                    self.table[idx] = (nombre, new_mot)
                    self._reset_stats_on_mot_change(nombre, old_mot, new_mot)
                    changes += 1

        self.table = _sort_table_pairs(self.table)
        self._persist_table()
        save_stats(self.stats, self.table)

        if changes > 0:
            messagebox.showinfo(
                "Sauvegardé",
                f"{changes} modification(s) enregistrée(s) !",
            )
        else:
            messagebox.showinfo("Rien à faire", "Aucune modification détectée.")

    def _export_table_file(self):
        """Exporte la table + stats (JSON v2) ou table + stats en colonnes (CSV)."""
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter la table",
            defaultextension=".json",
            filetypes=[
                ("JSON", "*.json"),
                ("CSV", "*.csv"),
            ],
        )
        if not path:
            return
        try:
            if path.lower().endswith(".csv"):
                with open(path, "w", encoding="utf-8", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(
                        ["Nombre", "Mot", "N→M", "M→N", "s/lettre", "s/chiffre"],
                    )
                    for n, m in self.table:
                        v = self.stats.get((n, m), _default_stats_row())
                        w.writerow([n, m, v[0], v[1], v[2], v[3]])
            else:
                payload = {
                    "mnemos_export_version": TABLE_EXPORT_VERSION,
                    "app": APP_NAME,
                    "app_version": VERSION,
                    "table": [[n, m] for n, m in self.table],
                    "stats": {
                        _stats_key(n, m): [
                            int(v[0]), int(v[1]),
                            float(v[2]), float(v[3]),
                        ]
                        for (n, m), v in self.stats.items()
                    },
                }
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
            messagebox.showinfo(
                "Export réussi",
                f"{len(self.table)} paires et leurs stats enregistrées dans :\n{path}",
            )
        except OSError as e:
            messagebox.showerror("Export", str(e))

    def _import_table_file(self):
        """Importe une table depuis JSON ou CSV (stats optionnelles dans le fichier)."""
        path = filedialog.askopenfilename(
            parent=self,
            title="Importer une table",
            filetypes=[
                ("JSON", "*.json"),
                ("CSV", "*.csv"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not path:
            return
        try:
            new_table, norm_stats_map = parse_imported_table_file(path)
        except (OSError, json.JSONDecodeError, ValueError) as e:
            messagebox.showerror("Import", str(e))
            return
        new_table = _sort_table_pairs(list(new_table))
        if norm_stats_map is not None:
            msg = (
                f"Remplacer la table actuelle ({len(self.table)} paires) par "
                f"{len(new_table)} paires importées ?\n\n"
                "⚠️ Ce fichier contient des statistiques : elles remplaceront "
                "les stats en mémoire pour les paires importées (les paires sans "
                "entrée dans le fichier repartent à zéro).\n\n"
                "Les paires absentes du fichier disparaissent de la table."
            )
        else:
            msg = (
                f"Remplacer la table actuelle ({len(self.table)} paires) par "
                f"{len(new_table)} paires importées ?\n\n"
                "Aucune stat dans le fichier : les stats des paires identiques "
                "(même nombre et même mot) sont conservées ; le reste est "
                "réinitialisé."
            )
        if not messagebox.askyesno("Importer la table", msg):
            return
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
            "Import réussi",
            f"{len(new_table)} paires chargées et enregistrées.",
        )
        self.show_table_view()

    def _persist_table(self):
        """Écrit la table modifiée en JSON."""
        path = _table_path()
        data = [[n, m] for n, m in self.table]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
            f.flush()
            os.fsync(f.fileno())
        save_stats(self.stats, self.table)

    def _export_weekly_plan_file(self):
        """Exporte le plan hebdomadaire en JSON (7 chaînes)."""
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter le plan hebdomadaire",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        try:
            days = load_weekly_plan_days()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(days, f, ensure_ascii=False, indent=2)
            messagebox.showinfo(
                "Export réussi",
                f"Plan des 7 jours enregistré dans :\n{path}",
            )
        except OSError as e:
            messagebox.showerror("Export", str(e))

    def _import_weekly_plan_file(self):
        """Importe un plan depuis JSON (liste ≥7 ou dict jours)."""
        path = filedialog.askopenfilename(
            parent=self,
            title="Importer le plan hebdomadaire",
            filetypes=[
                ("JSON", "*.json"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not path:
            return
        try:
            days = parse_imported_weekly_plan_file(path)
        except (OSError, json.JSONDecodeError, ValueError) as e:
            messagebox.showerror("Import", str(e))
            return
        if not messagebox.askyesno(
            "Importer le plan",
            "Remplacer le plan actuel (7 jours) par le contenu du fichier ?",
        ):
            return
        save_weekly_plan_days(days)
        messagebox.showinfo("Import réussi", "Plan enregistré.")
        self.show_main_menu()

