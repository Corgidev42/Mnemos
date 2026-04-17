"""Dessin canvas (barre de maîtrise, etc.)."""
from mnemos.ui._quiz_shared import *  # noqa: F403, F401


class DrawingMixin:
    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, fill, r=4):
        """Dessine un rectangle aux coins arrondis."""
        if x2 <= x1 or y2 <= y1:
            return
        r = min(r, (x2 - x1) // 2, (y2 - y1) // 2)
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="")
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="")
        canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=fill, outline="")
        canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=fill, outline="")
        canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=fill, outline="")
        canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=fill, outline="")

    def _draw_mastery_bar(self, canvas, total, ok, en_cours, revoir, non_vus):
        """Dessine une barre de progression colorée aux coins arrondis."""
        canvas.update_idletasks()
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if total == 0 or w <= 0 or h <= 0:
            return
        r = min(4, h // 2)
        segments = [
            (ok, FG_GREEN), (en_cours, FG_YELLOW),
            (revoir, FG_RED), (non_vus, BTN_BG),
        ]
        x = 0
        for count, color in segments:
            seg_w = max(0, int(w * count / total))
            if seg_w > 0:
                self._draw_rounded_rect(canvas, x, 0, x + seg_w, h, color, r)
            x += seg_w

