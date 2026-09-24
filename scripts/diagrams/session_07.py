"""Session 7's four figures: the road, cosine, what cosine misses, and the pipeline.

The five similarity figures are measured, not illustrative: they are what
nomic-embed-text returns for those pairs. Re-measure before editing one.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from .slide import SLIDE_DPI, Slide, save_pixels
from .theme import DECK_07, LIGHT, figure, install, palette

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


#: Three angles, and where U and V point at each one. Offsets are from the
#: panel's own origin, in pixels, so the three crosses stay the same size.
SESSION_07_ANGLES = (
    ("same direction", "θ ≈ 0°  →  cos θ ≈ 1", "green", (98, -99), (136, -45)),
    ("perpendicular", "θ = 90°  →  cos θ = 0", "blue", (-36, -131), (140, -35)),
    ("opposite", "θ = 180°  →  cos θ = −1", "red", (-130, 50), (131, -58)),
)

#: Measured with nomic-embed-text. The first row is the whole point of the slide.
SESSION_07_PAIRS = (
    ("safe to sign", "dangerous to sign", 0.93, "red"),
    ("payment on Solana", "send tokens on Solana", 0.73, "green"),
    ("transaction fees", "refund policy for fees", 0.64, "brown"),
    ("cost me to send this", "transaction fees", 0.46, "blue"),
    ("payment on Solana", "weather tomorrow", 0.33, "dim"),
)

SESSION_07_BEFORE = (
    ("documents", "blue"),
    ("chunks", "blue"),
    ("embedding\nmodel", "green"),
    ("vector\n+ text + source", "blue"),
)
SESSION_07_WHEN = (
    ("question", "blue"),
    ("the SAME\nmodel", "green"),
    ("query\nvector", "blue"),
    ("nearest k\n= context", "blue"),
)


def _hue(name: str) -> str:
    # Named at the call site rather than bound at import, so a figure cannot
    # carry a light accent into a dark rendering.
    return {"ink": INK, "dim": DIM, "blue": BLUE, "green": GREEN, "brown": BROWN, "red": RED}[name]


@figure(dark=f"{DECK_07}/01-cosine-and-the-angle.png")
def s07_cosine_and_the_angle(target: Path) -> None:
    """Three angles between two vectors, and the one number each one is worth."""
    s = Slide(1430, 528)
    reach, top, floor = 200, 18, 378

    for index, (name, sum_up, hue, v_at, u_at) in enumerate(SESSION_07_ANGLES):
        cx, cy = 242 + index * 472.5, 215
        colour = _hue(hue)
        s.ax.plot([cx - reach, cx + reach], [cy, cy], color=LINE, linewidth=1.6)
        s.ax.plot([cx, cx], [top, floor], color=LINE, linewidth=1.6)
        for label, (dx, dy) in (("V", v_at), ("U", u_at)):
            s.arrow((cx, cy), (cx + dx, cy + dy), colour, scale=22, width=3.0)
            # the name sits past the tip, along the same line, so it never
            # lands on the arrow it belongs to
            s.text(
                cx + dx * 1.18,
                cy + dy * 1.18,
                label,
                colour,
                size=19,
                bold=True,
                ha="center",
            )
        s.text(cx, 429, name, colour, size=19, bold=True, ha="center")
        s.text(cx, 488, sum_up, INK, size=17, ha="center")

    s.save(target)


@figure(dark=f"{DECK_07}/02-similarity-is-not-meaning.png")
def s07_similarity_is_not_meaning(target: Path) -> None:
    """Five measured pairs. The opposite pair scores highest, and that is the lesson."""
    fig = plt.figure(figsize=(14.30, 5.72), facecolor=PAGE, dpi=SLIDE_DPI)
    ax = fig.add_axes((0.360, 0.168, 0.580, 0.666), facecolor=PAGE)

    places = range(len(SESSION_07_PAIRS))
    for place, (_, _, score, hue) in zip(places, SESSION_07_PAIRS, strict=True):
        ax.barh(place, score, height=0.62, color=_hue(hue))
        ax.text(
            score + 0.012,
            place,
            f"{score:.2f}",
            color=INK,
            fontsize=19,
            fontweight="bold",
            va="center",
        )

    ax.set_yticks(list(places))
    ax.set_yticklabels([f"{left}  /  {right}" for left, right, _, _ in SESSION_07_PAIRS])
    ax.invert_yaxis()
    ax.set_xlim(0, 1.02)
    ax.set_xticks([x / 5 for x in range(6)])
    ax.tick_params(axis="x", colors=DIM, length=0, labelsize=17)
    # the pairs are the longest text on the slide; sized so the widest one still
    # starts inside the figure rather than running off the left edge
    ax.tick_params(axis="y", colors=DIM, length=0, labelsize=15.5)
    for name, spine in ax.spines.items():
        spine.set_visible(name == "left")
    ax.spines["left"].set_color(LINE)
    for label in ax.get_yticklabels():
        label.set_color(INK)

    fig.text(
        0.988,
        0.935,
        "Cosine similarity, measured with nomic-embed-text (768 numbers)",
        color=INK,
        fontsize=17,
        fontweight="bold",
        ha="right",
    )
    fig.text(
        0.360,
        0.043,
        "The opposite pair scores highest. The unrelated pair is not 0.",
        color=BROWN,
        fontsize=17,
    )
    save_pixels(fig, target)


@figure(dark=f"{DECK_07}/03-the-embedding-pipeline.png")
def s07_the_embedding_pipeline(target: Path) -> None:
    """Two passes over the same model: one before any question, one when it arrives."""
    s = Slide(1430, 616)
    first, step, width, height = 29, 269.7, 232, 133
    store = (1133, 222, 1399, 394)

    for top, stops in ((95, SESSION_07_BEFORE), (354, SESSION_07_WHEN)):
        for index, (label, hue) in enumerate(stops):
            left = first + index * step
            # sized by the widest label on the slide, so no card's text touches
            # the edge it is supposed to sit inside
            s.card((left, top, left + width, top + height), label, _hue(hue), size=17.5)
            if index:
                s.step(left - step + width + 8, left - 8, top + height / 2)

    s.text(34, 48, "BEFORE ANY QUESTION", DIM, size=15, bold=True)
    s.text(34, 307, "WHEN THE QUESTION ARRIVES", DIM, size=15, bold=True)

    s.card(store, "vector\ndatabase", BROWN)
    # written on the way in, read on the way out: the same store, both passes
    s.arrow((first + 3 * step + width + 4, 168), ((store[0] + store[2]) / 2, store[1] - 6), BROWN)
    s.arrow((store[0] + 20, store[3] - 22), (first + 3 * step + width + 8, 400), BROWN)

    s.text(
        34,
        571,
        "Same model, same version, both sides. Vectors from two models cannot be "
        "compared, even at the same size.",
        BROWN,
        size=17,
    )
    s.save(target)


#: Every figure on this session's slides, in the order the deck shows them.
#: The road is not here: it is `road(7)`, one function for all fifteen sessions.
SESSION_07 = (
    s07_cosine_and_the_angle,
    s07_similarity_is_not_meaning,
    s07_the_embedding_pipeline,
)
