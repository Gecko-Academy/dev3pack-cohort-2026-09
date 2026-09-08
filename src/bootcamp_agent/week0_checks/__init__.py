"""Checkers for Week 0, the prerequisite track.

Importing this package registers every week-0 exercise into `CHECKS`, which is
what `check()`, `review("wNN")` and `curriculum.unit_exercise_ids` rely on. One
module per track, so a course can grow without one file swallowing the rest:

  fast_lane             units 1-4, the floor session 1 assumes
  software_engineering  units 5-6, packages, PyPI, PEP 8, portability
  software_engineering_classes
                        units 7-8, classes, docs, tests, readability
  mcp_course            units 9-10, an MCP server, its client, and the loop around an LLM
  mcp_course_integrations
                        unit 11, databases, APIs and third-party servers
  dsa                   unit 12, the data structures an agent loop is made of

A submodule that does not exist yet is simply not imported; add the import line
when the course lands.
"""

from __future__ import annotations

from bootcamp_agent.week0_checks import (
    dsa,  # noqa: F401
    fast_lane,  # noqa: F401 - registration side effect
    mcp_course,  # noqa: F401
    mcp_course_integrations,  # noqa: F401
    software_engineering,  # noqa: F401
    software_engineering_classes,  # noqa: F401
)
