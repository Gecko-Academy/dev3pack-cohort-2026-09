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

    def panel(self, x0, y0, w, h, label, color, where="", tab_w=3.3):
        """`row`, stood up: the same light card, with its label tab across the top.

        `row` can only band the full width. Two things side by side, or four in a
        grid, need the tab at the top instead of down the left. Same card, same
        tab, same right-hand `where` slot.
        """
        self.ax.add_patch(
            FancyBboxPatch(
                (x0, y0),
                w,
                h,
                boxstyle="round,pad=0,rounding_size=0.25",
                facecolor=PANEL,
                edgecolor=LINE,
                linewidth=1.4,
            )
        )
        self.ax.add_patch(
            FancyBboxPatch(
                (x0 + 0.18, y0 + h - 1.0),
                tab_w,
                0.8,
                boxstyle="round,pad=0,rounding_size=0.18",
                facecolor=color,
                edgecolor=color,
            )
        )
        self.ax.text(
            x0 + 0.18 + tab_w / 2,
            y0 + h - 0.6,
            label,
            fontsize=15,
            fontweight="bold",
            color="white",
            ha="center",
            va="center",
        )
        if where:
            self.ax.text(
                x0 + w - 0.22,
                y0 + h - 0.6,
                where,
                fontsize=9.5,
                color=color,
                ha="right",
                va="center",
                fontweight="bold",
            )

    def spend(self, x, y, color, lines, w=6.8, h=1.75, title="What it spends"):
        """The cost, on its own card, because the cost is the whole comparison."""
        self.box(x, y, w, h, color)
        self.label(x, y + h / 2 - 0.16, title, size=10.5)
        for i, text in enumerate(lines):
            self.ax.text(
                x,
                y + h / 2 - 0.78 - i * 0.44,
                text,
                fontsize=11,
                color=INK,
                ha="center",
                va="center",
                family="monospace",
            )

    def failure(self, x, y, text, w=5.4, h=1.9):
        """The card on the right of every rung: the one new way this rung fails."""
        self.box(x, y, w, h, RED)
        self.shield(x - w / 2 + 0.62, y - 0.02, RED, s=0.8)
        self.ax.text(
            x - w / 2 + 1.25,
            y + 0.58,
            "The new way it fails",
            fontsize=10,
            fontweight="bold",
            color=RED,
            ha="left",
            va="center",
        )
        self.ax.text(
            x - w / 2 + 1.25,
            y - 0.18,
            text,
            fontsize=9.4,
            color=INK,
            ha="left",
            va="center",
            style="italic",
            linespacing=1.35,
        )

    def dot(self, x, y, c, r=0.095, filled=False):
        """One vector. The index pictures need a plain marker and no icon is one."""
        self.ax.add_patch(
            Circle(
                (x, y),
                r,
                facecolor=c if filled else PAGE,
                edgecolor=INK,
                linewidth=1.1,
                zorder=4,
            )
        )

    def query_dot(self, x, y, c, s=1.0):
        """The vector you are searching with: a dot inside a dashed ring."""
        self.ax.add_patch(
            Circle(
                (x, y),
                0.27 * s,
                facecolor=PAGE,
                edgecolor=c,
                linewidth=1.5,
                linestyle=(0, (2, 2)),
                zorder=5,
            )
        )
        self.ax.add_patch(
            Circle((x, y), 0.13 * s, facecolor=c, edgecolor=INK, linewidth=1.2, zorder=6)
        )

    def centroid(self, x, y, c, s=1.0):
        """A cluster's middle, drawn as a cross so it reads apart from a vector."""
        for dy in (0.16, -0.16):
            self.ax.plot(
                [x - 0.16 * s, x + 0.16 * s],
                [y - dy * s, y + dy * s],
                color=c,
                linewidth=2.0,
                zorder=5,
                solid_capstyle="round",
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


def loop_vs_graph() -> None:
    """One loop beside a graph of roles: the same task, and what each one spends."""
    c = Canvas(20, 13)
    c.title(
        0.4,
        12.35,
        "One loop, or a graph of roles",
        "The same task both ways: what each one is made of, and what each one spends",
    )

    # ---- left: one loop
    c.panel(0.4, 0.85, 9.3, 10.45, "One loop", BROWN, "ONE ROLE, ONE BUDGET", tab_w=3.0)
    c.node(1.75, 9.1, "target", BROWN, "Question", "one task", w=2.0, h=1.6)
    c.node(4.85, 9.1, "chip", BROWN, "agent", "one model, one prompt", w=2.6, h=1.9)
    c.node(8.1, 9.1, "gear", BROWN, "tool", "search_documents", w=2.2, h=1.7)
    c.arrow((2.8, 9.1), (3.5, 9.1))
    c.arrow((6.25, 9.1), (6.95, 9.1), "call")
    c.path(
        [(8.9, 8.25), (8.9, 7.55), (3.9, 7.55), (3.9, 8.15)],
        "and round again",
        text_at=(6.4, 7.63),
    )
    c.node(
        2.0,
        6.55,
        "checklist",
        BROWN,
        "step counter",
        "three tool calls, then it stops",
        w=2.6,
        h=1.7,
    )
    c.arrow((3.8, 7.68), (3.35, 7.45))
    c.node(
        7.1,
        5.9,
        "flag",
        BROWN,
        "Stop, with a receipt",
        "answered · budget · repeated_call",
        w=4.2,
        h=1.7,
    )
    c.arrow((3.35, 6.2), (4.85, 6.05), "the counter runs out")
    c.spend(5.05, 2.95, BROWN, ["1 model call", "2 with a corrective retry"])
    c.note(5.05, 1.8, "one role, one budget, one exit table")

    # ---- right: a graph of four roles
    c.panel(10.3, 0.85, 9.3, 10.45, "A graph", PURPLE, "FOUR NARROW ROLES", tab_w=3.0)
    c.ax.add_patch(
        FancyBboxPatch(
            (10.55, 4.25),
            8.9,
            5.9,
            boxstyle="round,pad=0,rounding_size=0.2",
            facecolor="none",
            edgecolor=PURPLE,
            linewidth=1.3,
            linestyle=(0, (4, 3)),
        )
    )
    c.ax.text(
        14.95,
        10.15,
        "ONE GRAPH: declared state, declared edges",
        fontsize=9.5,
        color=PURPLE,
        fontweight="bold",
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=TINT[PURPLE], edgecolor=PURPLE),
    )
    roles = [
        ("coordinator", "picks the path"),
        ("researcher", "finds passages"),
        ("writer", "writes, cites"),
        ("critic", "checks, once"),
    ]
    for i, (name, what) in enumerate(roles):
        px = 11.52 + i * 2.32
        c.box(px, 9.1, 1.8, 1.7, PURPLE)
        c.chip(px, 9.45, PURPLE, s=0.55)
        c.ax.text(
            px,
            8.85,
            name,
            fontsize=9.5,
            fontweight="bold",
            color=INK,
            ha="center",
            va="center",
            family="monospace",
        )
        c.note(px, 8.62, what, size=8.5)
        if i:
            c.arrow((px - 1.42, 9.1), (px - 0.92, 9.1), color=PURPLE, solid=True)

    # the one edge back, and the cap that makes it one
    c.ax.plot([18.48, 18.48, 16.16], [8.25, 7.45, 7.45], color=PURPLE, linewidth=1.3, zorder=2)
    c.arrow((16.16, 7.45), (16.16, 8.25), color=PURPLE, solid=True)
    c.badge(17.32, 7.45, "×1")
    c.note(17.32, 7.12, "cap: one revision")

    c.node(
        14.95,
        5.6,
        "layers",
        PURPLE,
        "shared state",
        "one typed dict, and every role reads it and writes it",
        w=4.4,
        h=1.7,
    )
    c.arrow((13.3, 6.45), (11.8, 8.25), "reads")
    c.arrow((15.6, 8.25), (15.9, 6.45), "writes", dx=-0.55)
    c.spend(14.95, 2.95, PURPLE, ["2 model calls", "4 with a revision"])
    c.note(14.95, 1.8, "four roles, four instructions, and one edge you capped on purpose")

    c.ax.text(
        0.45,
        0.55,
        "More roles cost more calls. The table is how you find out what they bought.",
        fontsize=10.5,
        color=DIM,
        va="top",
    )
    c.save(ROOT / "units/en/unit2/session-08-loops-and-graphs/img/loop-vs-graph.png")


def rag_family() -> None:
    """A ladder: each rung adds one thing to the rung below, and one new way to fail."""
    c = Canvas(18, 19.4)
    c.title(
        0.4,
        18.75,
        "The RAG family, rung by rung",
        "Read from the bottom up. Each rung adds one thing to the rung below it, "
        "and one new way to fail.",
    )

    rungs = [
        (
            0.3,
            "1",
            "A model\nalone",
            BLUE,
            "",
            "WHAT IT IS",
            True,
            [
                ("magnifier", "question", "as the reader asked it"),
                ("chip", "model", "answers from what\nit memorised"),
                ("bubbles", "answer", "fluent, and nothing\nto check it against"),
            ],
            "It answers from memory, and nothing\non the page says where that came from.",
        ),
        (
            3.85,
            "2",
            "Naive\nRAG",
            GREEN,
            "PROJECT 02, STEPS 5 TO 8",
            "WHAT IT ADDS",
            True,
            [
                ("document", "chunk", "split into pieces"),
                ("chip", "embed", "numbers per piece"),
                ("cylinder", "top k", "the nearest few"),
                ("bubbles", "answer", "from those passages"),
            ],
            "It retrieves a confidently wrong passage,\nand the answer reads just as well.",
        ),
        (
            7.4,
            "3",
            "Grounded\nand\nchecked",
            GREEN,
            "PROJECT 02, STEP 9",
            "WHAT IT ADDS",
            False,
            [
                ("document", "citations", "every claim carries\nthe id it came from"),
                ("shield", "a similarity floor", "below it, refuse\nrather than answer"),
                ("checklist", "a labelled set", "questions whose\nanswers you know"),
            ],
            "It scores well on the questions\nit was tuned on.",
        ),
        (
            10.95,
            "4",
            "Routed\nand\nhybrid",
            BROWN,
            "",
            "WHAT IT ADDS",
            True,
            [
                ("hub", "a router", "narrows before\nit searches"),
                ("magnifier", "hybrid search", "keyword and\nembeddings together"),
                ("layers", "one ranked list", "both scores, merged"),
            ],
            "The router picks wrong, and the answer\nstill looks right.",
        ),
        (
            14.5,
            "5",
            "A team\nin a\ngraph",
            PURPLE,
            "PROJECT 03",
            "WHAT IT ADDS",
            False,
            [
                ("chip", "narrow roles", "coordinator, researcher,\nwriter, critic"),
                ("hub", "declared edges", "written down, not\ndiscovered at run time"),
                ("layers", "shared state", "one typed dict,\nevery role reads it"),
            ],
            "It costs more, and it takes a transition\nnobody declared.",
        ),
    ]

    h = 3.3
    for y, number, label, color, where, tag, arrows, cards, fails in rungs:
        c.row(y, h, label, color, where)
        c.badge(0.58, y + h - 0.18, number)
        m = y + 1.75
        c.ax.text(
            2.95,
            y + 2.85,
            tag,
            fontsize=9,
            fontweight="bold",
            color=color,
            ha="left",
            va="center",
        )
        n = len(cards)
        w = 1.95 if n == 4 else 2.3
        xs = [3.6 + i * (6.8 / (n - 1)) for i in range(n)]
        for x, (icon, name, note) in zip(xs, cards, strict=True):
            c.node(x, m, icon, color, name, note, w=w, h=1.7)
        if arrows:
            for a, b in zip(xs, xs[1:], strict=False):
                c.arrow((a + w / 2 + 0.02, m), (b - w / 2 - 0.02, m))
        c.failure(14.55, m, fails)

    c.ax.text(
        0.45,
        -0.25,
        "Climb a rung when a measured failure justifies it, and not before.",
        fontsize=10.5,
        color=DIM,
        va="top",
    )
    c.save(ROOT / "units/en/unit2/session-08-loops-and-graphs/img/rag-family.png")


def vector_indexes() -> None:
    """What sits under a vector database: four structures, and no measurements.

    Deliberately numberless. Speed, memory and recall belong in the table on the
    page, where a figure cannot strip the source off them.
    """
    c = Canvas(18, 14)
    c.title(
        0.4,
        13.35,
        "What sits under a vector database",
        "Four index structures, drawn as shapes. This figure carries no measurements.",
    )

    # ---- flat: compare against every vector
    c.panel(0.4, 7.0, 8.3, 5.5, "Flat", BLUE, "EXACT", tab_w=2.2)
    flat = [
        (3.3, 11.0),
        (4.4, 11.0),
        (5.5, 11.0),
        (6.6, 11.0),
        (7.7, 11.0),
        (3.1, 10.1),
        (4.2, 10.1),
        (5.3, 10.1),
        (6.4, 10.1),
        (7.5, 10.1),
        (8.2, 10.1),
        (3.4, 9.2),
        (4.5, 9.2),
        (5.6, 9.2),
        (6.7, 9.2),
        (7.8, 9.2),
        (3.2, 8.3),
        (4.3, 8.3),
        (5.4, 8.3),
        (6.5, 8.3),
        (7.6, 8.3),
    ]
    for px, py in flat:
        c.ax.plot([1.6, px], [9.5, py], color=LINE, linewidth=0.7, zorder=1)
    for px, py in flat:
        c.dot(px, py, BLUE, filled=(px, py) == (3.1, 10.1))
    c.query_dot(1.6, 9.5, BLUE)
    c.label(1.6, 9.12, "query", size=9.5)
    c.note(3.1, 10.52, "the nearest one", size=8.8)
    c.note(4.55, 7.62, "every vector compared, one by one, exactly")

    # ---- IVF: clusters around centroids, most of them skipped
    c.panel(9.3, 7.0, 8.3, 5.5, "IVF", GREEN, "CLUSTERED", tab_w=2.2)
    clusters = [
        (11.3, 10.5, 1.15, 0.80, True),
        (13.85, 10.5, 1.15, 0.80, False),
        (16.3, 10.4, 1.10, 0.80, False),
        (12.6, 8.75, 1.15, 0.82, True),
        (15.4, 8.7, 1.15, 0.80, False),
    ]
    for cx, cy, rx, ry, searched in clusters:
        c.ax.add_patch(
            Ellipse(
                (cx, cy),
                rx * 2,
                ry * 2,
                facecolor=TINT[GREEN] if searched else PAGE,
                edgecolor=GREEN if searched else LINE,
                linewidth=1.6 if searched else 1.3,
                linestyle="-" if searched else (0, (4, 3)),
                zorder=2,
            )
        )
        c.centroid(cx, cy + 0.18, GREEN if searched else DIM)
        for ox, oy in ((-0.6, -0.15), (-0.2, -0.45), (0.25, -0.42), (0.62, -0.1)):
            c.dot(cx + ox, cy + oy, GREEN)
        c.note(
            cx,
            cy + ry - 0.08,
            "searched" if searched else "skipped",
            color=GREEN if searched else DIM,
            size=8.8,
        )
    for cx, cy, _rx, _ry, searched in clusters:
        if searched:
            c.ax.plot([10.4, cx], [9.3, cy + 0.18], color=GREEN, linewidth=1.4, zorder=3)
    c.query_dot(10.4, 9.3, GREEN)
    c.label(10.4, 8.95, "query", size=9.5)
    c.note(13.45, 7.62, "the query searches its nearest clusters, and skips the rest")

    # ---- PQ: pieces, each replaced by a short code
    c.panel(0.4, 0.8, 8.3, 5.5, "PQ", BROWN, "COMPRESSED", tab_w=2.1)
    c.label(4.55, 5.08, "one long vector", size=10.5)
    c.ax.add_patch(
        Rectangle(
            (1.3, 4.25),
            6.5,
            0.45,
            facecolor=TINT[BROWN],
            edgecolor=INK,
            linewidth=1.4,
            zorder=3,
        )
    )
    edges = [1.3 + 6.5 * k / 4 for k in range(5)]
    for x in edges[1:-1]:
        c.ax.plot([x, x], [4.25, 4.70], color=INK, linewidth=1.3, zorder=4)
    codes = ["kq", "mv", "zt", "bd"]
    middles = [(edges[k] + edges[k + 1]) / 2 for k in range(4)]
    for sx, code in zip(middles, codes, strict=True):
        c.arrow((sx, 4.22), (sx, 3.80))
        c.ax.add_patch(
            FancyBboxPatch(
                (sx - 0.475, 3.2),
                0.95,
                0.6,
                boxstyle="round,pad=0,rounding_size=0.1",
                facecolor=TINT[BROWN],
                edgecolor=BROWN,
                linewidth=1.4,
                zorder=3,
            )
        )
        c.ax.text(
            sx,
            3.5,
            code,
            fontsize=10,
            fontweight="bold",
            color=INK,
            ha="center",
            va="center",
            family="monospace",
            zorder=4,
        )
    c.note(4.55, 3.05, "each piece becomes a short code")
    c.ax.add_patch(
        Rectangle(
            (3.53, 2.25),
            2.04,
            0.5,
            facecolor=TINT[BROWN],
            edgecolor=INK,
            linewidth=1.4,
            zorder=3,
        )
    )
    for k in range(1, 4):
        c.ax.plot([3.53 + 0.51 * k] * 2, [2.25, 2.75], color=INK, linewidth=1.1, zorder=4)
    for k, code in enumerate(codes):
        c.ax.text(
            3.785 + 0.51 * k,
            2.5,
            code,
            fontsize=8.5,
            color=INK,
            ha="center",
            va="center",
            family="monospace",
            zorder=4,
        )
    c.label(4.55, 2.10, "what gets stored", size=10.5)
    c.shield(6.85, 2.5, RED, s=0.8)
    c.ax.text(
        7.25,
        2.5,
        "the original\nis not\nrecoverable",
        fontsize=8.6,
        color=RED,
        ha="left",
        va="center",
        style="italic",
        linespacing=1.3,
    )
    c.note(4.55, 1.35, "small, and lossy")

    # ---- HNSW: sparse on top, dense at the bottom, a greedy descent
    c.panel(9.3, 0.8, 8.3, 5.5, "HNSW", PURPLE, "LAYERED", tab_w=2.4)
    bands = [(3.95, "sparse"), (2.85, "denser"), (1.75, "every vector")]
    for by, name in bands:
        c.ax.add_patch(
            FancyBboxPatch(
                (10.3, by),
                6.0,
                0.8,
                boxstyle="round,pad=0,rounding_size=0.15",
                facecolor="none",
                edgecolor=PURPLE,
                linewidth=1.3,
                linestyle=(0, (4, 3)),
                zorder=1,
            )
        )
        c.ax.text(
            16.5,
            by + 0.4,
            name,
            fontsize=9,
            color=DIM,
            ha="left",
            va="center",
            style="italic",
        )
    for px in (10.9, 12.6, 14.3, 15.8):
        c.dot(px, 4.35, PURPLE)
    for px in (10.8, 11.8, 12.9, 14.0, 15.1, 15.9):
        c.dot(px, 3.25, PURPLE)
    for px in (10.7, 11.25, 11.8, 12.35, 12.9, 13.45, 14.0, 14.55, 15.1, 15.65, 16.0):
        c.dot(px, 2.15, PURPLE)
    for p1, p2 in (
        ((11.2, 4.35), (12.35, 4.35)),
        ((12.6, 4.15), (12.9, 3.45)),
        ((13.15, 3.25), (13.75, 3.25)),
        ((14.0, 3.05), (13.6, 2.35)),
        ((13.65, 2.15), (14.4, 2.15)),
    ):
        c.arrow(p1, p2, color=PURPLE, solid=True)
    c.query_dot(10.9, 4.35, PURPLE, s=0.9)
    c.label(10.9, 5.02, "entry point", size=9.5)
    c.dot(14.55, 2.15, PURPLE, r=0.13, filled=True)
    c.note(14.55, 1.68, "nearest neighbour", size=8.8)
    c.note(13.45, 1.35, "an entry point at the top, and a greedy descent to the bottom")

    c.ax.text(
        0.45,
        0.45,
        "Structure only. Speed, memory and recall are measurements, and they live in the "
        "table on the page, where they carry a source.",
        fontsize=10.5,
        color=DIM,
        va="top",
    )
    c.save(ROOT / "units/en/unit2/session-08-loops-and-graphs/img/vector-indexes.png")


if __name__ == "__main__":
    model_rag_agent_team()
    project_02()
    capstone()
    loop_vs_graph()
    rag_family()
    vector_indexes()
