"""`Canvas`: the inch-grid card, the icons drawn on it, and the arrows between.

One drawing primitive per idea a figure needs to say. Nothing here knows which
session it serves, and nothing here chooses a file."""

from __future__ import annotations

from pathlib import Path

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

from .theme import LIGHT, ROOT, install, palette

# The active palette, kept in step by `use_theme`. Every primitive reads these
# as plain globals, which is what lets one drawing render under either theme;
# registering is what stops this module holding a stale copy of the other.
(
    INK,
    DIM,
    LINE,
    PAGE,
    PANEL,
    BLUE,
    GREEN,
    BROWN,
    PURPLE,
    RED,
    TINT,
    TAB_INK,
    BADGE_FACE,
    BADGE_EDGE,
) = palette(LIGHT)
install(globals())


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
            color=TAB_INK,
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

    def label(self, x, y, text, size=11.5, color=None, bold=True, va="top"):
        # Resolved here, not in the signature: a default argument binds at import
        # time and would keep the light ink under a dark theme.
        color = INK if color is None else color
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

    def note(self, x, y, text, color=None, size=9.2, ha="center"):
        color = DIM if color is None else color
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

    def arrow(self, p1, p2, text="", color=None, rad=0.0, dy=0.14, dx=0.0, solid=False):
        color = DIM if color is None else color
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

    def path(self, points, text="", color=None, text_at=None):
        color = DIM if color is None else color
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
            Circle(
                (x, y), 0.26, facecolor=BADGE_FACE, edgecolor=BADGE_EDGE, linewidth=1.2, zorder=6
            )
        )
        self.ax.text(
            x,
            y,
            text,
            fontsize=8.5,
            fontweight="bold",
            color=BADGE_EDGE,
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
            color=TAB_INK,
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
