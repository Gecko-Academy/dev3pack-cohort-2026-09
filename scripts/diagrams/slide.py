"""`Slide`: a dark deck figure measured in pixels, the way a slide is measured.

`Canvas` draws on an inch grid because its figures are pages, read at whatever
size the reader's browser picks. These are slides: laid out against a fixed
pixel width and shown at it, so the pixel is the honest unit and a card's
position is the number somebody measured off the projected image.

Origin is top left and y grows downward, because that is the order a slide is
read and the order these figures were laid out in.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

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


SLIDE_DPI = 100
SLIDE_ROUND = 14  # px, the corner radius every deck card has
SLIDE_EDGE = 2.6  # px, the width of a card's coloured edge


def save_pixels(fig: plt.Figure, target: Path) -> None:
    """Write a pixel-measured figure. The one place a deck PNG's size is decided."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=SLIDE_DPI, facecolor=PAGE)
    plt.close(fig)
    print(f"wrote {target.relative_to(ROOT)}")


class Slide:
    def __init__(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        self.fig = plt.figure(
            figsize=(width / SLIDE_DPI, height / SLIDE_DPI), facecolor=PAGE, dpi=SLIDE_DPI
        )
        self.ax = self.fig.add_axes((0, 0, 1, 1), facecolor=PAGE)
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(height, 0)
        self.ax.axis("off")

    def card(
        self,
        box: tuple[float, float, float, float],
        label: str,
        colour: str,
        *,
        fill: str | None = None,
        ink: str | None = None,
        size: float = 19,
    ) -> None:
        """A rounded card with a coloured edge. `box` is (left, top, right, bottom)."""
        left, top, right, bottom = box
        self.ax.add_patch(
            FancyBboxPatch(
                (left, top),
                right - left,
                bottom - top,
                boxstyle=f"round,pad=0,rounding_size={SLIDE_ROUND}",
                facecolor=fill or PAGE,
                edgecolor=colour,
                linewidth=SLIDE_EDGE,
            )
        )
        self.text(
            (left + right) / 2,
            (top + bottom) / 2,
            label,
            ink or INK,
            size=size,
            bold=True,
            ha="center",
        )

    def step(self, left: float, right: float, y: float, colour: str | None = None) -> None:
        """The stubby arrow between two cards in a row: the reading order, made literal."""
        self.arrow((left, y), (right, y), colour or INK, scale=22, width=3.2)

    def arrow(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        colour: str,
        *,
        scale: float = 26,
        width: float = 2.4,
    ) -> None:
        self.ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=scale,
                linewidth=width,
                color=colour,
                shrinkA=0,
                shrinkB=0,
            )
        )

    def text(
        self,
        x: float,
        y: float,
        text: str,
        colour: str | None = None,
        *,
        size: float = 15,
        bold: bool = False,
        ha: str = "left",
        va: str = "center",
    ) -> None:
        self.ax.text(
            x,
            y,
            text,
            fontsize=size,
            color=colour or INK,
            fontweight="bold" if bold else "normal",
            ha=ha,
            va=va,
            linespacing=1.35,
        )

    def save(self, target: Path) -> None:
        save_pixels(self.fig, target)
