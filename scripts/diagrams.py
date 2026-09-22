"""Every course diagram, drawn in one style: a light panel per idea, icons, labelled arrows.

    uv run --extra projects python scripts/diagrams.py

Each diagram is our own drawing of the course's own parts. Re-run after changing a
number the pictures quote; the numbers are written here, next to where they came from.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (
    Circle,
    Ellipse,
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
    Rectangle,
    Wedge,
)

ROOT = Path(__file__).resolve().parents[1]
INK, DIM, LINE, PAGE, PANEL = "#1f2937", "#5b6472", "#c9ced6", "#ffffff", "#fbfcfd"
BLUE, GREEN, BROWN, PURPLE, RED = "#2f5f9e", "#2f7a4f", "#8c5a24", "#5a4696", "#c2413b"
TINT = {BLUE: "#e8eef8", GREEN: "#e6f2ea", BROWN: "#f7ede0", PURPLE: "#ece8f6", RED: "#fbe9e8"}


class Canvas:
    def __init__(self, width: float, height: float) -> None:
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=180)
        self.fig.patch.set_facecolor(PAGE)
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.set_aspect("equal")
        self.ax.axis("off")

    # ------------------------------------------------------------- layout
    def title(self, x: float, y: float, text: str, sub: str = "") -> None:
        self.ax.add_patch(Rectangle((x, y - 0.32), 0.12, 0.64, color=GREEN))
        self.ax.text(x + 0.35, y, text, fontsize=24, fontweight="bold", color=INK, va="center")
        if sub:
            self.ax.text(x + 0.35, y - 0.62, sub, fontsize=11.5, color=DIM, va="center")

    def row(self, y: float, h: float, label: str, color: str, where: str, x0=0.4, x1=None) -> None:
        x1 = x1 or self.ax.get_xlim()[1] - 0.4
        self.ax.add_patch(
            FancyBboxPatch(
                (x0, y),
                x1 - x0,
                h,
                boxstyle="round,pad=0,rounding_size=0.25",
                facecolor=PANEL,
                edgecolor=LINE,
                linewidth=1.4,
            )
        )
        self.ax.add_patch(
            FancyBboxPatch(
                (x0 + 0.18, y + 0.18),
                1.7,
                h - 0.36,
                boxstyle="round,pad=0,rounding_size=0.18",
                facecolor=color,
                edgecolor=color,
            )
        )
        self.ax.text(
            x0 + 1.03,
            y + h / 2,
            label,
            fontsize=17,
            fontweight="bold",
            color="white",
            ha="center",
            va="center",
            linespacing=1.15,
        )
        self.ax.text(
            x1 - 0.2,
            y + h - 0.25,
            where,
            fontsize=9.5,
            color=color,
            ha="right",
            va="top",
            fontweight="bold",
        )

    def box(self, x, y, w, h, color, dashed=False, fill=True):
        self.ax.add_patch(
            FancyBboxPatch(
                (x - w / 2, y - h / 2),
                w,
                h,
                boxstyle="round,pad=0,rounding_size=0.14",
                facecolor=TINT[color] if fill else "none",
                edgecolor=color,
                linewidth=1.5,
                linestyle=(0, (4, 3)) if dashed else "-",
            )
        )

    def label(self, x, y, text, size=11.5, color=INK, bold=True, va="top"):
        self.ax.text(
            x,
            y,
            text,
            fontsize=size,
            color=color,
            ha="center",
            va=va,
            fontweight="bold" if bold else "normal",
            linespacing=1.2,
        )

    def note(self, x, y, text, color=DIM, size=9.2, ha="center"):
        self.ax.text(
            x,
            y,
            text,
            fontsize=size,
            color=color,
            ha=ha,
            va="top",
            linespacing=1.25,
            style="italic",
        )

    def arrow(self, p1, p2, text="", color=DIM, rad=0.0, dy=0.14, dx=0.0, solid=False):
        self.ax.add_patch(
            FancyArrowPatch(
                p1,
                p2,
                arrowstyle="-|>",
                mutation_scale=13,
                linewidth=1.3,
                color=color,
                linestyle="-" if solid else (0, (4, 3)),
                connectionstyle=f"arc3,rad={rad}",
                zorder=2,
            )
        )
        if text:
            self.ax.text(
                (p1[0] + p2[0]) / 2 + dx,
                (p1[1] + p2[1]) / 2 + dy,
                text,
                fontsize=9.2,
                color=DIM,
                ha="center",
                va="bottom",
                linespacing=1.15,
            )

    def path(self, points, text="", color=DIM, text_at=None):
        xs, ys = zip(*points, strict=True)
        self.ax.plot(xs[:-1], ys[:-1], color=color, linewidth=1.3, linestyle=(0, (4, 3)), zorder=2)
        self.arrow(points[-2], points[-1], color=color)
        if text and text_at:
            self.ax.text(*text_at, text, fontsize=9.2, color=DIM, ha="center", va="bottom")

    def save(self, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(target, facecolor=PAGE, bbox_inches="tight", pad_inches=0.15)
        plt.close(self.fig)
        print(f"wrote {target.relative_to(ROOT)}")

    def badge(self, x, y, text):
        self.ax.add_patch(
            Circle((x, y), 0.26, facecolor="#f5c518", edgecolor=INK, linewidth=1.2, zorder=6)
        )
        self.ax.text(
            x,
            y,
            text,
            fontsize=8.5,
            fontweight="bold",
            color=INK,
            ha="center",
            va="center",
            zorder=7,
        )

    def node(
        self,
        x,
        y,
        icon,
        color,
        name,
        note="",
        w=2.1,
        h=1.75,
        badge=None,
        dashed=False,
        filled=False,
    ):
        """A tinted card: an icon, a bold name, and an italic line under the card."""
        self.box(x, y, w, h, color, dashed=dashed)
        if filled:
            self.ax.add_patch(
                FancyBboxPatch(
                    (x - w / 2, y - h / 2),
                    w,
                    h,
                    boxstyle="round,pad=0,rounding_size=0.14",
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.18,
                    zorder=1,
                )
            )
        getattr(self, icon)(x, y + 0.25, color, s=0.62)
        self.label(x, y - 0.33, name, size=10.5)
        if note:
            self.note(x, y - h / 2 - 0.12, note)
        if badge:
            self.badge(x + w / 2 - 0.05, y + h / 2 - 0.05, badge)

    # -------------------------------------------------------------- icons
    def bubbles(self, x, y, c, s=0.55):
        for dx, dy, fc in ((0.18, 0.14, TINT[c]), (-0.12, -0.1, PAGE)):
            self.ax.add_patch(
                FancyBboxPatch(
                    (x + dx * s - 0.5 * s, y + dy * s - 0.34 * s),
                    s,
                    0.68 * s,
                    boxstyle=f"round,pad=0,rounding_size={0.12 * s}",
                    facecolor=fc,
                    edgecolor=INK,
                    linewidth=1.4,
                    zorder=3,
                )
            )
        self.ax.add_patch(
            Polygon(
                [
                    (x - 0.42 * s, y - 0.4 * s),
                    (x - 0.42 * s, y - 0.62 * s),
                    (x - 0.22 * s, y - 0.44 * s),
                ],
                closed=True,
                facecolor=PAGE,
                edgecolor=INK,
                linewidth=1.4,
                zorder=3,
            )
        )
        for dx in (-0.25, -0.1, 0.05):
            self.ax.add_patch(Circle((x + dx * s, y - 0.1 * s), 0.035 * s, color=INK, zorder=4))

    def chip(self, x, y, c, s=0.6):
        for i in (-0.25, 0, 0.25):
            for ax_, ay_, bx, by in (
                (i, 0.36, i, 0.5),
                (i, -0.36, i, -0.5),
                (0.36, i, 0.5, i),
                (-0.36, i, -0.5, i),
            ):
                self.ax.plot(
                    [x + ax_ * s, x + bx * s],
                    [y + ay_ * s, y + by * s],
                    color=INK,
                    linewidth=1.4,
                    zorder=3,
                )
        self.ax.add_patch(
            FancyBboxPatch(
                (x - 0.36 * s, y - 0.36 * s),
                0.72 * s,
                0.72 * s,
                boxstyle=f"round,pad=0,rounding_size={0.06 * s}",
                facecolor=TINT[c],
                edgecolor=INK,
                linewidth=1.5,
                zorder=4,
            )
        )
        self.ax.add_patch(
            Rectangle(
                (x - 0.17 * s, y - 0.17 * s),
                0.34 * s,
                0.34 * s,
                facecolor=c,
                edgecolor=INK,
                linewidth=1.2,
                zorder=5,
            )
        )

    def magnifier(self, x, y, c, s=0.6):
        self.ax.plot(
            [x + 0.12 * s, x + 0.42 * s],
            [y - 0.12 * s, y - 0.42 * s],
            color=INK,
            linewidth=4,
            zorder=3,
            solid_capstyle="round",
        )
        self.ax.add_patch(
            Circle(
                (x - 0.08 * s, y + 0.08 * s),
                0.28 * s,
                facecolor=TINT[c],
                edgecolor=INK,
                linewidth=1.8,
                zorder=4,
            )
        )
        self.ax.text(
            x - 0.08 * s,
            y + 0.07 * s,
            "?",
            fontsize=15 * s,
            fontweight="bold",
            color=c,
            ha="center",
            va="center",
            zorder=5,
        )

    def cylinder(self, x, y, c, s=0.6):
        w, h = 0.8 * s, 0.7 * s
        self.ax.add_patch(
            Rectangle((x - w / 2, y - h / 2), w, h, facecolor=TINT[c], edgecolor="none", zorder=3)
        )
        self.ax.plot([x - w / 2] * 2, [y - h / 2, y + h / 2], color=INK, linewidth=1.5, zorder=4)
        self.ax.plot([x + w / 2] * 2, [y - h / 2, y + h / 2], color=INK, linewidth=1.5, zorder=4)
        for yy in (y - h / 2, y, y + h / 2):
            self.ax.add_patch(
                Ellipse(
                    (x, yy),
                    w,
                    0.26 * s,
                    facecolor=TINT[c] if yy < y + h / 2 else c,
                    edgecolor=INK,
                    linewidth=1.5,
                    zorder=4,
                )
            )

    def document(self, x, y, c, s=0.6, lines=4):
        w, h = 0.62 * s, 0.8 * s
        self.ax.add_patch(
            Polygon(
                [
                    (x - w / 2, y - h / 2),
                    (x + w / 2, y - h / 2),
                    (x + w / 2, y + h / 2 - 0.18 * s),
                    (x + w / 2 - 0.18 * s, y + h / 2),
                    (x - w / 2, y + h / 2),
                ],
                closed=True,
                facecolor=PAGE,
                edgecolor=INK,
                linewidth=1.4,
                zorder=3,
            )
        )
        for i in range(lines):
            yy = y + h / 2 - 0.25 * s - i * 0.14 * s
            self.ax.plot(
                [x - w / 2 + 0.1 * s, x + w / 2 - 0.12 * s],
                [yy, yy],
                color=c,
                linewidth=1.6,
                zorder=4,
            )

    def target(self, x, y, c, s=0.6):
        for r, fc in ((0.42, PAGE), (0.3, TINT[c]), (0.18, PAGE), (0.08, c)):
            self.ax.add_patch(
                Circle((x, y), r * s, facecolor=fc, edgecolor=INK, linewidth=1.3, zorder=3)
            )
        self.ax.annotate(
            "",
            xy=(x + 0.02 * s, y + 0.02 * s),
            xytext=(x + 0.5 * s, y + 0.5 * s),
            zorder=5,
            arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.8),
        )

    def checklist(self, x, y, c, s=0.6):
        w, h = 0.66 * s, 0.86 * s
        self.ax.add_patch(
            FancyBboxPatch(
                (x - w / 2, y - h / 2),
                w,
                h,
                boxstyle=f"round,pad=0,rounding_size={0.05 * s}",
                facecolor=PAGE,
                edgecolor=INK,
                linewidth=1.4,
                zorder=3,
            )
        )
        self.ax.add_patch(
            Rectangle(
                (x - 0.14 * s, y + h / 2 - 0.06 * s),
                0.28 * s,
                0.13 * s,
                facecolor=c,
                edgecolor=INK,
                linewidth=1.1,
                zorder=4,
            )
        )
        for i in range(3):
            yy = y + 0.2 * s - i * 0.22 * s
            self.ax.plot(
                [x - 0.22 * s, x - 0.16 * s, x - 0.08 * s],
                [yy, yy - 0.06 * s, yy + 0.06 * s],
                color=c,
                linewidth=1.8,
                zorder=4,
            )
            self.ax.plot([x - 0.02 * s, x + 0.22 * s], [yy, yy], color=INK, linewidth=1.3, zorder=4)

    def gear(self, x, y, c, s=0.6):
        for k in range(8):
            self.ax.add_patch(
                Wedge((x, y), 0.42 * s, k * 45 - 12, k * 45 + 12, facecolor=INK, zorder=3)
            )
        self.ax.add_patch(
            Circle((x, y), 0.32 * s, facecolor=TINT[c], edgecolor=INK, linewidth=1.5, zorder=4)
        )
        self.ax.add_patch(
            Circle((x, y), 0.12 * s, facecolor=PAGE, edgecolor=INK, linewidth=1.3, zorder=5)
        )

    def layers(self, x, y, c, s=0.6):
        for i, fc in enumerate((TINT[c], c, TINT[c])):
            yy = y - 0.2 * s + i * 0.2 * s
            self.ax.add_patch(
                Polygon(
                    [
                        (x - 0.42 * s, yy),
                        (x, yy + 0.16 * s),
                        (x + 0.42 * s, yy),
                        (x, yy - 0.16 * s),
                    ],
                    closed=True,
                    facecolor=fc,
                    edgecolor=INK,
                    linewidth=1.3,
                    zorder=3 + i,
                )
            )

    def flag(self, x, y, c, s=0.6):
        self.ax.plot(
            [x - 0.25 * s, x - 0.25 * s],
            [y - 0.45 * s, y + 0.45 * s],
            color=INK,
            linewidth=2,
            zorder=3,
        )
        self.ax.add_patch(
            Polygon(
                [
                    (x - 0.25 * s, y + 0.45 * s),
                    (x + 0.4 * s, y + 0.3 * s),
                    (x - 0.25 * s, y + 0.05 * s),
                ],
                closed=True,
                facecolor=c,
                edgecolor=INK,
                linewidth=1.3,
                zorder=4,
            )
        )
        self.ax.add_patch(
            Ellipse(
                (x - 0.25 * s, y - 0.45 * s),
                0.4 * s,
                0.1 * s,
                facecolor=TINT[c],
                edgecolor=INK,
                linewidth=1.2,
                zorder=3,
            )
        )

    def hub(self, x, y, c, s=0.6):
        import math

        for k in range(5):
            a = math.radians(90 + k * 72)
            px, py = x + 0.42 * s * math.cos(a), y + 0.42 * s * math.sin(a)
            self.ax.plot([x, px], [y, py], color=INK, linewidth=1.4, zorder=3)
            self.ax.add_patch(
                Circle(
                    (px, py), 0.09 * s, facecolor=TINT[c], edgecolor=INK, linewidth=1.2, zorder=4
                )
            )
        self.ax.add_patch(
            Circle((x, y), 0.16 * s, facecolor=c, edgecolor=INK, linewidth=1.3, zorder=5)
        )

    def shield(self, x, y, c, s=0.6):
        self.ax.add_patch(
            Polygon(
                [
                    (x, y + 0.45 * s),
                    (x + 0.36 * s, y + 0.3 * s),
                    (x + 0.32 * s, y - 0.12 * s),
                    (x, y - 0.45 * s),
                    (x - 0.32 * s, y - 0.12 * s),
                    (x - 0.36 * s, y + 0.3 * s),
                ],
                closed=True,
                facecolor=TINT[c],
                edgecolor=INK,
                linewidth=1.5,
                zorder=3,
            )
        )
        self.ax.plot(
            [x - 0.14 * s, x + 0.14 * s],
            [y + 0.02 * s, y + 0.02 * s],
            color=c,
            linewidth=3,
            zorder=4,
        )

    def tools(self, x, y, c, names, w=4.0, h=1.25, title="Read-only tools"):
        self.box(x, y, w, h, c)
        self.label(x, y + h / 2 - 0.1, title, size=10.5)
        step = w / (len(names) + 1)
        for i, name in enumerate(names):
            px = x - w / 2 + step * (i + 1)
            self.document(px, y + 0.02, c, s=0.42, lines=3)
            self.ax.text(
                px,
                y - h / 2 + 0.1,
                name,
                fontsize=8.2,
                color=INK,
                ha="center",
                va="bottom",
                family="monospace",
            )


# =================================================================== diagrams


def model_rag_agent_team() -> None:
    """Four rows, each adding one thing to the row above, each with its session."""
    c = Canvas(18, 23)
    c.title(
        0.4,
        22.35,
        "Model, RAG, agent, agent team",
        "What each one adds to the row above it, and where this course teaches it",
    )

    # ---- 1. a model call (session 2)
    y, h = 17.55, 3.7
    c.row(y, h, "A model\ncall", BLUE, "SESSION 2 · PROJECT 02 STEP 1")
    m = y + h / 2 - 0.1
    c.bubbles(4.2, m + 0.25, BLUE, s=0.9)
    c.label(4.2, m - 0.45, "Prompt +\nyour context")
    c.box(9.4, m + 0.15, 2.3, 1.8, BLUE)
    c.chip(9.4, m + 0.35, BLUE, s=0.8)
    c.label(9.4, m - 0.25, "Model", size=11)
    c.note(9.4, m - 0.95, "behind the LLMClient seam")
    c.bubbles(15.0, m + 0.25, BLUE, s=0.9)
    c.label(15.0, m - 0.45, "Reply")
    c.note(15.0, m - 1.0, "fluent, from memory,\nwith nothing to check it against")
    c.arrow((5.25, m + 0.25), (8.2, m + 0.25), "system + user messages")
    c.arrow((10.6, m + 0.25), (13.9, m + 0.25), "one reply, word by word")

    # ---- 2. RAG (sessions 6, 7)
    y, h = 11.95, 5.2
    c.row(y, h, "RAG", GREEN, "SESSIONS 6 AND 7 · PROJECT 02 · THE CAPSTONE")
    m = y + h - 1.55
    c.magnifier(3.6, m + 0.2, GREEN, s=0.9)
    c.label(3.6, m - 0.45, "Question")
    c.box(7.3, m + 0.1, 2.4, 1.7, GREEN)
    c.magnifier(6.95, m + 0.35, GREEN, s=0.6)
    c.document(7.7, m + 0.35, GREEN, s=0.62)
    c.label(7.3, m - 0.3, "Retriever", size=11)
    c.box(7.3, y + 1.0, 2.9, 1.25, GREEN)
    c.cylinder(6.3, y + 1.0, GREEN, s=0.62)
    c.label(7.75, y + 1.35, "Index", size=11)
    c.note(7.75, y + 1.02, "chunks, each\nwith its id")
    c.box(11.8, m + 0.1, 2.3, 1.7, GREEN)
    c.chip(11.8, m + 0.3, GREEN, s=0.8)
    c.label(11.8, m - 0.3, "Model", size=11)
    c.bubbles(15.6, m + 0.3, GREEN, s=0.85)
    c.document(16.25, m + 0.05, GREEN, s=0.5, lines=3)
    c.label(15.7, m - 0.45, "Cited answer")
    c.note(15.7, m - 1.05, "grounded, and still not\nguaranteed correct: measure it")
    c.arrow((4.6, m + 0.2), (6.1, m + 0.2), "question")
    c.arrow((6.9, m - 0.75), (6.9, y + 1.62), "search", dx=-0.45, dy=-0.1)
    c.arrow((7.7, y + 1.62), (7.7, m - 0.75), "top k", dx=0.45, dy=-0.1)
    c.arrow((8.5, m + 0.2), (10.65, m + 0.2), "question +\npassages + ids")
    c.arrow((12.95, m + 0.2), (14.7, m + 0.2), "JSON")
    c.shield(11.8, y + 1.05, RED, s=0.75)
    c.label(12.6, y + 1.45, "Refuse", size=11, color=RED)
    c.ax.text(
        12.35,
        y + 1.05,
        "nothing retrieved:\nthe model is never called",
        fontsize=9.2,
        color=DIM,
        va="top",
        ha="left",
        style="italic",
    )
    c.arrow(
        (8.5, m - 0.45), (11.3, y + 1.35), "nothing found", color=RED, rad=0.12, dx=0.5, dy=-0.05
    )

    # ---- 3. an agent (sessions 4, 5)
    y, h = 5.75, 5.85
    c.row(y, h, "An\nagent", BROWN, "SESSIONS 4 AND 5 · THE BOUNDED LOOP")
    m = y + h - 2.25
    c.target(3.4, m, BROWN, s=0.9)
    c.label(3.4, m - 0.7, "Question\nor goal")
    c.box(7.1, m, 3.7, 2.3, BROWN)
    c.label(7.1, m + 1.0, "The loop", size=11.5)
    c.chip(6.0, m + 0.15, BROWN, s=0.6)
    c.label(6.0, m - 0.35, "Model", size=9.5)
    c.checklist(7.2, m + 0.15, BROWN, s=0.6)
    c.label(7.2, m - 0.35, "Rules", size=9.5)
    c.layers(8.35, m + 0.15, BROWN, s=0.6)
    c.label(8.35, m - 0.35, "State", size=9.5)
    c.note(7.1, m - 0.72, "budget: 3 tool calls")
    c.checklist(11.3, m, BROWN, s=0.8)
    c.label(11.3, m - 0.6, "Decide")
    c.flag(15.6, m + 0.2, BROWN, s=0.85)
    c.label(15.6, m - 0.45, "Stop, with a receipt")
    c.note(15.6, m - 0.95, "answered · budget ·\nrepeated_call · tool_error")
    c.gear(11.3, y + 1.25, BROWN, s=0.8)
    c.label(11.3, y + 0.55, "Act", size=11)
    c.tools(
        15.0,
        y + 1.25,
        BROWN,
        ["search_\ndocuments", "get_document_\nmetadata", "summarize_\ndocument"],
        w=4.8,
        h=1.55,
    )
    c.arrow((4.1, m), (5.25, m), "question")
    c.arrow((8.95, m), (10.75, m), "state")
    c.arrow((11.85, m + 0.2), (14.95, m + 0.2), "done, or a limit hit")
    c.arrow((11.3, m - 1.0), (11.3, y + 1.75), "pick a tool", dx=0.7, dy=-0.1)
    c.arrow((11.85, y + 1.25), (12.55, y + 1.25), "call")
    c.path(
        [(14.0, y + 2.03), (14.0, y + 2.5), (7.1, y + 2.5), (7.1, m - 1.15)],
        "the result goes into the state, and round again",
        text_at=(9.0, y + 2.02),
    )

    # ---- 4. an agent team, as a graph (session 8)
    y, h = 0.2, 5.2
    c.row(y, h, "Agents\nin a\ngraph", PURPLE, "SESSION 8 · LOOPS AND GRAPHS")
    m = y + h - 1.9
    c.ax.add_patch(
        FancyBboxPatch(
            (4.9, y + 0.35),
            9.2,
            h - 0.8,
            boxstyle="round,pad=0,rounding_size=0.2",
            facecolor="none",
            edgecolor=PURPLE,
            linewidth=1.3,
            linestyle=(0, (4, 3)),
        )
    )
    c.ax.text(
        9.5,
        y + h - 0.3,
        "ONE GRAPH: declared states, declared edges",
        fontsize=9.5,
        color=PURPLE,
        fontweight="bold",
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=TINT[PURPLE], edgecolor=PURPLE),
    )
    c.flag(3.3, m, PURPLE, s=0.85)
    c.label(3.3, m - 0.65, "Question")
    roles = [
        ("router", "picks the path"),
        ("retriever", "finds passages"),
        ("answerer", "writes, cites"),
        ("critic", "checks, once"),
    ]
    for i, (name, what) in enumerate(roles):
        px = 6.1 + i * 2.2
        c.box(px, m, 1.8, 1.5, PURPLE)
        c.chip(px, m + 0.25, PURPLE, s=0.5)
        c.ax.text(
            px,
            m - 0.2,
            name,
            fontsize=10,
            fontweight="bold",
            color=INK,
            ha="center",
            va="center",
            family="monospace",
        )
        c.note(px, m - 0.42, what, size=8.5)
        if i:
            c.arrow((px - 1.3, m), (px - 0.9, m))
    c.arrow((3.9, m), (5.2, m), "")
    c.layers(9.4, y + 1.0, PURPLE, s=0.7)
    c.label(10.45, y + 1.35, "Shared state", size=10.5)
    c.note(10.45, y + 1.02, "one typed dict,\nevery node reads it")
    c.arrow((12.7, m - 0.75), (10.1, y + 1.35), "writes", rad=-0.15, dy=-0.05)
    c.arrow((8.8, y + 1.35), (6.1, m - 0.75), "reads", rad=-0.15, dy=-0.05)
    c.flag(15.9, m, PURPLE, s=0.85)
    c.label(15.9, m - 0.65, "Answer, or a refusal")
    c.note(15.9, m - 1.15, "more calls, more ways\nto fail: count them")
    c.arrow((13.6, m), (15.3, m), "approved", dx=0.15)

    c.ax.text(
        0.45,
        -0.25,
        "Each row adds one thing: context, then a loop, then a graph of roles. Each also adds a "
        "way to fail and a number to measure.",
        fontsize=10.5,
        color=DIM,
        va="top",
    )
    c.save(ROOT / "units/en/unit2/session-08-loops-and-graphs/img/model-rag-agent-team.png")


def project_02() -> None:
    """Project 02: prepare once, answer per question, measure. Numbers from its run."""
    c = Canvas(19, 16.5)
    c.title(
        0.4,
        15.85,
        "Project 02: RAG on eight annual reports",
        "Prepare once, answer every question, measure both ways. "
        "Every number is printed by the notebook.",
    )

    y, h = 10.9, 4.0
    c.row(y, h, "Prepare,\nonce", BLUE, "STEPS 2 TO 6 · ONCE PER SET OF FILINGS")
    m = y + h / 2 + 0.05
    xs = [3.4, 6.0, 8.6, 11.2, 13.8, 16.6]
    cards = [
        ("document", "Raw filings", "8 files, 1.2 MB of HTML", None),
        ("checklist", "Clean", "a parser for tags,\nregex for page furniture", "e1"),
        ("layers", "Load", "8 Documents,\none per company", None),
        ("document", "Chunk", "1,401 chunks of at most\n800 characters, 0 words lost", "e2"),
        ("chip", "Embed", "nomic-embed-text,\n768 numbers each", None),
        ("cylinder", "Store", "ChromaDB: id, vector,\ntext, company", "e3"),
    ]
    for x, (icon, name, note, badge) in zip(xs, cards, strict=True):
        c.node(x, m, icon, BLUE, name, note, badge=badge)
    for a, b in zip(xs, xs[1:], strict=False):
        c.arrow((a + 1.05, m), (b - 1.05, m))

    y, h = 4.9, 5.55
    c.row(y, h, "Answer,\nper\nquestion", GREEN, "")
    c.ax.text(
        18.4,
        y + 0.3,
        "STEPS 7 AND 8 · ONE MODEL CALL AT MOST",
        fontsize=9.5,
        color=GREEN,
        ha="right",
        va="bottom",
        fontweight="bold",
    )
    m = y + h - 1.75
    xs = [3.4, 5.95, 8.5, 11.05, 13.6, 16.3]
    cards = [
        ("magnifier", "Question", "as the analyst typed it"),
        ("cylinder", "Nearest 4", "the question embedded,\ncosine search"),
        ("shield", "Floor 0.58", "keep hits at or above it"),
        ("document", "Prompt", "rules + JSON shape;\n4 passages, each with its id"),
        ("chip", "Model", "qwen2.5:7b-instruct,\none chat call"),
        ("bubbles", "Cited answer", "parsed; citations kept only\nif retrieval returned them"),
    ]
    for x, (icon, name, note) in zip(xs, cards, strict=True):
        c.node(x, m, icon, GREEN, name, note, filled=name == "Model")
    for a, b in zip(xs, xs[1:], strict=False):
        c.arrow((a + 1.05, m), (b - 1.05, m))
    c.node(8.5, y + 0.95, "shield", RED, "Refuse", w=2.2, h=1.35)
    c.ax.text(
        9.8,
        y + 1.3,
        "nothing above the floor, so the model\nis never called. "
        "Nonsense scored 0.51\nor less here; "
        "real questions 0.64 or more.",
        fontsize=9.2,
        color=DIM,
        va="top",
        style="italic",
    )
    c.arrow((8.5, m - 1.45), (8.5, y + 1.65), "no hits", color=RED, dx=0.45, dy=-0.1)
    c.path([(17.55, 12.05), (17.55, 9.9), (5.95, 9.9), (5.95, m + 0.9)])
    c.ax.text(
        11.0,
        9.93,
        "the stored vectors, texts and metadata: every question searches them",
        fontsize=9.2,
        color=DIM,
        ha="center",
        va="bottom",
    )

    y, h = 0.2, 4.35
    c.row(y, h, "Measure", PURPLE, "STEP 9 · 20 LABELLED QUESTIONS")
    m = y + h / 2 + 0.05
    c.node(3.6, m, "checklist", PURPLE, "20 questions", "10 in the filing's words,\n10 paraphrased")
    c.node(7.3, m + 0.55, "magnifier", PURPLE, "Keyword", w=2.0, h=1.4)
    c.node(7.3, m - 1.05, "chip", PURPLE, "Embeddings", w=2.0, h=1.4)
    c.arrow((4.7, m + 0.1), (6.25, m + 0.55))
    c.arrow((4.7, m - 0.1), (6.25, m - 1.05))
    c.box(12.4, m - 0.2, 6.2, 2.6, PURPLE)
    c.badge(15.45, m + 1.05, "e4")
    c.label(12.4, m + 0.85, "Right company in the top 3", size=10.5)
    rows = [
        ("", "own words", "paraphrased"),
        ("keyword", "10 / 10", "7 / 10"),
        ("embeddings", "10 / 10", "10 / 10"),
    ]
    for i, (a, b, d) in enumerate(rows):
        yy = m + 0.3 - i * 0.55
        weight = "bold" if i == 0 else "normal"
        for xx, t in ((10.4, a), (12.6, b), (14.5, d)):
            c.ax.text(
                xx,
                yy,
                t,
                fontsize=10.5,
                color=INK,
                ha="center",
                va="center",
                fontweight=weight,
                family="monospace" if i else None,
            )
    c.arrow((8.35, m + 0.55), (9.25, m + 0.15))
    c.arrow((8.35, m - 1.05), (9.25, m - 0.55))
    c.note(12.4, m - 1.6, "embeddings buy back the paraphrases. The table is how you know.")
    c.save(ROOT / "projects/02-sec-filings/img/architecture.png")


def capstone() -> None:
    """The capstone: one path, four exits, and the evidence each run leaves."""
    c = Canvas(19, 16.8)
    c.title(
        0.4,
        16.15,
        "The capstone: a research assistant that cites or refuses",
        "One path with one model call, four ways out that are not a crash, "
        "and what every run leaves behind",
    )

    y, h = 11.0, 4.25
    c.row(y, h, "One\nquestion", GREEN, "THE REFERENCE PIPELINE · SESSIONS 2 TO 6")
    m = y + h / 2 + 0.05
    xs = [3.35 + 2.3 * i for i in range(7)]
    cards = [
        ("magnifier", "Question", "one at a time", None),
        ("cylinder", "Retrieve", "lexical, top k,\nover 6 documents", None),
        ("document", "Prompt", "rules + JSON shape;\npassages are data", None),
        ("chip", "Model", "behind the\nLLMClient seam", None),
        ("checklist", "Parse", "strict; one\ncorrective retry", None),
        ("shield", "Verify", "keep only cited ids\nretrieval returned", "e1"),
        ("bubbles", "AgentResult", "answer + trace,\none shape always", None),
    ]
    for x, (icon, name, note, badge) in zip(xs, cards, strict=True):
        c.node(x, m, icon, GREEN, name, note, w=1.95, badge=badge, filled=name == "Model")
    for a, b in zip(xs, xs[1:], strict=False):
        c.arrow((a + 0.98, m), (b - 0.98, m))

    y, h = 5.55, 5.0
    c.row(y, h, "Four\nexits", RED, "")
    m = y + h / 2 + 0.25
    exits = [
        (
            4.4,
            xs[1],
            "Nothing retrieved",
            "refuse before the model:\nzero calls, no citations",
            "sessions 5, 6",
            False,
            "e2",
        ),
        (
            8.3,
            xs[3],
            "Provider hangs",
            "a flagged refusal. Not in the\nreference pipeline: YOU ADD IT",
            "session 14",
            True,
            None,
        ),
        (
            12.2,
            xs[4],
            "Reply will not parse",
            "one retry,\nthen a flagged refusal",
            "sessions 3, 5",
            False,
            None,
        ),
        (
            16.1,
            xs[5],
            "Citation never retrieved",
            "stripped, confidence capped\nat 0.2, flagged for a human",
            "sessions 3, 6",
            False,
            None,
        ),
    ]
    for x, src, name, note, taught, dashed, badge in exits:
        c.node(x, m, "shield", RED, name, note, w=3.0, h=1.7, dashed=dashed, badge=badge)
        c.ax.text(
            x,
            y + 0.95,
            f"taught in {taught}",
            fontsize=9,
            color=RED,
            ha="center",
            va="bottom",
            fontweight="bold",
        )
        c.arrow((src, 11.0 + 0.55), (x, m + 0.9), color=RED, rad=0.0)
    c.ax.text(
        10.3,
        y + 0.45,
        "Each one leaves by a door, never by a crash. And an instruction inside a passage "
        "is quoted, never obeyed (sessions 4 and 13).",
        fontsize=9.8,
        color=RED,
        ha="center",
        va="bottom",
        style="italic",
    )

    y, h = 0.2, 4.95
    c.row(y, h, "The\nevidence", PURPLE, "WHAT EVERY RUN LEAVES, AND WHO READS IT")
    m = y + h / 2 + 0.3
    cards = [
        ("layers", "Trace", "retrieve, llm_call,\ndecision (s9)", "e3"),
        ("checklist", "Contract tests", "tests/ in your\nrepository", None),
        ("target", "Eval gate", "golden set, before\nand after (s7, s9)", "e4"),
        ("magnifier", "Grader", "grade.py: gates per\ncase, critical safety", None),
        ("document", "Your docs", "ISSUES, EVAL_REPORT,\nSKILL, ADR, RETENTION", "e5"),
        ("flag", "Defence", "6 minutes, one failure\nyou did not plan (s15)", None),
    ]
    xs = [3.4, 5.95, 8.5, 11.05, 13.6, 16.3]
    for x, (icon, name, note, badge) in zip(xs, cards, strict=True):
        c.node(x, m, icon, PURPLE, name, note, w=2.2, badge=badge)
    c.save(ROOT / "units/en/unit2/capstone/img/architecture.png")


if __name__ == "__main__":
    model_rag_agent_team()
    project_02()
    capstone()
