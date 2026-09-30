"""Session 13's figures: a guard decides on the string, on every hop, by three rules in order.

Two render light for the course page and dark for the deck (the session 8 pattern): the
guard before the socket, and the redirect. The rest are dark, for the deck only.

The terminal cards print output that was RUN on 29 September 2026: the notebook as
shipped, and the instructor's finished notebook (its output only; no solution code is
shown). Change one only by running it again.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.patches import FancyBboxPatch

from .slide import SLIDE_EDGE, SLIDE_ROUND, Slide
from .terminal import Terminal
from .theme import DECK_13, LIGHT, UNIT_13, figure, install, palette

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


@figure(
    light=f"{UNIT_13}/guard-before-the-socket.png", dark=f"{DECK_13}/01-guard-before-the-socket.png"
)
def guard_before_the_socket(target: Path) -> None:
    """A check after the request has already fetched; a guard decides on the string."""
    s = Slide(1430, 640)
    s.text(34, 44, "Decide on the string, before the socket opens", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "The URL arrives from whatever text reached the model. By the time a response "
        "exists, it is too late to refuse.",
        DIM,
        size=17,
    )

    _card(s, (29, 132, 689, 500), RED)
    s.text(53, 166, "CHECKED AFTER THE REQUEST", RED, size=16, bold=True)
    _rule(s, 53, 665, 192)
    steps = (
        "read_page(url)",
        "the request leaves",
        "the inside service answers",
        "the answer is in context",
    )
    for i, text in enumerate(steps):
        _box(s, 90, 214 + i * 64, 330, 48, text, RED if i >= 2 else INK)
        if i:
            s.arrow((255, 214 + i * 64 - 16), (255, 214 + i * 64), RED, scale=16)
    s.text(450, 424, "the check says no:", INK, size=15, bold=True)
    s.text(450, 452, "too late", RED, size=17, bold=True)

    _card(s, (741, 132, 1401, 500), GREEN)
    s.text(765, 166, "CHECKED ON THE STRING", GREEN, size=16, bold=True)
    _rule(s, 765, 1377, 192)
    _box(s, 800, 214, 330, 48, "read_page(url)", INK)
    s.arrow((965, 262), (965, 294), GREEN, scale=16)
    _box(s, 800, 294, 330, 48, "fetch_guard(url)", GREEN)
    s.arrow((965, 342), (965, 374), GREEN, scale=16)
    _box(s, 800, 374, 330, 48, "refused, with a code", GREEN)
    s.text(1160, 318, "no socket,", DIM, size=14)
    s.text(1160, 344, "no DNS", DIM, size=14)
    s.text(800, 456, "nothing left the machine", GREEN, size=16, bold=True)

    s.text(
        34,
        560,
        "A guard is a function of a string. That is why the whole lab runs with the "
        "network unplugged.",
        BROWN,
        size=16,
    )
    s.save(target)


@figure(light=f"{UNIT_13}/every-hop.png", dark=f"{DECK_13}/02-every-hop.png")
def every_hop(target: Path) -> None:
    """A redirect: the first URL was fine, the third hop was the point."""
    s = Slide(1430, 620)
    s.text(34, 44, "The guard runs on every hop", INK, size=26, bold=True)
    s.text(
        34,
        86,
        "A public host answers 302 and names the next hop. Nothing about the first URL was wrong.",
        DIM,
        size=17,
    )
    hops = (
        "https://docs.example.com/spec",
        "https://example.com/v2/spec",
        "http://169.254.169.254/latest/meta-data/",
    )
    for col, (title, accent, stops_at) in enumerate(
        (("GUARD ONCE", RED, None), ("GUARD EVERY HOP", GREEN, 2))
    ):
        left = 29 + col * 712
        _card(s, (left, 132, left + 660, 480), accent)
        s.text(left + 24, 166, title, accent, size=16, bold=True)
        _rule(s, left + 24, left + 636, 192)
        for i, hop in enumerate(hops):
            y = 226 + i * 76
            checked = col == 1 or i == 0
            if stops_at is not None and i > stops_at:
                break
            refused = stops_at == i
            mark = "REFUSE" if refused else ("ALLOW" if checked else "not checked")
            colour = RED if refused else (GREEN if checked else DIM)
            s.text(left + 30, y, f"hop {i + 1}", INK, size=15, bold=True)
            s.text(left + 110, y, hop, INK, size=14)
            s.text(left + 110, y + 26, mark, colour, size=14, bold=True)
        if col == 0:
            s.text(
                left + 30,
                450,
                "hop 3 is fetched, and its answer reaches the model",
                RED,
                size=14,
                bold=True,
            )
        else:
            s.text(left + 30, 450, "stopped: not-public", GREEN, size=14, bold=True)
    s.text(
        34,
        540,
        "Guard every hop, and cap the number of hops.",
        BROWN,
        size=16,
    )
    s.save(target)


@figure(dark=f"{DECK_13}/03-three-rules.png")
def three_rules(target: Path) -> None:
    """Scheme, address, allowlist: the first rule that fires decides, and names itself."""
    s = Slide(1430, 560)
    s.text(34, 44, "Three rules, in this order", INK, size=26, bold=True)
    s.text(
        34, 86, "The first one that fires decides. The reason starts with its code.", DIM, size=17
    )
    rules = (
        ("1  scheme", "only http and https", "scheme", BLUE),
        ("2  address", "a host that IS an address must be public", "not-public", RED),
        ("3  allowlist", "a declared domain, or its subdomain", "not-allowlisted", PURPLE),
    )
    for i, (name, what, code, accent) in enumerate(rules):
        left = 29 + i * 468
        _card(s, (left, 140, left + 440, 360), accent)
        s.text(left + 24, 180, name, accent, size=20, bold=True)
        s.text(left + 24, 230, what, INK, size=14)
        s.text(left + 24, 300, "code:", DIM, size=13)
        s.text(left + 90, 300, code, accent, size=16, bold=True)
        if i < 2:
            s.arrow((left + 440, 250), (left + 468, 250), INK, scale=18)
    s.text(
        34,
        420,
        "Why the order is graded: the address rule survives the day the allowlist is widened,",
        BROWN,
        size=16,
    )
    s.text(
        34,
        452,
        "and 'not-allowlisted' for an inside address sends the next person to fix the wrong thing.",
        BROWN,
        size=16,
    )
    s.save(target)


@figure(dark=f"{DECK_13}/04-as-shipped.png")
def as_shipped(target: Path) -> None:
    """Section 1, and the check before anything is written."""
    t = Terminal("section 1, then bootcamp check ch13, as shipped")
    t.line("read_page takes ['url']", "ink")
    t.line("read-only: True", "ink")
    t.line("allowed hosts: example.com, docs.python.org (and their subdomains)", "ink")
    t.blank()
    t.line("$ uv run bootcamp check ch13", "blue")
    t.line("ch13: 0/3 passed", "ink")
    t.wrapped(
        "✘ ch13-e4: https://example.com/pricing was refused ('not-allowlisted: no rules "
        "written yet'), and it has to be allowed. ... A guard that refuses everything is "
        "not a guard, it is an outage."
    )
    t.save(target)


@figure(dark=f"{DECK_13}/05-probes.png")
def probes(target: Path) -> None:
    """The six probes through a finished guard (the instructor's run; output only)."""
    t = Terminal("section 2, with a finished guard")
    for verdict, url, reason, colour in (
        ("ALLOW ", "https://example.com/pricing", "example.com is on the allowlist", "green"),
        (
            "ALLOW ",
            "https://api.example.com/v1/status",
            "api.example.com is on the allowlist",
            "green",
        ),
        ("REFUSE", "http://169.254.169.254/latest/meta-data/", "not-public: ...", "red"),
        ("REFUSE", "http://2130706433/", "not-public: ... is 127.0.0.1", "red"),
        ("REFUSE", "https://evil-example.com/spec.json", "not-allowlisted: ...", "red"),
        ("REFUSE", "file:///etc/passwd", "scheme: file is not http or https", "red"),
    ):
        t.line(f"{verdict} {url:42} {reason}", colour)
    t.blank()
    t.line("✔ ch13-e4 passed", "green")
    t.save(target)


@figure(dark=f"{DECK_13}/06-redirect-walk.png")
def redirect_walk(target: Path) -> None:
    """Section 3's recorded chain through a finished guard."""
    t = Terminal("section 3, the redirect, one hop at a time")
    t.line("hop 1: ALLOW   https://docs.example.com/spec", "green")
    t.line("hop 2: ALLOW   https://example.com/v2/spec", "green")
    t.line("hop 3: REFUSE  http://169.254.169.254/latest/meta-data/", "red")
    t.line("         stopped: not-public: 169.254.169.254 is not a public address", "red")
    t.save(target)


SESSION_13 = (
    guard_before_the_socket,
    every_hop,
    three_rules,
    as_shipped,
    probes,
    redirect_walk,
)
