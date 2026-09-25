"""Session 10's two figures: where a skill sits, and what makes a decision reversible.

Dark only. The course pages carry the same two arguments in prose; these exist so the
room can see the shape while it is being argued.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.patches import FancyBboxPatch

from .slide import SLIDE_EDGE, SLIDE_ROUND, Slide
from .theme import DECK_10, LIGHT, figure, install, palette

# The active palette, kept in step by `use_theme`. Every primitive reads these as plain
# globals, which is what lets one drawing render under either theme; registering is what
# stops this module holding a stale copy of the other.
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


def _card(s: Slide, box: tuple[float, float, float, float], accent: str) -> None:
    left, top, right, bottom = box
    s.ax.add_patch(
        FancyBboxPatch(
            (left, top),
            right - left,
            bottom - top,
            boxstyle=f"round,pad=0,rounding_size={SLIDE_ROUND}",
            facecolor=PANEL,
            edgecolor=accent,
            linewidth=SLIDE_EDGE,
        )
    )


@figure(dark=f"{DECK_10}/01-where-a-skill-sits.png")
def where_a_skill_sits(target: Path) -> None:
    """A skill is text the model may follow. It is not code, and it is not a permission."""
    s = Slide(1430, 640)
    s.text(34, 44, "Where a skill sits", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "Text the model MAY follow, loaded when it is relevant. Not code the app runs, "
        "and not the thing that stops a write.",
        DIM,
        size=17,
    )

    # The skill: what it is.
    _card(s, (29, 132, 629, 470), GREEN)
    s.text(53, 168, "SKILL.md — an instruction artifact", GREEN, size=16, bold=True)
    s.ax.plot([53, 605], [194, 194], color=LINE, linewidth=1.4)
    sections = (
        ("When to use", "and, explicitly, when not to"),
        ("Workflow", "numbered, with a stop condition"),
        ("Output format", "so the next step can read it"),
        ("Failure rules", "what to do when it goes wrong"),
        ("Safety boundary", "a sentence, not an enforcement"),
    )
    for i, (name, why) in enumerate(sections):
        y = 224 + i * 46
        s.text(53, y, f"{i + 1}. {name}", INK, size=17, bold=True)
        s.text(318, y, why, DIM, size=14)
    s.text(53, 446, "The model reads it. It may ignore it.", GREEN, size=17, bold=True)

    # What it is NOT.
    _card(s, (665, 132, 1401, 470), RED)
    s.text(689, 168, "WHAT IT IS NOT", RED, size=16, bold=True)
    s.ax.plot([689, 1377], [194, 194], color=LINE, linewidth=1.4)
    nots = (
        ("Not code", "nothing here executes; it is a file of prose"),
        ("Not a permission", "the tool still decides whether a write happens"),
        ("Not always loaded", "the description line is what gets it chosen"),
        ("Not a guarantee", "a skill that changes nothing is decoration"),
    )
    for i, (name, why) in enumerate(nots):
        y = 230 + i * 54
        s.text(689, y, name, RED, size=17, bold=True)
        s.text(689, y + 24, why, DIM, size=15)
    s.text(689, 446, "A safety line here is a wish.", RED, size=17, bold=True)

    s.text(
        34,
        520,
        "SO THE TEST IS A MEASUREMENT, NOT A READING:",
        BROWN,
        size=16,
        bold=True,
    )
    s.text(
        34,
        556,
        "run the same task with the skill and without it. Two identical outputs mean the "
        "file did nothing,",
        INK,
        size=17,
    )
    s.text(
        34,
        586,
        "however well it reads. `ch10-e1` refuses two identical excerpts, which is the "
        "only way prose can be checked.",
        INK,
        size=17,
    )
    s.save(target)


@figure(dark=f"{DECK_10}/02-decision-or-preference.png")
def decision_or_preference(target: Path) -> None:
    """The reversal test: a number and a unit, or it is an opinion."""
    s = Slide(1430, 640)
    s.text(34, 44, "A decision, or a preference", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "Write down what would change your mind, before you are attached to being right.",
        DIM,
        size=17,
    )

    _card(s, (29, 132, 699, 430), RED)
    s.text(53, 168, "NOT A TRIGGER", RED, size=16, bold=True)
    s.ax.plot([53, 675], [194, 194], color=LINE, linewidth=1.4)
    for i, line in enumerate(
        ('"when it gets slow"', '"if quality drops"', '"when we have more users"')
    ):
        s.text(53, 232 + i * 52, line, INK, size=18)
    s.text(53, 398, "Nobody can ever show it happened.", RED, size=17, bold=True)

    _card(s, (731, 132, 1401, 430), GREEN)
    s.text(755, 168, "A TRIGGER: A NUMBER AND A UNIT", GREEN, size=16, bold=True)
    s.ax.plot([755, 1377], [194, 194], color=LINE, linewidth=1.4)
    for i, line in enumerate(
        (
            "p95 over 2000 ms for 15 minutes",
            "golden set under 0.8, two runs running",
            "the corpus passes 500 documents",
        )
    ):
        s.text(755, 232 + i * 52, line, INK, size=18)
    s.text(755, 398, "Somebody else can check it without you.", GREEN, size=17, bold=True)

    s.text(34, 486, "THE FOUR FIELDS", BROWN, size=16, bold=True)
    fields = (
        ("decision", "a choice, not a description"),
        ("options_considered", "at least two"),
        ("why_not", "why the loser lost, TODAY"),
        ("reverses_it", "the measurement that flips it"),
    )
    for i, (name, why) in enumerate(fields):
        x = 34 + i * 348
        s.text(x, 524, name, BROWN, size=16, bold=True)
        s.text(x, 552, why, DIM, size=13)

    s.text(
        34,
        600,
        "The last field is what makes the first three worth writing. "
        "Without it, an opinion with citations.",
        BROWN,
        size=17,
    )
    s.save(target)


SESSION_10 = (where_a_skill_sits, decision_or_preference)
