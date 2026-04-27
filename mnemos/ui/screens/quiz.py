"""Modes quiz : blocs, focus, aléatoire, toute la table, questions."""
from mnemos.ui._quiz_shared import *  # noqa: F403, F401


class QuizMixin:
    def show_bloc_config(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="📦 Quiz par bloc", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(35, 15))

        card = self.make_card(self.container)
        card.pack(padx=80, fill="x")

        n_blocs = _bloc_count_for_table(self.table)
        last_start = (n_blocs - 1) * 10
        tk.Label(
            card,
            text=(
                "Sélectionne les blocs à réviser (tranches de 10 nombres : 0–9, 10–19, …). "
                f"Ta table génère {n_blocs} bloc(s), jusqu’à "
                f"{last_start}–{last_start + 9}."
            ),
            font=FONT_BODY, bg=BG_CARD, fg=FG_SECONDARY, wraplength=600,
        ).pack(pady=(5, 8))
        rows_g = max(1, (n_blocs + 3) // 4)
        scroll_h = min(440, max(168, 20 + rows_g * 36))
        scroll_wrap = tk.Frame(card, bg=BG_CARD, height=scroll_h)
        scroll_wrap.pack(fill="x", pady=4)
        scroll_wrap.pack_propagate(False)
        b_canvas = tk.Canvas(
            scroll_wrap, bg=BG_CARD, highlightthickness=0,
            height=max(140, scroll_h - 8),
        )
        b_sb = ttk.Scrollbar(scroll_wrap, orient="vertical", command=b_canvas.yview)
        blocs_frame = tk.Frame(b_canvas, bg=BG_CARD)
        blocs_frame.bind(
            "<Configure>",
            lambda e, c=b_canvas: c.configure(scrollregion=c.bbox("all")),
        )
        b_canvas.create_window((0, 0), window=blocs_frame, anchor="nw")
        b_canvas.configure(yscrollcommand=b_sb.set)
        b_canvas.pack(side="left", fill="both", expand=True)
        b_sb.pack(side="right", fill="y")
        self._bind_mousewheel(b_canvas)

        self.bloc_vars = {}
        for i in range(n_blocs):
            start = i * 10
            end = start + 9
            var = tk.BooleanVar(value=False)
            self.bloc_vars[i] = var
            cb = tk.Checkbutton(
                blocs_frame, text=f"  {start:>3}–{end}", variable=var,
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=CHECK_ON, highlightthickness=0,
                indicatoron=True, onvalue=True, offvalue=False,
            )
            cb.grid(row=i // 4, column=i % 4, padx=12, pady=5, sticky="w")

        # Sélection rapide
        quick_frame = tk.Frame(card, bg=BG_CARD)
        quick_frame.pack(pady=(8, 5))
        self.make_button(
            quick_frame, "Tout sélectionner", self._select_all_blocs, width=18,
        ).pack(side="left", padx=5)
        self.make_button(
            quick_frame, "Tout désélectionner", self._deselect_all_blocs,
            width=18,
        ).pack(side="left", padx=5)

        tens_frame = tk.Frame(card, bg=BG_CARD)
        tens_frame.pack(pady=(6, 2))
        tk.Label(
            tens_frame, text="Sélection rapide :",
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))
        row_a = tk.Frame(tens_frame, bg=BG_CARD)
        row_a.pack(fill="x")
        self.make_button(
            row_a, "Dizaines « paires » (0–9, 20–29, …)",
            self._select_even_tens_blocs,
            width=28,
        ).pack(side="left", padx=4, pady=2)
        self.make_button(
            row_a, "Dizaines « impaires » (10–19, …)",
            self._select_odd_tens_blocs,
            width=28,
        ).pack(side="left", padx=4, pady=2)
        row_b = tk.Frame(tens_frame, bg=BG_CARD)
        row_b.pack(fill="x")
        self.make_button(
            row_b, "Tous les nombres pairs", self._start_quiz_even_numbers,
            width=24,
        ).pack(side="left", padx=4, pady=2)
        self.make_button(
            row_b, "Tous les nombres impairs", self._start_quiz_odd_numbers,
            width=24,
        ).pack(side="left", padx=4, pady=2)

        # Direction
        self._add_direction_picker(card)
        self._add_flashcard_option(card)

        # Boutons
        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=20)
        self.make_button(btn_frame, "🚀  Lancer le quiz",
                         self._start_bloc_quiz, accent=True).pack(
            side="left", padx=10)
        self.make_button(btn_frame, "⬅  Retour",
                         self.show_main_menu).pack(side="left", padx=10)

    def _select_all_blocs(self):
        for v in self.bloc_vars.values():
            v.set(True)

    def _deselect_all_blocs(self):
        for v in self.bloc_vars.values():
            v.set(False)

    def _select_even_tens_blocs(self):
        """Toutes les tranches 0–9, 20–29, … dont l’indice de dizaine est pair."""
        for i, v in self.bloc_vars.items():
            v.set(i % 2 == 0)

    def _select_odd_tens_blocs(self):
        """Toutes les tranches 10–19, 30–39, … dont l’indice de dizaine est impair."""
        for i, v in self.bloc_vars.items():
            v.set(i % 2 == 1)

    def _start_quiz_even_numbers(self):
        pairs = []
        for p in self.table:
            v = _parse_nombre_int(p[0])
            if v is not None and v % 2 == 0:
                pairs.append(p)
        if not pairs:
            messagebox.showwarning(
                "Attention",
                "Aucune paire avec nombre pair dans la table.",
            )
            return
        self._build_questions(
            pairs,
            use_flashcard=self.session_flashcard_var.get(),
            session_kind="bloc",
        )

    def _start_quiz_odd_numbers(self):
        pairs = []
        for p in self.table:
            v = _parse_nombre_int(p[0])
            if v is not None and v % 2 != 0:
                pairs.append(p)
        if not pairs:
            messagebox.showwarning(
                "Attention",
                "Aucune paire avec nombre impair dans la table.",
            )
            return
        self._build_questions(
            pairs,
            use_flashcard=self.session_flashcard_var.get(),
            session_kind="bloc",
        )

    def _add_direction_picker(self, parent):
        """Widget de sélection de direction réutilisable."""
        sens_frame = tk.Frame(parent, bg=BG_CARD)
        sens_frame.pack(pady=(12, 5))
        tk.Label(sens_frame, text="Direction :", font=FONT_BODY_BOLD,
                 bg=BG_CARD, fg=FG_PRIMARY).pack(side="left", padx=(0, 10))

        self.sens_var = tk.StringVar(value="3")
        for text, val in [("Nombre → Mot", "1"), ("Mot → Nombre", "2"),
                          ("Les deux", "3")]:
            tk.Radiobutton(
                sens_frame, text=f"  {text}", variable=self.sens_var,
                value=val,
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=CHECK_ON, highlightthickness=0,
            ).pack(side="left", padx=8)

    def _start_bloc_quiz(self):
        selected = [i for i, v in self.bloc_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Attention",
                                   "Sélectionne au moins un bloc !")
            return
        pairs = []
        for bloc_i in selected:
            pairs.extend(_pairs_in_bloc_indices(self.table, bloc_i))
        if not pairs:
            messagebox.showwarning("Attention",
                                   "Aucune correspondance pour ces blocs.")
            return
        self._build_questions(
            pairs,
            use_flashcard=self.session_flashcard_var.get(),
            session_kind="bloc",
        )

    # --------------------------------------------------------
    # Modes de démarrage rapide
    # --------------------------------------------------------
    def start_focus_mode(self):
        self._show_sens_then_start(self._do_start_focus)

    def _do_start_focus(self):
        manual = [p for p in self.manual_weak if p in self.stats]
        tri = sorted(self.stats.items(),
                     key=lambda x: x[1][0] + x[1][1])
        seen = set(manual)
        pool = list(manual)
        for k, _v in tri:
            if len(pool) >= 20:
                break
            if k in seen:
                continue
            pool.append(k)
            seen.add(k)
        if not pool:
            messagebox.showwarning(
                "Attention",
                "Aucune paire à réviser (stats ou points faibles manuels).",
            )
            return
        self._build_questions(
            pool,
            use_flashcard=self.session_flashcard_var.get(),
            session_kind="focus",
        )

    def start_random_mode(self):
        self._show_random_config()

    def _show_random_config(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="🎲 Quiz aléatoire", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(60, 20))

        card = self.make_card(self.container)
        card.pack(padx=120)

        row_n = tk.Frame(card, bg=BG_CARD)
        row_n.pack(fill="x", pady=(8, 12))
        tk.Label(
            row_n, text="Nombre de questions :",
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
        ).pack(side="left", padx=(0, 10))
        self.random_n_var = tk.StringVar(value="20")
        tk.Entry(
            row_n, textvariable=self.random_n_var, font=FONT_BODY,
            bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
            relief="flat", width=8, justify="center",
        ).pack(side="left", ipady=4)
        tk.Label(
            row_n,
            text="  (tirage avec remise dans la table)",
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
        ).pack(side="left", padx=(10, 0))

        self._add_direction_picker(card)
        self._add_flashcard_option(card)

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=30)
        self.make_button(
            btn_frame, "🚀  Lancer", self._do_start_random,
            accent=True,
        ).pack(side="left", padx=10)
        self.make_button(
            btn_frame, "⬅  Retour", self.show_main_menu,
        ).pack(side="left", padx=10)

    def _do_start_random(self):
        try:
            nq = int(self.random_n_var.get().strip())
        except (ValueError, AttributeError):
            messagebox.showwarning(
                "Attention", "Nombre de questions invalide (entier).")
            return
        if nq < 1:
            messagebox.showwarning(
                "Attention", "Il faut au moins une question.")
            return
        if nq > 500:
            messagebox.showwarning(
                "Attention", "Maximum 500 questions pour cette session.")
            return
        pairs = [random.choice(self.table) for _ in range(nq)]
        self._build_questions(
            pairs,
            use_flashcard=self.session_flashcard_var.get(),
            session_kind="random",
        )

    def start_full_mode(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="📋  Toute la table", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(45, 10))
        tk.Label(
            self.container,
            text="Révision de toutes les paires. Choisis la direction et l’ordre des questions.",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY, wraplength=560,
        ).pack(pady=(0, 14))

        card = self.make_card(self.container)
        card.pack(padx=80, fill="x")

        self._add_direction_picker(card)

        self.full_shuffle_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            card,
            text="  Mélanger les questions (ordre aléatoire)",
            variable=self.full_shuffle_var,
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
            selectcolor=CHECK_BG, activebackground=BG_CARD,
            activeforeground=CHECK_ON, highlightthickness=0, anchor="w",
        ).pack(anchor="w", pady=(14, 2))
        tk.Label(
            card,
            text="       Décoché : ordre croissant des nombres, sans mélange.",
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY, wraplength=520,
            justify="left",
        ).pack(anchor="w")

        self._add_flashcard_option(card)

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=28)
        self.make_button(
            btn_frame, "🚀  Lancer", self._do_start_full,
            accent=True,
        ).pack(side="left", padx=10)
        self.make_button(
            btn_frame, "⬅  Retour", self.show_main_menu,
        ).pack(side="left", padx=10)

    def _do_start_full(self):
        shuffle_q = self.full_shuffle_var.get()
        self._full_table_meta = {
            "sens": self.sens_var.get(),
            "shuffle": shuffle_q,
        }
        self._build_questions(
            list(self.table),
            shuffle_questions=shuffle_q,
            use_flashcard=self.session_flashcard_var.get(),
            session_kind="full_table",
        )

    def _show_sens_then_start(self, callback):
        """Demande la direction puis lance le quiz."""
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="Direction du quiz", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(60, 25))

        self.sens_var = tk.StringVar(value="3")
        card = self.make_card(self.container)
        card.pack(padx=120)

        options = [
            ("1", "Nombre → Mot", "On te donne le nombre, trouve le mot"),
            ("2", "Mot → Nombre", "On te donne le mot, trouve le nombre"),
            ("3", "Les deux sens", "Questions mélangées dans les deux sens"),
        ]
        for val, title, desc in options:
            f = tk.Frame(card, bg=BG_CARD, pady=5)
            f.pack(fill="x")
            tk.Radiobutton(
                f, text=f"  {title}", variable=self.sens_var, value=val,
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=CHECK_ON, highlightthickness=0, anchor="w",
            ).pack(anchor="w")
            tk.Label(f, text=f"       {desc}", font=FONT_SMALL,
                     bg=BG_CARD, fg=FG_SECONDARY).pack(anchor="w")

        self._add_flashcard_option(card)

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=30)
        self.make_button(btn_frame, "🚀  Lancer", callback,
                         accent=True).pack(side="left", padx=10)
        self.make_button(btn_frame, "⬅  Retour",
                         self.show_main_menu).pack(side="left", padx=10)

    def _unbind_menu_keys(self):
        """Détache les raccourcis du menu principal."""
        for key in ("1", "2", "3", "4", "5", "p"):
            self.unbind(key)

    # --------------------------------------------------------
    # Tirage aléatoire (X entrées sans remise — nombres ou mots)
    # --------------------------------------------------------
    def show_draw_config(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="🎴 Tirage aléatoire",
            font=FONT_TITLE, bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(40, 12))

        tk.Label(
            self.container,
            text=(
                "Tire X entrées au hasard dans ta table (sans doublon). "
                "Utile pour un entraînement libre ou pour piocher des ancres "
                "(ex. liste de courses)."
            ),
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY, wraplength=560,
        ).pack(pady=(0, 14))

        card = self.make_card(self.container)
        card.pack(padx=100, fill="x")

        row_n = tk.Frame(card, bg=BG_CARD)
        row_n.pack(fill="x", pady=(8, 10))
        tk.Label(
            row_n, text="Nombre d’entrées (X) :",
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
        ).pack(side="left", padx=(0, 10))
        self.draw_n_var = tk.StringVar(value="5")
        tk.Entry(
            row_n, textvariable=self.draw_n_var, font=FONT_BODY,
            bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
            relief="flat", width=8, justify="center",
        ).pack(side="left", ipady=4)
        tk.Label(
            row_n,
            text=f"  (max. {len(self.table)} — ta table actuelle)",
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
        ).pack(side="left", padx=(10, 0))

        tk.Label(
            card, text="Afficher :",
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
        ).pack(anchor="w", pady=(10, 4))

        self.draw_display_var = tk.StringVar(value="nombre")
        for val, title, desc in [
            (
                "nombre",
                "Les nombres seuls",
                "Reconstruis l’image mentale associée à chaque chiffre.",
            ),
            (
                "mot",
                "Les mots seuls",
                "Utilise les images comme ancres (ex. liste de courses).",
            ),
        ]:
            f = tk.Frame(card, bg=BG_CARD, pady=4)
            f.pack(fill="x")
            tk.Radiobutton(
                f, text=f"  {title}", variable=self.draw_display_var,
                value=val,
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=CHECK_ON, highlightthickness=0, anchor="w",
            ).pack(anchor="w")
            tk.Label(
                f, text=f"       {desc}", font=FONT_SMALL,
                bg=BG_CARD, fg=FG_SECONDARY,
            ).pack(anchor="w")

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=28)
        self.make_button(
            btn_frame, "🎲  Tirer", self._do_start_draw, accent=True,
        ).pack(side="left", padx=10)
        self.make_button(
            btn_frame, "⬅  Retour", self.show_main_menu,
        ).pack(side="left", padx=10)

    def _do_start_draw(self):
        try:
            n_req = int(self.draw_n_var.get().strip())
        except (ValueError, AttributeError):
            messagebox.showwarning(
                "Attention", "Nombre d’entrées invalide (entier).")
            return
        if n_req < 1:
            messagebox.showwarning(
                "Attention", "Il faut au moins une entrée.")
            return
        n_table = len(self.table)
        if n_table < 1:
            messagebox.showwarning(
                "Attention", "Ta table est vide.")
            return
        n = min(n_req, n_table)
        if n < n_req:
            messagebox.showinfo(
                "Tirage",
                f"Ta table contient {n_table} entrée(s). "
                f"Le tirage utilisera X = {n}.",
            )
        self._draw_last_n = n
        self._draw_last_display = self.draw_display_var.get()
        picked = random.sample(list(self.table), n)
        self._show_draw_result(picked)

    def _show_draw_result(self, pairs):
        self.clear()
        self.unbind("<Return>")
        show_mots = getattr(self, "_draw_last_display", "nombre") == "mot"

        tk.Label(
            self.container, text="🎴 Résultat du tirage",
            font=FONT_TITLE, bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(28, 6))

        mode_lbl = (
            "Mots (ancres)" if show_mots
            else "Nombres (reconstruction mentale)"
        )
        tk.Label(
            self.container,
            text=f"{len(pairs)} entrée(s) · {mode_lbl}",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(0, 14))

        outer = tk.Frame(self.container, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=36, pady=(0, 8))

        canvas = tk.Canvas(outer, bg=BG_CARD, highlightthickness=1,
                           highlightbackground=BORDER_ACCENT)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_CARD)
        inner.bind(
            "<Configure>",
            lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._bind_mousewheel(canvas)

        for i, (nombre, mot) in enumerate(pairs, start=1):
            line = tk.Frame(inner, bg=BG_CARD)
            line.pack(fill="x", padx=14, pady=6)
            tk.Label(
                line, text=f"{i}.", font=FONT_BODY_BOLD,
                bg=BG_CARD, fg=FG_SECONDARY, width=3, anchor="e",
            ).pack(side="left", padx=(0, 8))
            txt = mot if show_mots else str(nombre)
            tk.Label(
                line, text=txt, font=FONT_BIG,
                bg=BG_CARD, fg=FG_GREEN if show_mots else FG_ACCENT,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=(16, 24))
        self.make_button(
            btn_frame, "🔄  Nouveau tirage (mêmes réglages)",
            self._do_draw_again, accent=True, width=32,
        ).pack(side="left", padx=8)
        self.make_button(
            btn_frame, "⚙️  Modifier les réglages…",
            self.show_draw_config, width=24,
        ).pack(side="left", padx=8)
        self.make_button(
            btn_frame, "⬅  Menu", self.show_main_menu, width=12,
        ).pack(side="left", padx=8)

    def _do_draw_again(self):
        n = str(getattr(self, "_draw_last_n", 5))
        disp = getattr(self, "_draw_last_display", "nombre")
        if not hasattr(self, "draw_n_var"):
            self.draw_n_var = tk.StringVar(value=n)
            self.draw_display_var = tk.StringVar(value=disp)
        else:
            self.draw_n_var.set(n)
            self.draw_display_var.set(disp)
        self._do_start_draw()

    # --------------------------------------------------------
    # Construction des questions et lancement
    # --------------------------------------------------------
    def _build_questions(
        self,
        pairs,
        shuffle_questions=True,
        *,
        use_flashcard=False,
        session_kind="bloc",
    ):
        sens = self.sens_var.get()
        if not shuffle_questions:
            pairs = _sort_table_pairs(list(pairs))
        self.questions = []
        for nombre, mot in pairs:
            if sens in ("1", "3"):
                self.questions.append(("nombre->mot", nombre, mot))
            if sens in ("2", "3"):
                self.questions.append(("mot->nombre", nombre, mot))
        if shuffle_questions:
            random.shuffle(self.questions)
        sk = session_kind if session_kind in _VALID_SESSION_KINDS else "bloc"
        self._session_kind = sk
        self._quiz_is_flashcard = use_flashcard
        self.current_q = 0
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.results = []
        self.quiz_start_time = time.time()
        if use_flashcard:
            self._launch_flashcard_from_questions()
            return
        self._show_question()

    # --------------------------------------------------------
    # Écran : Question du quiz
    # --------------------------------------------------------
    def _show_question(self):
        # Début du chrono question à l’affichage (exclut l’écran de feedback de la question précédente).
        self.question_start_time = time.time()
        self.clear()
        self.unbind("<Return>")

        mode, nombre, mot = self.questions[self.current_q]
        total = len(self.questions)
        idx = self.current_q + 1

        # -- Barre de progression & infos --
        top_bar = tk.Frame(self.container, bg=BG_DARK)
        top_bar.pack(fill="x", padx=40, pady=(18, 0))

        tk.Label(
            top_bar, text=f"Question {idx}/{total}",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(side="left")

        # Streak
        if self.streak >= 2:
            tk.Label(
                top_bar, text=f"🔥 {self.streak}",
                font=FONT_STREAK, bg=BG_DARK, fg=FG_ORANGE,
            ).pack(side="left", padx=15)

        if idx > 1:
            tk.Label(
                top_bar, text=f"Score : {self.score}/{idx - 1}",
                font=FONT_BODY, bg=BG_DARK, fg=FG_GREEN,
            ).pack(side="right", padx=(0, 12))

        self.session_timer_label = tk.Label(
            top_bar, text="⏳ Session : 0.0s",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_ORANGE,
        )
        self.session_timer_label.pack(side="right")

        # Progress bar
        bar = tk.Canvas(self.container, height=6, bg=BTN_BG,
                        highlightthickness=0)
        bar.pack(fill="x", padx=40, pady=(5, 0))
        self.after(50, lambda: self._draw_progress(bar, idx, total))

        # -- Zone question --
        q_frame = tk.Frame(self.container, bg=BG_DARK)
        q_frame.pack(expand=True, fill="both", padx=40)

        if mode == "nombre->mot":
            tk.Label(
                q_frame, text="Quel mot correspond au nombre…",
                font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(pady=(30, 8))
            tk.Label(
                q_frame, text=nombre, font=FONT_BIG,
                bg=BG_DARK, fg=FG_ACCENT,
            ).pack(pady=(0, 20))
        else:
            tk.Label(
                q_frame, text="Quel nombre correspond au mot…",
                font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(pady=(30, 8))
            tk.Label(
                q_frame, text=mot, font=FONT_BIG,
                bg=BG_DARK, fg=FG_GREEN,
            ).pack(pady=(0, 20))

        # Input
        self.answer_var = tk.StringVar()
        entry = tk.Entry(
            q_frame, textvariable=self.answer_var,
            font=FONT_INPUT, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY, relief="flat",
            justify="center", width=25,
        )
        entry.pack(ipady=8, pady=(0, 15))
        entry.focus_set()
        entry.bind("<Return>", lambda e: self._submit_answer())

        # Bouton valider
        self.make_button(
            q_frame, "Valider ↵", self._submit_answer, accent=True, width=20,
        ).pack()

        # Timer live
        self.timer_label = tk.Label(
            q_frame, text="⏱ 0.0s", font=FONT_SMALL,
            bg=BG_DARK, fg=FG_SECONDARY,
        )
        self.timer_label.pack(pady=(12, 0))
        self._update_quiz_timers()

    def _draw_progress(self, canvas, current, total):
        canvas.update_idletasks()
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if total <= 0 or w <= 0 or h <= 0:
            return
        fill_w = int(w * (current - 1) / total)
        if fill_w > 0:
            self._draw_rounded_rect(canvas, 0, 0, fill_w, h, FG_ACCENT, min(3, h // 2))

    def _update_quiz_timers(self):
        if hasattr(self, "timer_label") and self.timer_label.winfo_exists():
            elapsed_q = time.time() - self.question_start_time
            self.timer_label.configure(text=f"⏱ Question : {elapsed_q:.1f}s")
        if hasattr(self, "session_timer_label") and self.session_timer_label.winfo_exists():
            elapsed_s = time.time() - self.quiz_start_time
            self.session_timer_label.configure(
                text=f"⏳ Session : {elapsed_s:.1f}s",
            )
        if (
            hasattr(self, "timer_label") and self.timer_label.winfo_exists()
        ) or (
            hasattr(self, "session_timer_label")
            and self.session_timer_label.winfo_exists()
        ):
            self.after(100, self._update_quiz_timers)

    def _apply_answer_stats(self, mode, nombre, mot, correct, elapsed):
        """Met à jour les compteurs / temps moyen pour une paire (quiz ou flashcard)."""
        if mode == "nombre->mot":
            if correct:
                self.stats[(nombre, mot)][0] += 1
                nb_lettres = len(mot)
                if nb_lettres > 0:
                    tpl = elapsed / nb_lettres
                    ancien = self.stats[(nombre, mot)][2]
                    self.stats[(nombre, mot)][2] = (
                        tpl if ancien == 0 else (ancien + tpl) / 2
                    )
            else:
                self.stats[(nombre, mot)][0] -= 1
        else:
            if correct:
                self.stats[(nombre, mot)][1] += 1
                nb_ch = len(str(nombre))
                if nb_ch > 0:
                    tps = elapsed / nb_ch
                    ancien = self.stats[(nombre, mot)][3]
                    self.stats[(nombre, mot)][3] = (
                        tps if ancien == 0 else (ancien + tps) / 2
                    )
            else:
                self.stats[(nombre, mot)][1] -= 1
        save_stats(self.stats, self.table)

    def _submit_answer(self):
        answer = self.answer_var.get().strip().lower()
        if not answer:
            return

        mode, nombre, mot = self.questions[self.current_q]
        elapsed = time.time() - self.question_start_time

        if mode == "nombre->mot":
            correct = answer == mot.lower()
            expected = mot
        else:
            correct = answer == nombre
            expected = nombre

        self._apply_answer_stats(mode, nombre, mot, correct, elapsed)

        if correct:
            self.score += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
        else:
            self.streak = 0

        self.results.append((mode, nombre, mot, answer, correct, elapsed))

        self._show_feedback(correct, expected, elapsed)

    # --------------------------------------------------------
    # Écran : Feedback après réponse
    # --------------------------------------------------------
    def _show_feedback(self, correct, expected, elapsed):
        self.clear()
        mode, nombre, mot, answer, _, _ = self.results[-1]

        if correct:
            icon, msg, color = "✅", "Correct !", FG_GREEN
        else:
            icon, msg, color = "❌", "Mauvaise réponse", FG_RED

        tk.Label(
            self.container, text=icon, font=("Helvetica", 64),
            bg=BG_DARK, fg=color,
        ).pack(pady=(40, 0))
        tk.Label(
            self.container, text=msg, font=FONT_TITLE,
            bg=BG_DARK, fg=color,
        ).pack(pady=(0, 10))

        # Streak badge
        if correct and self.streak >= 3:
            tk.Label(
                self.container,
                text=f"🔥 Série de {self.streak} !",
                font=FONT_STREAK, bg=BG_DARK, fg=FG_ORANGE,
            ).pack()

        # Détails
        card = self.make_card(self.container)
        card.pack(padx=120, pady=(10, 0))

        if not correct:
            tk.Label(
                card, text=f"Ta réponse : {answer}", font=FONT_BODY,
                bg=BG_CARD, fg=FG_RED,
            ).pack(anchor="w", pady=2)
            tk.Label(
                card, text=f"Bonne réponse : {expected}",
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_GREEN,
            ).pack(anchor="w", pady=2)

        tk.Label(
            card, text=f"{nombre}  ↔  {mot}",
            font=FONT_QUESTION, bg=BG_CARD, fg=FG_ACCENT,
        ).pack(pady=(10, 5))
        tk.Label(
            card, text=f"⏱ {elapsed:.1f}s",
            font=FONT_BODY, bg=BG_CARD, fg=FG_SECONDARY,
        ).pack()

        weak_var = tk.BooleanVar(value=(nombre, mot) in self.manual_weak)
        tk.Checkbutton(
            card,
            text="🎯 Point faible (inclus au focus)",
            variable=weak_var,
            command=lambda p=(nombre, mot), v=weak_var: self._persist_weak_toggle(
                p, v.get(),
            ),
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
            selectcolor=CHECK_BG, activebackground=BG_CARD,
            activeforeground=FG_ORANGE, highlightthickness=0,
        ).pack(anchor="w", pady=(10, 0))

        # Progression
        idx = self.current_q + 1
        total = len(self.questions)
        tk.Label(
            self.container, text=f"{idx}/{total} — Score : {self.score}/{idx}",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(12, 0))

        # Navigation
        self.current_q += 1
        if self.current_q < total:
            btn_text = "Question suivante →"
            btn_cmd = self._show_question
        else:
            btn_text = "Voir les résultats 🏁"
            btn_cmd = self._show_results

        btn = self.make_button(
            self.container, btn_text, btn_cmd, accent=True, width=25,
        )
        btn.pack(pady=20)
        self.bind("<Return>", lambda e: btn_cmd())
        btn.focus_set()

        delay_ok = int(self.preferences.get(
            "auto_advance_correct_ms", DEFAULT_AUTO_ADVANCE_CORRECT_MS,
        ))
        delay_bad = int(self.preferences.get(
            "auto_advance_wrong_ms", DEFAULT_AUTO_ADVANCE_WRONG_MS,
        ))

        if correct and delay_ok > 0 and self.current_q < total:
            tk.Label(
                self.container, text="Suite automatique…",
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack()
            self._auto_advance_id = self.after(delay_ok, btn_cmd)
        elif (
            not correct
            and delay_bad > 0
        ):
            tk.Label(
                self.container, text="Suite automatique…",
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack()
            self._auto_advance_id = self.after(delay_bad, btn_cmd)

    # --------------------------------------------------------
    # Écran : Résultats du quiz
    # --------------------------------------------------------
    def _show_results(self):
        self.unbind("<Return>")
        self.clear()
        save_stats(self.stats, self.table)

        total_time = time.time() - self.quiz_start_time
        total_q = len(self.questions)
        pct = (self.score / total_q * 100) if total_q else 0

        if total_q > 0:
            err_count = sum(1 for r in self.results if not r[4])
            self._record_session_run(
                total_q=total_q,
                score=self.score,
                errors_count=err_count,
                duration_s=total_time,
                flashcard=False,
            )

        tk.Label(
            self.container, text="🏁 Résultats", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(25, 10))

        # Score principal
        score_color = (FG_GREEN if pct >= 80
                       else (FG_YELLOW if pct >= 50 else FG_RED))
        tk.Label(
            self.container, text=f"{self.score}/{total_q}",
            font=FONT_HUGE, bg=BG_DARK, fg=score_color,
        ).pack()
        tk.Label(
            self.container,
            text=f"{pct:.0f}%  ·  Meilleure série : {self.best_streak} 🔥",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(0, 6))
        tk.Label(
            self.container,
            text=f"⏳ Chronomètre total de la série : {total_time:.1f}s",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_ORANGE,
        ).pack(pady=(0, 15))

        # Temps moyen par question
        if total_q > 0:
            avg_time = total_time / total_q
            tk.Label(
                self.container,
                text=f"⏱ Temps moyen : {avg_time:.1f}s / question",
                font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(pady=(0, 10))

        # Erreurs
        errors = [r for r in self.results if not r[4]]
        if errors:
            err_card = self.make_card(self.container)
            err_card.pack(padx=60, fill="x", pady=(0, 8))

            tk.Label(
                err_card, text=f"❌ {len(errors)} erreur(s) à revoir :",
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_RED,
            ).pack(anchor="w", pady=(0, 8))

            list_frame = tk.Frame(err_card, bg=BG_CARD)
            list_frame.pack(fill="x")

            for mode, nombre, mot, answer, _, t in errors[:15]:
                direction = "→" if mode == "nombre->mot" else "←"
                line = (f"  {nombre} {direction} {mot}  "
                        f"(ta réponse : {answer}, {t:.1f}s)")
                tk.Label(
                    list_frame, text=line, font=FONT_SMALL,
                    bg=BG_CARD, fg=FG_SECONDARY, anchor="w",
                ).pack(anchor="w")
            if len(errors) > 15:
                tk.Label(
                    list_frame,
                    text=f"  … et {len(errors) - 15} autre(s)",
                    font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
                ).pack(anchor="w")
        else:
            tk.Label(
                self.container, text="🎉 Aucune erreur ! Parfait !",
                font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_GREEN,
            ).pack(pady=10)

        # Boutons
        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=15)
        self.make_button(
            btn_frame, "🔄  Recommencer", self.show_main_menu, accent=True,
        ).pack(side="left", padx=10)

        # Relancer uniquement les erreurs
        if errors:
            self.make_button(
                btn_frame, "🎯  Re-quiz erreurs",
                lambda: self._requiz_errors(errors), width=20,
            ).pack(side="left", padx=10)

        self.make_button(
            btn_frame, "🚪  Quitter", self._on_quit,
        ).pack(side="left", padx=10)

    def _requiz_errors(self, errors):
        """Relance un quiz uniquement sur les erreurs."""
        self._session_kind = "errors_review"
        self.questions = [
            (mode, nombre, mot) for mode, nombre, mot, _, _, _ in errors
        ]
        random.shuffle(self.questions)
        self.current_q = 0
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.results = []
        self.quiz_start_time = time.time()
        if getattr(self, "_quiz_is_flashcard", False):
            self._launch_flashcard_from_questions()
        else:
            self._show_question()

