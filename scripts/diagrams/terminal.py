"""`Terminal`: a card of monospace output, coloured by what each line means.

Sessions 4 and 5 present what a notebook printed, not geometry. The card is a
character grid, so a receipt lines up under the reply above it and a refusal is
the same width as the call it refused."""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

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


# Sessions 4 and 5 present what the notebook printed, not geometry. The card is
# a character grid: a receipt lines up under the reply above it, and a refusal
# is the same width as the call it refused.
TERM_WIDTH = 1300  # px, what every one of these deck figures has always been
TERM_DPI = 100
TERM_MONO_PT = 14.2  # the one size whose advance is a whole 12 px at TERM_DPI
TERM_CHAR = 12.0  # px per column; spans are placed by column, never by measure
TERM_LINE = 28.0  # px between rows
TERM_PAD = 26.0  # px, the left margin
TERM_BAR = 47.0  # px, the title bar, when the card has one
TERM_LIGHTS = 7.0  # px, radius of a window button


class Terminal:
    """A card of monospace output, coloured by what each line means.

    Rows are collected and drawn on `save`, because the card's height is how
    many rows there are: a figure that gains a line must not also need its
    size edited somewhere else.
    """

    def __init__(self, title: str | None = None, width: int = TERM_WIDTH) -> None:
        self.title = title
        self.width = width
        self.rows: list[tuple[tuple[str, str, bool], ...]] = []

    @property
    def columns(self) -> int:
        """How many characters fit on a row. Wrapping asks this, never the width."""
        return int((self.width - 2 * TERM_PAD) / TERM_CHAR)

    # ------------------------------------------------------------- content
    def blank(self, count: int = 1) -> None:
        for _ in range(count):
            self.rows.append(())

    def line(self, text: str, colour: str = "ink", bold: bool = False) -> None:
        self.rows.append(((text, colour, bold),))

    def spans(self, *parts: tuple[str, str]) -> None:
        """One row in several colours, laid on the same character grid."""
        self.rows.append(tuple((text, colour, False) for text, colour in parts))

    def wrapped(
        self, text: str, colour: str = "ink", indent: int = 0, hanging: int | None = None
    ) -> None:
        """A paragraph, folded to the card. The card's width decides the break."""
        hanging = indent if hanging is None else hanging
        for line in textwrap.wrap(
            text,
            self.columns,
            initial_indent=" " * indent,
            subsequent_indent=" " * hanging,
        ):
            self.line(line, colour)

    # ------------------------------------------------------------- drawing
    def _hues(self) -> dict[str, str]:
        # Resolved here rather than at import: a figure body naming a colour
        # before `use_theme` has run would bind the light palette.
        return {
            "ink": INK,
            "dim": DIM,
            "green": GREEN,
            "red": RED,
            "amber": BROWN,
            "blue": BLUE,
        }

    def save(self, target: Path) -> None:
        top = TERM_BAR + 36 if self.title else 38
        height = top + (len(self.rows) - 1) * TERM_LINE + (52 if self.title else 41)
        fig = plt.figure(figsize=(self.width / TERM_DPI, height / TERM_DPI), facecolor=PAGE)
        ax = fig.add_axes((0, 0, 1, 1), facecolor=PAGE)
        ax.set_xlim(0, self.width)
        ax.set_ylim(height, 0)  # y grows downward, the way the output reads
        ax.axis("off")

        if self.title:
            ax.add_patch(Rectangle((0, 0), self.width, TERM_BAR, facecolor=PANEL, edgecolor="none"))
            for i, colour in enumerate((RED, BROWN, GREEN)):
                ax.add_patch(
                    Circle((TERM_PAD + i * 20, TERM_BAR / 2), TERM_LIGHTS, facecolor=colour, lw=0)
                )
            ax.text(
                TERM_PAD + 66,
                TERM_BAR / 2,
                self.title,
                fontsize=12,
                fontweight="bold",
                color=DIM,
                va="center",
            )

        hues = self._hues()
        for index, row in enumerate(self.rows):
            y = top + index * TERM_LINE
            column = 0
            for text, colour, bold in row:
                ax.text(
                    TERM_PAD + column * TERM_CHAR,
                    y,
                    text,
                    fontsize=TERM_MONO_PT,
                    family="monospace",
                    color=hues[colour],
                    fontweight="bold" if bold else "normal",
                    va="center",
                )
                column += len(text)

        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=TERM_DPI, facecolor=PAGE)
        plt.close(fig)
        print(f"wrote {target.relative_to(ROOT)}")
