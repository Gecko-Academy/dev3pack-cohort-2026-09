"""The analyst team's tools, as a package the notebook writes and then imports.

A folder becomes a package when it holds an `__init__.py`. That file is what runs
on `import analyst_tools`, and it is the only place that decides what the name
means to everybody else.

One module per tool, because a tool is a contract and a contract deserves a file
you can read in one sitting. `build_registry` is the only thing a caller needs:
name -> Tool, which is the shape session 4's `build_tools` already returns.
"""

from __future__ import annotations

from bootcamp_agent.projects.analyst_team import Searcher
from bootcamp_agent.tools import Tool, ToolError

from . import companies, filings

__all__ = ["Tool", "ToolError", "build_registry", "companies", "filings"]


def build_registry(
    search: Searcher, tickers: dict[str, str], *, include_web: bool = False
) -> dict[str, Tool]:
    """name -> Tool. `include_web` adds the one tool that leaves the machine.

    The web tool is opt-IN. A registry is an allow-list, and an allow-list that
    grows by itself is not one. It is also imported here rather than at the top of
    the file, so this package works before `web.py` exists: step 9 writes two tools
    and step 10 writes the third.
    """
    registry = {
        "search_filings": filings.build(search, tickers),
        "list_companies": companies.build(tickers),
    }
    if include_web:
        from . import web

        registry["web_search"] = web.build()
    return registry
