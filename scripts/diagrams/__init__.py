"""Every course diagram, drawn in one style: a panel per idea, icons, labelled arrows.

    uv run --extra projects python scripts/diagrams

Each diagram is our own drawing of the course's own parts. Re-run after changing
a number the pictures quote; the numbers are written next to where they came from.

One drawing, two renderings: the course pages are light, the decks are dark.
`theme` owns the palette and decides where a rendering may land, `canvas`,
`terminal` and `slide` are the three ways of drawing, and every other module is
one session's figures. Everything a caller used when this was a single file is
re-exported here, so `import diagrams` still reaches all of it.
"""

from __future__ import annotations

from .architecture import capstone, model_rag_agent_team, project_02
from .canvas import Canvas
from .road import ROAD_CHECKS, ROAD_SESSIONS, ROAD_TODAY_FILL, ROAD_WEEKS, road
from .session_04 import SESSION_04
from .session_05 import SESSION_05
from .session_06 import SESSION_06
from .session_07 import SESSION_07
from .session_08 import loop_vs_graph, rag_family, vector_indexes
from .session_09 import SESSION_09
from .slide import Slide
from .terminal import Terminal
from .theme import (
    DARK,
    DECK_04,
    DECK_05,
    DECK_06,
    DECK_07,
    DECK_08,
    LIGHT,
    ROOT,
    UNIT_08,
    Theme,
    figure,
    install,
    palette,
    use_theme,
)

# Registered last so `diagrams.PAGE` follows `use_theme` the way it did when
# every drawing lived in this one namespace.
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

__all__ = [
    "DARK",
    "DECK_04",
    "DECK_05",
    "DECK_06",
    "DECK_07",
    "DECK_08",
    "LIGHT",
    "ROAD_CHECKS",
    "ROAD_SESSIONS",
    "ROAD_TODAY_FILL",
    "ROAD_WEEKS",
    "ROOT",
    "SESSION_04",
    "SESSION_05",
    "SESSION_06",
    "SESSION_07",
    "SESSION_09",
    "UNIT_08",
    "Canvas",
    "Slide",
    "Terminal",
    "Theme",
    "capstone",
    "figure",
    "install",
    "loop_vs_graph",
    "model_rag_agent_team",
    "palette",
    "project_02",
    "rag_family",
    "road",
    "use_theme",
    "vector_indexes",
]
