"""The fifteen-session road, with TODAY on one card.

One figure, one parameter: the session number decides the badged card, which
cards are dimmed ahead of the class, and which session directory it writes into."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from .theme import DARK, LIGHT, ROOT, install, palette, use_theme

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


# One line per session: the short label on its card, and the capstone piece it
# hands you. Both are read from units/en/unit2/capstone/road.mdx — change them
# there first, then here.
ROAD_SESSIONS: tuple[tuple[str, str | None], ...] = (
    ("assistant", None),
    ("model\nadapter", None),
    ("typed\noutput", None),
    ("bounded\ntools", None),
    ("mini-\nagent", None),
    ("retrieval", "load +\nretrieve"),
    ("metrics", "baseline\npass rate"),
    ("graphs", "run shape\n+ cost"),
    ("trace +\neval", "trace +\nrun_evals"),
    ("skill +\nADR", "SKILL.md\n+ ADR"),
    ("memory", "retention\npolicy"),
    ("MCP", "tools:\nread only"),
    ("secure\nserver", "recorded\nsource"),
    ("deploy", "harden +\nregression"),
    ("defend", "demo +\ndiagnose"),
)
ROAD_WEEKS = (
    (1, 5, "WEEK 1 \u00b7 contracts before code"),
    (6, 10, "WEEK 2 \u00b7 grounding and evidence"),
    (11, 15, "WEEK 3 \u00b7 operating it"),
)
ROAD_CHECKS = {6: "e1  e2", 9: "e3  e4  e5"}
ROAD_TODAY_FILL = "#10231a"  # the one lit card: dark green, not an accent


def road(today: int) -> None:
    """The fifteen-session road, with TODAY on one card. One render per session day.

    `today` is the session number, 1 to 15. It picks the badged card, decides
    which cards are lit and which are dimmed ahead of the class, and chooses the
    output directory: docs/instructor/sessions/session-<today>-*/img/00-the-road.png.
    """
    if not 1 <= today <= len(ROAD_SESSIONS):
        raise ValueError(f"today must be a session number 1..{len(ROAD_SESSIONS)}, got {today}")
    sessions = sorted((ROOT / "docs/instructor/sessions").glob(f"session-{today:02d}-*"))
    if not sessions:
        raise FileNotFoundError(f"no docs/instructor/sessions/session-{today:02d}-* to write into")

    # geometry: one row of fifteen cards, everything else measured off that row
    card_w, gap, x0 = 0.92, 0.12, 0.35
    step = card_w + gap
    width, height = 2 * x0 + 15 * step - gap, 6.4
    y_week, y_rule = 5.95, 5.8
    y_badge, y_card, card_h = 5.54, 4.2, 1.3
    y_piece, piece_h = 2.45, 1.1
    y_checks, y_projects, y_capstone = 2.1, 1.2, 0.55

    def card_x(session: int) -> float:
        return x0 + (session - 1) * step

    with use_theme(DARK):
        week_colour = (BLUE, GREEN, BROWN)
        fig = plt.figure(figsize=(width, height), facecolor=PAGE)
        ax = fig.add_axes((0, 0, 1, 1), facecolor=PAGE)
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.axis("off")

        for (first, last, label), colour in zip(ROAD_WEEKS, week_colour, strict=True):
            ax.text(card_x(first), y_week, label, fontsize=13, fontweight="bold", color=colour)
            ax.plot([card_x(first), card_x(last) + card_w], [y_rule] * 2, color=colour, linewidth=3)

        for number, (label, piece) in enumerate(ROAD_SESSIONS, start=1):
            left, centre = card_x(number), card_x(number) + card_w / 2
            colour = week_colour[(number - 1) // 5]
            ahead = number > today
            ax.add_patch(
                FancyBboxPatch(
                    (left, y_card),
                    card_w,
                    card_h,
                    boxstyle="round,pad=0.02,rounding_size=0.1",
                    linewidth=2.2,
                    edgecolor=colour,
                    facecolor=ROAD_TODAY_FILL if number == today else PAGE,
                )
            )
            ax.text(
                centre,
                y_card + 0.92,
                str(number),
                ha="center",
                fontsize=14,
                fontweight="bold",
                color=colour,
            )
            ax.text(
                centre,
                y_card + 0.5,
                label,
                ha="center",
                va="center",
                fontsize=10.5,
                color=DIM if ahead else INK,
            )

            if piece is None:
                continue
            ax.plot([centre] * 2, [y_card, y_piece + piece_h], color=DIM, linewidth=1.2)
            ax.add_patch(
                FancyBboxPatch(
                    (left, y_piece),
                    card_w,
                    piece_h,
                    boxstyle="round,pad=0.02,rounding_size=0.1",
                    linewidth=1.8,
                    edgecolor=BROWN,
                    facecolor=PAGE,
                )
            )
            ax.text(
                centre,
                y_piece + piece_h / 2,
                piece,
                ha="center",
                va="center",
                fontsize=9.5,
                color=INK,
            )

        for number, checks in ROAD_CHECKS.items():
            ax.text(
                card_x(number) + card_w / 2,
                y_checks,
                checks,
                ha="center",
                fontsize=11,
                fontweight="bold",
                color=GREEN,
            )

        gutter = card_x(6) - 0.05
        ax.text(
            gutter,
            y_piece + piece_h / 2,
            "capstone\npieces",
            ha="right",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=BROWN,
        )
        ax.text(
            gutter,
            y_checks + 0.02,
            "checks\ngo green",
            ha="right",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=GREEN,
        )

        # the TODAY badge, sitting on its card
        ax.add_patch(
            FancyBboxPatch(
                (card_x(today) + 0.1, y_badge - 0.14),
                card_w - 0.2,
                0.28,
                boxstyle="round,pad=0.01,rounding_size=0.06",
                linewidth=0,
                facecolor=GREEN,
            )
        )
        ax.text(
            card_x(today) + card_w / 2,
            y_badge,
            "TODAY",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=PAGE,
        )

        ax.text(
            x0,
            y_projects,
            "Projects (optional practice):   02 real RAG on company filings  ->  steps 6, 7"
            "      03 an agent team in a graph  ->  steps 8, 9",
            fontsize=12,
            color=BLUE,
        )
        ax.text(
            x0,
            y_capstone,
            "The capstone: answers from the corpus, cites every claim, refuses when "
            "unsupported. Five checks, then you defend it live.",
            fontsize=12.5,
            color=INK,
        )

        target = sessions[0] / "img/00-the-road.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=110, facecolor=PAGE)
        plt.close(fig)
        print(f"wrote {target.relative_to(ROOT)}")
