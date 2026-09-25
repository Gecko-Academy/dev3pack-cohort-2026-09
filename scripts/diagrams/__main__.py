"""Render every figure, light and dark.

uv run --extra projects python scripts/diagrams
"""

from __future__ import annotations

import sys
from pathlib import Path

# Run as a path, Python puts THIS directory on the import path rather than its
# parent, so the package cannot find itself by name. Point at the parent and
# import by name; `python -m diagrams` arrives the same way.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from diagrams import (  # noqa: E402
    DARK,
    SESSION_04,
    SESSION_05,
    SESSION_06,
    SESSION_07,
    SESSION_09,
    SESSION_10,
    capstone,
    loop_vs_graph,
    model_rag_agent_team,
    project_02,
    rag_family,
    road,
    vector_indexes,
)


def main() -> None:
    model_rag_agent_team()
    project_02()
    capstone()
    for both in (loop_vs_graph, rag_family, vector_indexes):
        both()
        both(DARK)
    for dark_only in SESSION_04 + SESSION_05 + SESSION_06 + SESSION_07 + SESSION_09 + SESSION_10:
        dark_only(DARK)
    # one road per session day: the badge moves, the geometry does not
    road(7)
    road(8)
    road(9)
    road(10)


if __name__ == "__main__":
    main()
