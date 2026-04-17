"""Parcours de la table."""
from mnemos.ui._quiz_shared import *  # noqa: F403, F401


class TableBrowseMixin:
    def show_table_view(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="📖 Ma table", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(20, 8))

        # Barre de recherche
        search_frame = tk.Frame(self.container, bg=BG_DARK)
        search_frame.pack(fill="x", padx=60, pady=(0, 8))

        tk.Label(search_frame, text="🔍", font=FONT_BODY,
                 bg=BG_DARK, fg=FG_SECONDARY).pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_table())
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=FONT_BODY, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY, relief="flat", width=30,
        )
        search_entry.pack(side="left", ipady=4)
        search_entry.focus_set()

        # Légende
        legend = tk.Frame(self.container, bg=BG_DARK)
        legend.pack(padx=60, anchor="w")
        for label, color in [("Maîtrisé", FG_GREEN), ("En cours", FG_YELLOW),
                             ("À revoir", FG_RED), ("Non vu", BTN_BG)]:
            tk.Label(legend, text="●", font=FONT_SMALL, bg=BG_DARK,
                     fg=color).pack(side="left", padx=(0, 2))
            tk.Label(legend, text=label, font=FONT_SMALL, bg=BG_DARK,
                     fg=FG_SECONDARY).pack(side="left", padx=(0, 12))
        tk.Label(legend, text="🎯", font=FONT_SMALL, bg=BG_DARK,
                 fg=FG_ORANGE).pack(side="left", padx=(8, 2))
        tk.Label(legend, text="Inclus au focus faibles", font=FONT_SMALL,
                 bg=BG_DARK, fg=FG_SECONDARY).pack(side="left", padx=(0, 12))

        # Zone table
        self.table_frame = tk.Frame(self.container, bg=BG_DARK)
        self.table_frame.pack(fill="both", expand=True, padx=40, pady=5)
        self._render_table_cards(self.table)

        btn_bar = tk.Frame(self.container, bg=BG_DARK)
        btn_bar.pack(pady=(5, 12))
        self.make_button(
            btn_bar, "⬅  Retour au menu", self.show_main_menu,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_bar, "✏️  Modifier la table", self._show_edit_table,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_bar, "📤  Exporter tout…", self._export_full_backup_file,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_bar, "📥  Importer tout…", self._import_full_backup_file,
        ).pack(side="left", padx=5)

    def _persist_weak_toggle(self, pair, enabled):
        """Marque / retire une paire des points faibles manuels (mode 2)."""
        if enabled:
            self.manual_weak.add(pair)
        else:
            self.manual_weak.discard(pair)
        self.manual_weak = save_manual_weak_set(self.manual_weak, self.table)

    def _filter_table(self):
        query = self.search_var.get().strip().lower()
        if query:
            filtered = [
                (n, m) for n, m in self.table
                if query in n.lower() or query in m.lower()
            ]
        else:
            filtered = self.table
        self._render_table_cards(filtered)

    def _render_table_cards(self, items):
        for w in self.table_frame.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.table_frame, bg=BG_DARK,
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical",
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

        cols = 5
        for i, (nombre, mot) in enumerate(items):
            r, c = divmod(i, cols)

            vals = self.stats.get((nombre, mot), _default_stats_row())
            total_s = vals[0] + vals[1]
            if total_s >= 4:
                border_color = FG_GREEN
            elif total_s < 0:
                border_color = FG_RED
            elif total_s > 0:
                border_color = FG_YELLOW
            else:
                border_color = BTN_BG

            cell = tk.Frame(inner, bg=border_color, padx=2, pady=2)
            cell.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

            inner_cell = tk.Frame(cell, bg=BG_CARD, padx=8, pady=6)
            inner_cell.pack(fill="both", expand=True)

            tk.Label(
                inner_cell, text=nombre, font=FONT_BODY_BOLD,
                bg=BG_CARD, fg=FG_ACCENT,
            ).pack()
            tk.Label(
                inner_cell, text=mot, font=FONT_SMALL,
                bg=BG_CARD, fg=FG_PRIMARY,
            ).pack()

            weak_var = tk.BooleanVar(value=(nombre, mot) in self.manual_weak)
            tk.Checkbutton(
                inner_cell, text="🎯 Point faible", variable=weak_var,
                command=lambda p=(nombre, mot), v=weak_var: self._persist_weak_toggle(
                    p, v.get(),
                ),
                font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=FG_ORANGE, highlightthickness=0,
            ).pack(pady=(4, 0))

        for c in range(cols):
            inner.columnconfigure(c, weight=1, minsize=150)

    # --------------------------------------------------------
