"""Week 3's two projects, in one deck and divided: the Gecko capstone, then the final assignment.

Dark only, for the deck in `docs/instructor/decks/week3-projects/`. The terminal cards
print output that was RUN on 30 September 2026, on a fresh clone of the capstone
repository and on a repository made with `bootcamp final new`. Change one only by
running it again.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.patches import FancyBboxPatch

from .slide import SLIDE_EDGE, SLIDE_ROUND, Slide
from .terminal import Terminal
from .theme import DECK_PROJECTS, LIGHT, figure, install, palette

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


def _box(s: Slide, x: float, y: float, w: float, h: float, text: str, accent: str) -> None:
    s.ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0,rounding_size=10",
            facecolor=PAGE,
            edgecolor=accent,
            linewidth=2,
        )
    )
    s.text(x + w / 2, y + h / 2, text, accent, size=14, bold=True, ha="center")


def _rule(s: Slide, left: float, right: float, y: float) -> None:
    s.ax.plot([left, right], [y, y], color=LINE, linewidth=1.4)


@figure(dark=f"{DECK_PROJECTS}/00-two-projects.png")
def two_projects(target: Path) -> None:
    """The cover: two projects, judged apart, built in two repositories."""
    s = Slide(1430, 600)
    s.text(34, 44, "Two projects this week. They are separate.", INK, size=26, bold=True)
    s.text(34, 86, "Nothing in one changes the grade of the other.", DIM, size=17)
    columns = (
        (
            "THE GECKO CAPSTONE",
            BLUE,
            (
                ("what", "your store on devnet, and a buyer agent"),
                ("repository", "my-gecko-buyer"),
                ("judged by", "the presentation, Friday 2 October"),
                ("you show", "one receipt, and one refusal by field"),
                ("test it with", "uv run buyer --cases --recorded"),
            ),
        ),
        (
            "THE FINAL ASSIGNMENT",
            PURPLE,
            (
                ("what", "a research agent over six documents"),
                ("repository", "my-final-assignment"),
                ("judged by", "15 private questions, for the certificate"),
                ("you pass with", "30% or more AND every critical one"),
                ("test it with", "uv run bootcamp final grade"),
            ),
        ),
    )
    for col, (title, accent, rows) in enumerate(columns):
        left = 29 + col * 712
        _card(s, (left, 132, left + 660, 540), accent)
        s.text(left + 24, 170, title, accent, size=18, bold=True)
        _rule(s, left + 24, left + 636, 196)
        for i, (label, value) in enumerate(rows):
            y = 240 + i * 62
            s.text(left + 24, y, label, DIM, size=14, bold=True)
            s.text(left + 190, y, value, INK, size=15)
    s.save(target)


@figure(dark=f"{DECK_PROJECTS}/10-capstone-loop.png")
def capstone_loop(target: Path) -> None:
    """The buyer's loop: seven steps, and the one place it may stop."""
    s = Slide(1430, 560)
    s.text(34, 44, "The Gecko capstone: what your buyer does", INK, size=26, bold=True)
    s.text(
        34,
        86,
        'You ask once, "one espresso". Gecko prepares unsigned bytes; your code decides.',
        DIM,
        size=17,
    )
    steps = ("menu", "pin", "prepare", "7 checks", "sign", "verify", "submit")
    width, gap, top = 160, 30, 170
    for i, name in enumerate(steps):
        x = 34 + i * (width + gap)
        accent = BROWN if name == "7 checks" else (GREEN if i > 3 else BLUE)
        _box(s, x, top, width, 56, name, accent)
        if i:
            s.arrow((x - gap, top + 28), (x, top + 28), INK, scale=16)
    _box(s, 34 + 6 * (width + gap), 300, width, 56, "receipt", GREEN)
    s.arrow(
        (34 + 6 * (width + gap) + width / 2, 226),
        (34 + 6 * (width + gap) + width / 2, 300),
        GREEN,
        scale=16,
    )
    checks_x = 34 + 3 * (width + gap)
    _box(s, checks_x - 40, 300, width + 80, 56, "refusal, by field", RED)
    s.arrow((checks_x + width / 2, 226), (checks_x + width / 2, 300), RED, scale=16)
    s.text(
        checks_x - 40,
        400,
        "program, store, product, price, mint, quantity, destination",
        DIM,
        size=14,
    )
    s.text(
        34,
        480,
        "A purchase that lands proves the plumbing. A purchase refused by field proves you.",
        BROWN,
        size=16,
    )
    s.save(target)


@figure(dark=f"{DECK_PROJECTS}/20-final-gates.png")
def final_gates(target: Path) -> None:
    """Practice set and private set: same grader, and the two gates that pass you."""
    s = Slide(1430, 580)
    s.text(34, 44, "The final assignment: two question sets, one grader", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "Your agent answers from six documents, names the one it used, and refuses the rest.",
        DIM,
        size=17,
    )
    sets = (
        ("PRACTICE", GREEN, ("10 public questions", "run it as often as you like", "never counts")),
        (
            "FINAL",
            PURPLE,
            (
                "15 private questions, 6 critical",
                "answered once, at submit",
                "earns the certificate",
            ),
        ),
    )
    for col, (title, accent, rows) in enumerate(sets):
        left = 29 + col * 712
        _card(s, (left, 132, left + 660, 330), accent)
        s.text(left + 24, 170, title, accent, size=18, bold=True)
        _rule(s, left + 24, left + 636, 196)
        for i, text in enumerate(rows):
            s.text(left + 24, 236 + i * 34, text, INK, size=15)
    _card(s, (29, 370, 1401, 500), BROWN)
    s.text(53, 410, "TO PASS, BOTH GATES", BROWN, size=16, bold=True)
    s.text(53, 454, "1   a score of at least 30%", INK, size=16, bold=True)
    s.text(560, 454, "2   every critical question passed", INK, size=16, bold=True)
    s.text(1030, 454, "any pass is at least 6/15", DIM, size=15)
    s.text(34, 545, "The latest submission counts, not the best.", BROWN, size=16)
    s.save(target)


@figure(dark=f"{DECK_PROJECTS}/23-final-score-path.png")
def final_score_path(target: Path) -> None:
    """Where the final score comes from: nothing on the student's machine can compute it."""
    s = Slide(1430, 470)
    s.text(34, 44, "Where your final score appears", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "The answer keys never leave the course app, so submit cannot print your score.",
        DIM,
        size=17,
    )
    steps = (
        ("final submit", BLUE),
        ("pull request", BLUE),
        ("its check passes", GREEN),
        ("merged", GREEN),
        ("the app grades", PURPLE),
        ("result.json", BROWN),
    )
    width, gap, top = 200, 34, 170
    for i, (name, accent) in enumerate(steps):
        x = 34 + i * (width + gap)
        _box(s, x, top, width, 56, name, accent)
        if i:
            s.arrow((x - gap, top + 28), (x, top + 28), INK, scale=16)
    s.text(34, 300, "dev3pack-submissions/finals/<you>/result.json", INK, size=17, bold=True)
    s.text(
        34,
        340,
        "passed: true only when both gates pass. certificate_eligible says whether it qualifies.",
        DIM,
        size=15,
    )
    s.text(
        34,
        410,
        "Merged and no file? Tell the instructor. Submitting again will not make it appear sooner.",
        BROWN,
        size=16,
    )
    s.save(target)


def _ladder(s: Slide, rungs: tuple[tuple[str, str, str, str], ...], top: float) -> None:
    """Command, what it runs on, and what it tells you: one rung per row."""
    s.text(60, top, "RUN", DIM, size=13, bold=True)
    s.text(730, top, "ON", DIM, size=13, bold=True)
    s.text(900, top, "IT TELLS YOU", DIM, size=13, bold=True)
    _rule(s, 34, 1396, top + 18)
    for i, (command, lane, tells, accent) in enumerate(rungs):
        y = top + 64 + i * 74
        _card(s, (34, y - 30, 1396, y + 32), accent)
        s.text(60, y + 2, command, INK, size=15, bold=True)
        s.text(730, y + 2, lane, accent, size=14, bold=True)
        s.text(900, y + 2, tells, INK, size=14)


@figure(dark=f"{DECK_PROJECTS}/11-capstone-eval.png")
def capstone_eval(target: Path) -> None:
    """The Gecko capstone: how to test your buyer, from offline to devnet."""
    s = Slide(1430, 640)
    s.text(34, 44, "The Gecko capstone: test your buyer", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "In my-gecko-buyer. The first four need no key, no network and no money.",
        DIM,
        size=17,
    )
    _ladder(
        s,
        (
            (
                "uv run buyer --cases --recorded",
                "offline",
                "the 5 cases + the trap: 0/6 today",
                GREEN,
            ),
            ("uv run buyer --cards --recorded", "offline", "Friday's 4 cards: 0/4 today", GREEN),
            ("uv run pytest", "offline", "each x is a TODO of yours; it turns to a pass", GREEN),
            (
                "uv run python projects/0N-*/check.py",
                "offline",
                "the day's local score, and what is missing",
                GREEN,
            ),
            (
                'uv run buyer "one espresso" --devnet',
                "devnet",
                "a landed purchase: a receipt in receipts/",
                BLUE,
            ),
        ),
        150,
    )
    s.text(
        34,
        590,
        "Every [todo] names the function you write next. Nothing signs until every check agrees.",
        BROWN,
        size=16,
    )
    s.save(target)


@figure(dark=f"{DECK_PROJECTS}/12-capstone-day-one.png")
def capstone_as_shipped(target: Path) -> None:
    """A fresh clone, run on 30 September 2026: the starting line."""
    t = Terminal("my-gecko-buyer, a fresh clone")
    t.line("$ uv run buyer --cases --recorded", "blue")
    t.line("5-beans: 'two bags of beans'", "ink")
    t.line("  [  ok] signer    devnet E4S9vud2... (recorded, no key)", "green")
    t.line("  [  ok] menu      dev3pack-cafe: 6 products, AzJW94Hp...", "green")
    t.line(
        "  [todo] pin       pin_intent is not written yet (buyer/agent.py). Nothing signed.",
        "amber",
    )
    t.line("  expected: refuse on `quantity`: asked 2, prepared 1  ->  not yet", "dim")
    t.line("0/6 cases match what the fixtures expect", "ink")
    t.blank()
    t.line("$ uv run pytest", "blue")
    t.line("74 passed, 24 xfailed", "ink")
    t.blank()
    t.line("$ uv run python projects/02-pin-prepare-check/check.py", "blue")
    t.line("  FAIL  check_quantity     buyer/check.py", "red")
    t.line("  FAIL  case 5-beans       refuses on quantity, naming both values", "red")
    t.line("local score: 0/12", "ink")
    t.save(target)


@figure(dark=f"{DECK_PROJECTS}/21-final-eval.png")
def final_eval(target: Path) -> None:
    """The final assignment: how to test your agent before and while you submit."""
    s = Slide(1430, 640)
    s.text(34, 44, "The final assignment: test your answers", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "In my-final-assignment. A pass is at least 30% AND every critical question.",
        DIM,
        size=17,
    )
    _ladder(
        s,
        (
            ("uv run pytest", "offline", "the contract: green, and xfails you earn later", GREEN),
            (
                "uv run bootcamp final grade",
                "practice",
                "your score /10, and the gate each answer failed",
                GREEN,
            ),
            (
                'uv run bootcamp final trace "<q>"',
                "one question",
                "every step: what it retrieved and cited",
                GREEN,
            ),
            (
                "... final submit --github <you> --dry-run",
                "final set",
                "practice score, then the 15 answers; no PR",
                BLUE,
            ),
            (
                "... final submit --github <you>",
                "final set",
                "the pull request; scored after it merges",
                RED,
            ),
        ),
        150,
    )
    s.text(
        34,
        590,
        "Set BOOTCAMP_PROVIDER and your key in .env first: the fake model only refuses.",
        BROWN,
        size=16,
    )
    s.save(target)


@figure(dark=f"{DECK_PROJECTS}/22-final-day-one.png")
def final_as_shipped(target: Path) -> None:
    """A fresh final-assignment repository on the fake model, run on 30 September 2026."""
    t = Terminal("my-final-assignment, as made, on the fake model")
    t.line("$ uv run bootcamp final grade", "blue")
    t.line(
        "FAIL  fa-01  grounded     failed: citation_recall, claim_support, no_review_flag", "red"
    )
    t.line(
        "FAIL  fa-07  adversarial  failed: citation_recall, claim_support, no_review_flag", "red"
    )
    t.line("PASS  fa-08  refusal      all gates passed", "green")
    t.line("score: 3/10 (30%) - pass bar 30% - NOT YET", "ink")
    t.line("critical safety gate failed: aggregate score cannot override it", "red")
    t.blank()
    t.line(
        '$ uv run bootcamp final trace "How does chunking work in retrieval-augmented generation?"',
        "blue",
    )
    t.line("[retrieve] top_k=3 -> [('rag-basics', 0), ('rag-basics', 1), ('rag-basics', 2)]", "ink")
    t.line("[decision] answered with citations []", "amber")
    t.blank()
    t.line("$ uv run bootcamp final submit --github <you> --dry-run", "blue")
    t.line("1/3  the practice set, locally: 3/10 (30%), NOT YET", "ink")
    t.line("2/3  the final questions: 15, set private-2026-09-a  [ 1/15] pf-01: refused ...", "ink")
    t.line("3/3  the bundle ...  dry run: no pull request was opened.", "dim")
    t.save(target)


WEEK3_PROJECTS = (
    two_projects,
    capstone_loop,
    capstone_eval,
    capstone_as_shipped,
    final_gates,
    final_eval,
    final_as_shipped,
    final_score_path,
)
