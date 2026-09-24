"""Session 9's two figures: what an answer can be, and the ceiling above a selector.

Both are dark only. There is no light course page behind them: the pages carry
the same two arguments in prose, and these exist so the room can see the shape
while it is being argued.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.patches import FancyBboxPatch, Rectangle

from .slide import SLIDE_EDGE, SLIDE_ROUND, Slide
from .theme import DECK_09, LIGHT, figure, install, palette

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


def _panel(s: Slide, left: float, accent: str, header: str) -> float:
    """One of the three columns: the box, its header, and the rule under it."""
    right = left + 440
    s.ax.add_patch(
        FancyBboxPatch(
            (left, 130),
            440,
            430,
            boxstyle=f"round,pad=0,rounding_size={SLIDE_ROUND}",
            facecolor=PANEL,
            edgecolor=accent,
            linewidth=SLIDE_EDGE,
        )
    )
    s.text(left + 24, 168, header, accent, size=16, bold=True)
    s.ax.plot([left + 24, right - 24], [194, 194], color=LINE, linewidth=1.4)
    return right


@figure(dark=f"{DECK_09}/01-ranking-vs-deciding.png")
def ranking_vs_deciding(target: Path) -> None:
    """Prose, an order, and typed options: only the third gives a threshold something."""
    s = Slide(1430, 640)
    s.text(34, 44, "Three answers to one question", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "Which endpoint settles a payment? Same question, three kinds of answer, "
        "and one you can branch on.",
        DIM,
        size=17,
    )

    # 1 — prose.
    _panel(s, 29, BROWN, "1 · A MODEL ANSWERS IN PROSE")
    s.ax.add_patch(
        FancyBboxPatch(
            (53, 216),
            392,
            136,
            boxstyle="round,pad=0,rounding_size=10",
            facecolor=TINT[BROWN],
            edgecolor="none",
        )
    )
    s.text(
        69,
        232,
        '"It looks like the transfer\nendpoint is probably the one,\n'
        'though /v1/payments may also\napply. Check the docs."',
        INK,
        size=16,
        va="top",
    )
    costs = (
        (394, "· you parse it"),
        (426, "· you invent a threshold"),
        (458, "· no option set, no probability"),
    )
    for y, line in costs:
        s.text(53, y, line, DIM, size=16)
    s.text(53, 512, "You cannot branch on this.", BROWN, size=19, bold=True)

    # 2 — a ranked list.
    _panel(s, 495, BLUE, "2 · A RANKER RETURNS AN ORDER")
    rows = (
        ("1", "POST /v1/transfers", "0.81"),
        ("2", "POST /v1/payments", "0.79"),
        ("3", "GET  /v1/balances", "0.78"),
        ("4", "POST /v1/quotes", "0.77"),
    )
    for i, (rank, name, score) in enumerate(rows):
        top = 216 + i * 50
        s.ax.add_patch(
            FancyBboxPatch(
                (519, top),
                392,
                40,
                boxstyle="round,pad=0,rounding_size=8",
                facecolor=PAGE,
                edgecolor=LINE,
                linewidth=1.2,
            )
        )
        s.text(535, top + 20, rank, BLUE, size=17, bold=True)
        s.ax.text(563, top + 20, name, fontsize=15, color=INK, family="monospace", va="center")
        s.text(895, top + 20, score, DIM, size=16, ha="right")
    s.text(
        519,
        430,
        "Cosine ranks. These four sit in a\nband 0.005 wide, so 0.81 says little.",
        DIM,
        size=15,
        va="top",
    )
    s.text(519, 512, "An order, not a decision.", BLUE, size=19, bold=True)

    # 3 — typed options with calibrated probabilities.
    _panel(s, 961, GREEN, "3 · A DECIDER RETURNS OPTIONS")
    options = (
        ("transfer", 0.62, GREEN),
        ("payment", 0.24, GREEN),
        ("balance", 0.09, GREEN),
        ("none of these", 0.05, DIM),
    )
    for i, (label, p, accent) in enumerate(options):
        top = 216 + i * 50
        s.text(985, top + 20, label, INK, size=16)
        s.ax.add_patch(Rectangle((1155, top + 11), p * 150, 18, facecolor=accent))
        s.text(1377, top + 20, f"{p:.2f}", accent, size=16, bold=True, ha="right")
    s.text(985, 440, "sums to 1.00", GREEN, size=17, bold=True)
    s.text(985, 512, "A threshold can test this.", GREEN, size=19, bold=True)

    s.text(
        34,
        602,
        "Only the third number means anything on its own. That is ranking against deciding.",
        BROWN,
        size=17,
    )
    s.save(target)


@figure(dark=f"{DECK_09}/02-stage1-stage2-ceiling.png")
def stage1_stage2_ceiling(target: Path) -> None:
    """Stage 2 picks among what stage 1 served, so stage 1's recall is its ceiling."""
    s = Slide(1430, 640)
    s.text(34, 44, "A selector cannot pick what retrieval never served", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "Stage 1 decides what is on the table. Stage 2 decides which one. "
        "Stage 2's ceiling is stage 1's recall.",
        DIM,
        size=17,
    )

    s.card((29, 136, 269, 260), "Stage 1\nretrieval", BLUE, size=19)

    # The pool, drawn before the chips so the chips sit on top of the dashed box.
    s.ax.add_patch(
        FancyBboxPatch(
            (325, 120),
            420,
            156,
            boxstyle="round,pad=0,rounding_size=12",
            facecolor="none",
            edgecolor=BLUE,
            linewidth=1.4,
            linestyle=(0, (4, 3)),
        )
    )
    s.text(535, 106, "EXACTLY THESE EIGHT, k=8", BLUE, size=15, bold=True, ha="center")
    for n in range(8):
        x = 337 + (n % 4) * 104
        y = 136 + (n // 4) * 68
        s.ax.add_patch(
            FancyBboxPatch(
                (x, y),
                92,
                54,
                boxstyle="round,pad=0,rounding_size=8",
                facecolor=PAGE,
                edgecolor=BLUE,
                linewidth=1.8,
            )
        )
        s.text(x + 46, y + 27, f"c{n + 1}", INK, size=15, ha="center")

    # The one that is not in the pool, which is the whole argument.
    s.ax.add_patch(
        FancyBboxPatch(
            (337, 300),
            168,
            58,
            boxstyle="round,pad=0,rounding_size=8",
            facecolor=PAGE,
            edgecolor=RED,
            linewidth=1.8,
            linestyle=(0, (3, 3)),
        )
    )
    s.text(421, 329, "the gold op,\nrank 19", RED, size=14, ha="center")
    s.text(525, 329, "not in the pool, so no selector reaches it", RED, size=16)

    s.card((785, 136, 1045, 260), "Stage 2\nselector", GREEN, size=19)
    s.text(915, 284, "picks among exactly those eight", DIM, size=15, ha="center")
    s.card((1093, 136, 1401, 260), "one typed option\n+ probability", GREEN, size=17)

    # Arrows last, so no arrowhead is clipped by a patch drawn after it.
    s.step(277, 317, 198)
    s.step(753, 777, 198)
    s.step(1053, 1085, 198)

    s.ax.plot([29, 1401], [378, 378], color=LINE, linewidth=1.4)

    s.text(34, 410, "THE CEILING WE MEASURED", BROWN, size=15, bold=True)
    s.text(34, 474, "0.22", BROWN, size=58, bold=True)
    s.text(250, 456, "pooled paraphrase recall@8", INK, size=18)
    s.text(250, 492, "27 tasks · measured 2026-09-23", DIM, size=15)

    s.text(640, 410, "PER SURFACE, SAME METRIC", BLUE, size=15, bold=True)
    surfaces = (
        ("txodds", 0.60, GREEN),
        ("pegana", 0.25, BROWN),
        ("birdeye", 0.12, BROWN),
        ("privy", 0.00, RED),
    )
    for i, (name, value, accent) in enumerate(surfaces):
        y = 442 + i * 40
        s.text(748, y, name, INK, size=17, ha="right")
        width = max(value * 600, 4)
        s.ax.add_patch(Rectangle((760, y - 13), width, 26, facecolor=accent))
        s.text(760 + width + 12, y, f"{value:.2f}", accent, size=17, bold=True)

    s.text(
        34,
        612,
        "A selector is a stage-2 tool. Our loss is stage 1. That is why we said no, "
        "and it is a number rather than a taste.",
        GREEN,
        size=17,
    )
    s.save(target)


SESSION_09 = (ranking_vs_deciding, stage1_stage2_ceiling)
