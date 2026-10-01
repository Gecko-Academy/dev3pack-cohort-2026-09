"""Session 14's figures: a smoke test that can say "bad", and a way back you have run.

Two render light for the course page and dark for the deck: the four deployments, and
rosy against the report. The rest are dark, for the deck only.

The terminal cards print output that was RUN on 30 September 2026: the session notebook
as shipped, demo 14, and the Gecko capstone's `make smoke` (live on devnet) and
`make smoke-recorded`, run by the instructor with a reference buyer (its output only; no
solution code is shown). Change one only by running it again.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.patches import FancyBboxPatch

from .slide import SLIDE_EDGE, SLIDE_ROUND, Slide
from .terminal import Terminal
from .theme import DECK_14, LIGHT, UNIT_14, figure, install, palette

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


@figure(light=f"{UNIT_14}/four-deployments.png", dark=f"{DECK_14}/01-four-deployments.png")
def four_deployments(target: Path) -> None:
    """The same three facts about four deployments, as section 2 prints them."""
    s = Slide(1430, 600)
    s.text(34, 44, "Four deployments, seen from outside", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "The same call shape. What the first call costs, what /health says, and what a "
        "body with a typo gets back.",
        DIM,
        size=17,
    )
    rows = (
        ("warm", "30 ms", "200", "400 refused", GREEN, "the one you hope for"),
        ("cold", "1900 ms", "200", "400 refused", BROWN, "the cold start"),
        ("lax", "70 ms", "200", "200 'Yes, that is correct.'", RED, "stopped validating"),
        ("killed", "110 ms", "503", "503 memory limit", RED, "the resource limit"),
    )
    heads = (
        (60, "DEPLOYMENT"),
        (250, "FIRST CALL"),
        (440, "/health"),
        (590, "MALFORMED BODY"),
        (1050, "THE FAILURE"),
    )
    for x, head in heads:
        s.text(x, 150, head, DIM, size=13, bold=True)
    _rule(s, 34, 1396, 168)
    for i, (kind, first, health, malformed, accent, failure) in enumerate(rows):
        y = 214 + i * 78
        _card(s, (34, y - 32, 1396, y + 32), accent)
        s.text(60, y + 2, kind, accent, size=17, bold=True)
        s.text(250, y + 2, first, INK, size=15)
        s.text(440, y + 2, health, RED if health != "200" else INK, size=15)
        s.text(590, y + 2, malformed, RED if malformed.startswith(("200", "503")) else INK, size=15)
        s.text(1050, y + 2, failure, DIM, size=14)
    s.text(
        34,
        560,
        "lax answers /health with 200. Only the probe nobody sends first catches it.",
        BROWN,
        size=16,
    )
    s.save(target)


@figure(light=f"{UNIT_14}/rosy-vs-report.png", dark=f"{DECK_14}/02-rosy-vs-report.png")
def rosy_vs_report(target: Path) -> None:
    """The lax deployment, judged by rosy and by a report that can say bad."""
    s = Slide(1430, 600)
    s.text(34, 44, "A test that can only pass measures nothing", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "The lax deployment, which answers garbage with 200, through two smoke tests.",
        DIM,
        size=17,
    )
    panels = (
        (
            "ROSY: DID ANYTHING ANSWER?",
            RED,
            (
                ("probes sent", "/health, one good question"),
                ("malformed_rejected", "True"),
                ("healthy", "True"),
                ("cold_start_ms", "0"),
            ),
            "green, and wrong: it never sent the bad body",
        ),
        (
            "THE REPORT: WHAT DID IT DO?",
            GREEN,
            (
                ("probes sent", "/health, a question, a bad body"),
                ("malformed_rejected", "False"),
                ("healthy", "False"),
                ("cold_start_ms", "70"),
            ),
            "bad news, reported as bad news",
        ),
    )
    for col, (title, accent, rows, verdict) in enumerate(panels):
        left = 29 + col * 712
        _card(s, (left, 132, left + 660, 500), accent)
        s.text(left + 24, 166, title, accent, size=16, bold=True)
        _rule(s, left + 24, left + 636, 192)
        for i, (field, value) in enumerate(rows):
            y = 236 + i * 56
            s.text(left + 30, y, field, DIM, size=14, bold=True)
            s.text(left + 260, y, value, INK, size=15)
        s.text(left + 30, 466, verdict, accent, size=15, bold=True)
    s.text(
        34,
        556,
        "Same deployment. One bit of output, spent on the thing least likely to be wrong.",
        BROWN,
        size=16,
    )
    s.save(target)


@figure(dark=f"{DECK_14}/03-the-report.png")
def the_report(target: Path) -> None:
    """The four fields, and what a wrong value in each would hide."""
    s = Slide(1430, 560)
    s.text(34, 44, "The report: four fields, each allowed to be bad", INK, size=26, bold=True)
    s.text(34, 86, "smoke(request) -> dict. The check holds you to each one.", DIM, size=17)
    fields = (
        ("cold_start_ms", "the FIRST call's elapsed_ms", "the 1.9 s every first caller pays", BLUE),
        ("malformed_rejected", "the bad body came back 4xx", "a deployment inventing answers", RED),
        ("healthy", "/health, an answer, a refusal", "serving vs serving correctly", GREEN),
        ("rollback", "an action, a number, a unit", "no plan at 16:40", PURPLE),
    )
    for i, (name, true_when, hides, accent) in enumerate(fields):
        left = 29 + i * 352
        _card(s, (left, 140, left + 330, 440), accent)
        s.text(left + 20, 180, name, accent, size=17, bold=True)
        s.text(left + 20, 230, "true when", DIM, size=13, bold=True)
        s.text(left + 20, 262, true_when, INK, size=13)
        s.text(left + 20, 330, "a wrong value hides", DIM, size=13, bold=True)
        s.text(left + 20, 362, hides, INK, size=13)
    s.text(34, 500, "Send all three probes, whatever the first one answers.", BROWN, size=16)
    s.save(target)


@figure(dark=f"{DECK_14}/04-as-shipped.png")
def as_shipped(target: Path) -> None:
    """Section 3 as shipped, and the check."""
    t = Terminal("section 3, then bootcamp check ch14, as shipped")
    for kind in ("warm", "cold", "lax", "killed"):
        t.line(
            f"{kind:7} {{'cold_start_ms': 0, 'malformed_rejected': False, 'healthy': False, "
            "'rollback': ''}",
            "ink",
        )
    t.blank()
    t.line("$ uv run bootcamp check ch14", "blue")
    t.line("ch14: 0/1 passed", "ink")
    t.wrapped(
        "✘ ch14-e3: the warm deployment: you never sent a well-formed question to "
        "'/answer'; hint: 'healthy' means it served a real request, so send one"
    )
    t.save(target)


@figure(dark=f"{DECK_14}/05-the-way-back.png")
def the_way_back(target: Path) -> None:
    """Demo 14's output: the same incident, two rollback plans."""
    t = Terminal("demo 14: v2 ships at 16:40, the malformed probe fires")
    t.line("the probe, against each release: {'v1': 400, 'v2': 200}", "ink")
    t.blank()
    t.line("plan A: If something breaks, roll back to the previous version.", "ink")
    t.line(
        "plan B: If the malformed probe returns 200, ship the previous version "
        "(`ship(previous)`): under 60 s.",
        "ink",
    )
    t.blank()
    t.line("plan A, the sentence  detected: True  still on v2    after 30.0 min", "red")
    t.line("plan B, the command   detected: True  back on v1     after 0.5 min", "green")
    t.save(target)


@figure(dark=f"{DECK_14}/06-capstone-smoke.png")
def capstone_smoke(target: Path) -> None:
    """The Gecko capstone's smoke, live on devnet, and its rollback, recorded."""
    t = Terminal("my-gecko-buyer: make smoke (devnet), then make smoke-recorded")
    t.line("$ make smoke", "blue")
    t.line("1-espresso: 'one espresso'", "ink")
    t.line("  expected: landed  ->  MATCH", "green")
    t.line("5-beans: 'two bags of beans'", "ink")
    t.line("  [  NO] check     REFUSED on quantity: asked 2, prepared 1", "red")
    t.line("  expected: refuse on `quantity`: asked 2, prepared 1  ->  MATCH", "green")
    t.line("# cases 2, 3, 4 and 6 refuse on product, mint, price_raw, price_raw: MATCH", "dim")
    t.line("6/6 cases match what the fixtures expect", "ink")
    t.line("# 25 s, live on devnet", "dim")
    t.blank()
    t.line("$ make smoke-recorded", "blue")
    t.line("GECKO_SOURCE=recorded uv run buyer --cases --json smoke-report.recorded.json", "dim")
    t.line("6/6 cases match what the fixtures expect", "ink")
    t.save(target)


@figure(dark=f"{DECK_14}/07-friday-ladder.png")
def friday_ladder(target: Path) -> None:
    """Friday's fallback ladder: step down, and say so."""
    s = Slide(1430, 560)
    s.text(34, 44, "Friday: the way back, written today", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "If a lane fails at minute 1:30, step down one rung and say which rung you are on.",
        DIM,
        size=17,
    )
    rungs = (
        ("mainnet", "finalists, funded wallet", "--mainnet --store geckocoffee", PURPLE),
        ("devnet, your store", "everyone", '"one espresso" --devnet', GREEN),
        (
            "devnet, class store",
            "your store is broken",
            "--store dev3pack-cafe --mint Eoqdd...",
            BLUE,
        ),
        ("recorded", "network or Gecko down", "GECKO_SOURCE=recorded ... --devnet", BROWN),
    )
    for i, (name, who, command, accent) in enumerate(rungs):
        y = 160 + i * 84
        _card(s, (34 + i * 40, y - 32, 1396, y + 32), accent)
        s.text(60 + i * 40, y + 2, name, accent, size=17, bold=True)
        s.text(460, y + 2, who, DIM, size=14)
        s.text(770, y + 2, command, INK, size=14)
    s.text(
        34,
        520,
        "A step down costs nothing when it is named. A replay presented as live is the one fail.",
        BROWN,
        size=16,
    )
    s.save(target)


SESSION_14 = (
    four_deployments,
    rosy_vs_report,
    the_report,
    as_shipped,
    the_way_back,
    capstone_smoke,
    friday_ladder,
)
