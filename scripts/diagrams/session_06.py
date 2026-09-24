"""Session 6's three figures: where retrieval sits, what a vector is, what a score is.

The numbers quoted here are the notebook's own: 768 for nomic-embed-text, and
3.84 for the dot product the retrieval baseline prints. Change the notebook
first, then these.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from .slide import SLIDE_DPI, SLIDE_EDGE, SLIDE_ROUND, Slide, save_pixels
from .theme import DECK_06, LIGHT, figure, install, palette

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


LIT_FILL = "#0f2a1a"  # the one lit card: dark green, the same one the road uses

#: The question's words, and whether the chunk being scored shares each one.
SESSION_06_WORDS = (
    ("agent", True),
    ("answer", True),
    ("cannot", True),
    ("justifies", False),
    ("falls", False),
    ("class", False),
)

#: One row of the dot product: its label, and the six numbers under the words.
SESSION_06_SCORE = (
    ("question", "1", "1", "1", "0", "0", "0"),
    ("agent-loops#2", "1.35", "1.13", "1.35", "3.18", "3.18", "3.18"),
    ("multiply", "1.35", "1.13", "1.35", "0.00", "0.00", "0.00"),
)


@figure(dark=f"{DECK_06}/01-rag-flow.png")
def s06_rag_flow(target: Path) -> None:
    """The whole route, with the one step today is about lit and the model dimmed."""
    s = Slide(1430, 506)
    top, bottom, width, step = 117, 267, 238, 286
    middle = (top + bottom) / 2

    stops = (
        ("Question", BLUE, None),
        ("Retrieve", GREEN, LIT_FILL),
        ("Context", BLUE, None),
        ("Model", DIM, None),
        ("Answer\nor action", BLUE, None),
    )
    for index, (label, colour, fill) in enumerate(stops):
        left = 29 + index * step
        s.card(
            (left, top, left + width, bottom),
            label,
            colour,
            fill=fill,
            ink=DIM if colour is DIM else INK,
        )
        if index:
            s.step(left - step + width + 8, left - 8, middle)

    s.text(29 + step + width / 2, 50, "TODAY", GREEN, size=19, bold=True, ha="center")
    s.text(29 + 3 * step + width / 2, 53, "not today", DIM, ha="center")

    # the documents feed retrieval, and nothing else on the row
    corpus = (29 + step, 354, 29 + step + width, 481)
    s.card(corpus, "your\ndocuments", BROWN, size=15)
    s.arrow((29 + step + width / 2, 349), (29 + step + width / 2, 275), BROWN)

    s.text(
        722,
        398,
        "If the right passage never comes back,\nthe model cannot answer from it.",
        BROWN,
        size=17,
        va="top",
    )
    s.save(target)


@figure(dark=f"{DECK_06}/02-a-vector.png")
def s06_a_vector(target: Path) -> None:
    """Two numbers you can draw, beside the number of dimensions a real one has."""
    fig = plt.figure(figsize=(12.10, 5.72), facecolor=PAGE, dpi=SLIDE_DPI)
    ax = fig.add_axes((0.045, 0.105, 0.515, 0.86), facecolor=PAGE)
    ax.set_xlim(-0.55, 4.6)
    ax.set_ylim(-0.55, 3.55)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(range(5))
    ax.set_yticks(range(4))
    ax.tick_params(colors=DIM, length=0, labelsize=15)
    ax.grid(color=LINE, linewidth=1)
    ax.set_axisbelow(True)
    ax.axhline(0, color=DIM, linewidth=1.4)
    ax.axvline(0, color=DIM, linewidth=1.4)

    ax.annotate(
        "",
        xy=(3, 2),
        xytext=(0, 0),
        arrowprops={"arrowstyle": "-|>", "color": BLUE, "linewidth": 4, "mutation_scale": 26},
    )
    for line in (((0, 3), (2, 2)), ((3, 3), (0, 2))):
        ax.plot(*line, color=BLUE, linewidth=1.6, linestyle=(0, (5, 4)))
    ax.text(2.35, 2.25, "U = (3, 2)", color=BLUE, fontsize=19, fontweight="bold")
    ax.text(1.5, -0.38, "Ux = 3", color=DIM, fontsize=15, ha="center")
    ax.text(-0.36, 1.0, "Uy = 2", color=DIM, fontsize=15, va="center", rotation=90)

    told = (
        (0.815, "A vector is a list of numbers.", INK, 20, True),
        (0.660, "Two numbers: we can draw it.", INK, 17, False),
        (0.507, "nomic-embed-text: 768 numbers.", BLUE, 17, False),
        (0.400, "Today's word vectors: one number\nper word in the corpus.", GREEN, 17, False),
    )
    for y, text, colour, size, bold in told:
        fig.text(
            0.601,
            y,
            text,
            color=colour,
            fontsize=size,
            fontweight="bold" if bold else "normal",
            va="top",
            linespacing=1.4,
        )

    save_pixels(fig, target)


@figure(dark=f"{DECK_06}/03-todays-score-is-a-dot-product.png")
def s06_dot_product(target: Path) -> None:
    """The notebook's 3.84, taken apart: six words, three rows, one sum."""
    s = Slide(1650, 594)
    left, cell, gap, row_top, row_h, row_gap = 346, 159, 170.5, 178, 78, 110

    s.text(34, 65, 'question: "what should an agent do when it cannot answer"', DIM)
    for index, (word, shared) in enumerate(SESSION_06_WORDS):
        s.text(
            left + index * gap + cell / 2,
            137,
            word,
            BLUE if shared else DIM,
            size=17,
            bold=True,
            ha="center",
        )

    for row, (label, *values) in enumerate(SESSION_06_SCORE):
        top = row_top + row * row_gap
        accent = BROWN if label == "multiply" else BLUE
        s.text(
            34, top + row_h / 2, label, accent if label == "multiply" else INK, size=17, bold=True
        )
        for index, value in enumerate(values):
            # the middle row is the chunk itself, so every one of its numbers is real;
            # elsewhere a word the chunk does not share is the point being made
            lit = SESSION_06_WORDS[index][1] or label == "agent-loops#2"
            x = left + index * gap
            s.ax.add_patch(
                FancyBboxPatch(
                    (x, top),
                    cell,
                    row_h,
                    boxstyle=f"round,pad=0,rounding_size={SLIDE_ROUND}",
                    facecolor=PAGE,
                    edgecolor=accent if lit else LINE,
                    linewidth=SLIDE_EDGE,
                )
            )
            s.text(
                x + cell / 2,
                top + row_h / 2,
                value,
                INK if lit else DIM,
                size=17,
                bold=lit,
                ha="center",
            )

    s.text(1405, 437, "add up\n= 3.84", BROWN, size=21, bold=True)
    s.text(
        34, 547, "The 3.84 in your notebook is this sum. A word the chunk does not share adds 0."
    )
    s.save(target)


#: Every figure on this session's slides, in the order the deck shows them.
SESSION_06 = (s06_rag_flow, s06_a_vector, s06_dot_product)
