"""The palette, and where a rendering of a figure is allowed to land.

Two renderings of one drawing: the course page is light, the deck is dark. The
drawing is written once and `figure` decides both the palette and the file.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from pathlib import Path

import matplotlib

# Chosen here, before any module imports pyplot: a backend that wants a display
# turns a headless render into a crash rather than a PNG.
matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[2]
# The light figures the course pages link by raw GitHub URL, and the dark deck
# they are re-rendered into. A light path never moves.
UNIT_08 = "units/en/unit2/session-08-loops-and-graphs/img"
DECK_08 = "docs/instructor/sessions/session-08-loops-and-graphs/img"
# Decks with no course page behind them: these figures are dark only.
DECK_04 = "docs/instructor/sessions/session-04-bounded-tools/img"
DECK_05 = "docs/instructor/sessions/session-05-deterministic-mini-agent/img"
DECK_06 = "docs/instructor/sessions/session-06-retrieval-baseline/img"
DECK_07 = "docs/instructor/sessions/session-07-grounding-metrics/img"
DECK_09 = "docs/instructor/sessions/session-09-trace-and-evaluate/img"


@dataclass(frozen=True)
class Theme:
    """One drawing, two renderings: the course page is light, the deck is dark.

    A figure is written once and rendered under either theme. The light values
    must stay exactly what they have always been: the course pages link their
    PNGs by raw GitHub URL, so a light file that moves is a broken page.
    """

    name: str
    ink: str  # primary text, and every icon outline
    dim: str  # secondary text, arrows, dashed paths
    line: str  # panel borders
    page: str  # figure background, and the savefig facecolor
    panel: str  # panel fill
    blue: str
    green: str
    brown: str
    purple: str
    red: str
    tint: dict[str, str]  # accent -> box fill, keyed by THIS theme's own accents
    tab_ink: str  # text printed on top of an accent fill
    badge_face: str
    badge_edge: str

    def target(self, light: Path | None, dark: Path | None) -> Path | None:
        """Where this rendering is written. Nothing else may choose the path."""
        return light if self.name == "light" else dark


LIGHT = Theme(
    name="light",
    ink="#1f2937",
    dim="#5b6472",
    line="#c9ced6",
    page="#ffffff",
    panel="#fbfcfd",
    blue="#2f5f9e",
    green="#2f7a4f",
    brown="#8c5a24",
    purple="#5a4696",
    red="#c2413b",
    tint={
        "#2f5f9e": "#e8eef8",
        "#2f7a4f": "#e6f2ea",
        "#8c5a24": "#f7ede0",
        "#5a4696": "#ece8f6",
        "#c2413b": "#fbe9e8",
    },
    tab_ink="white",
    badge_face="#f5c518",
    badge_edge="#1f2937",
)

# Sampled from the deck itself: the navy ground and the cyan/green/yellow of
# session 7's road. The dark accents are brighter than the light ones because a
# #2f5f9e box on a near-black ground is unreadable.
DARK = Theme(
    name="dark",
    ink="#e5e7eb",
    dim="#8b97ab",
    line="#2a3446",
    page="#0b1220",
    panel="#111a2c",
    blue="#22d3ee",
    green="#22c55e",
    brown="#facc15",  # the yellow accent takes brown's slot on dark
    purple="#a78bfa",
    red="#f87171",
    tint={
        "#22d3ee": "#0f2530",
        "#22c55e": "#102a1c",
        "#facc15": "#2a2410",
        "#a78bfa": "#1d1a33",
        "#f87171": "#2d1718",
    },
    tab_ink="#0b1220",
    badge_face="#facc15",
    badge_edge="#0b1220",
)

#: The names every drawing primitive reads, in the order `palette` returns them.
_NAMES = (
    "INK",
    "DIM",
    "LINE",
    "PAGE",
    "PANEL",
    "BLUE",
    "GREEN",
    "BROWN",
    "PURPLE",
    "RED",
    "TINT",
    "TAB_INK",
    "BADGE_FACE",
    "BADGE_EDGE",
)


_PALETTES: list[dict[str, object]] = []


def palette(theme: Theme) -> tuple[object, ...]:
    """This theme's values, in `_NAMES` order. The one place that order is fixed."""
    return (
        theme.ink,
        theme.dim,
        theme.line,
        theme.page,
        theme.panel,
        theme.blue,
        theme.green,
        theme.brown,
        theme.purple,
        theme.red,
        theme.tint,
        theme.tab_ink,
        theme.badge_face,
        theme.badge_edge,
    )


def install(namespace: dict[str, object]) -> None:
    """Register a drawing module, so `use_theme` repaints its palette too.

    Every primitive reads INK, PAGE and the accents as plain module globals.
    Once the drawings live in more than one module each needs its own copy kept
    in step, or a figure drawn dark quietly borrows a light colour from
    whichever module it happens to be written in.
    """
    namespace.update(dict(zip(_NAMES, palette(LIGHT), strict=True)))
    _PALETTES.append(namespace)


@contextmanager
def use_theme(theme: Theme) -> Iterator[Theme]:
    """Draw under one palette, then put the previous one back.

    `TINT` stays per-theme on purpose: a figure that reaches past this and names
    a foreign accent raises KeyError instead of quietly drawing the wrong fill.
    """
    values = palette(theme)
    previous = [[namespace[name] for name in _NAMES] for namespace in _PALETTES]
    for namespace in _PALETTES:
        namespace.update(dict(zip(_NAMES, values, strict=True)))
    try:
        yield theme
    finally:
        for namespace, before in zip(_PALETTES, previous, strict=True):
            namespace.update(dict(zip(_NAMES, before, strict=True)))


def figure(light: str | None = None, dark: str | None = None) -> Callable[..., Callable[..., None]]:
    """Turn a drawing into a figure that can be rendered under either theme.

    The drawing itself is written once and receives only where to save. The
    theme decides the palette and the destination together, so a dark rendering
    can never land on a light file's path.
    """

    def decorate(draw: Callable[[Path], None]) -> Callable[..., None]:
        @wraps(draw)
        def render(theme: Theme = LIGHT) -> None:
            relative = theme.target(Path(light) if light else None, Path(dark) if dark else None)
            if relative is None:
                raise ValueError(f"{draw.__name__} has no {theme.name} rendering")
            with use_theme(theme):
                draw(ROOT / relative)

        return render

    return decorate


# The active palette. Switching theme is one rebinding rather than 94 edits, and
# a module that forgets to register cannot half-switch: it never switches at all.
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
