"""The local tool: project 02's filings index, held to one company on request.

Written by step 9 of the notebook. Read it there first; this file is the copy
that survives the kernel restart.
"""

from __future__ import annotations

from bootcamp_agent.projects.analyst_team import Passage, Searcher
from bootcamp_agent.tools import MAX_SEARCH_RESULTS, Tool, ToolError


def build(search: Searcher, tickers: dict[str, str]) -> Tool:
    """Wrap the notebook's `search` as a Tool, with the contract session 4 asks for."""

    def search_filings(query: str, ticker: str | None = None, k: int = 4) -> list[Passage]:
        """Search the eight 10-K filings for passages. `ticker` holds it to one company."""
        if not query or not query.strip():
            raise ToolError("search_filings: 'query' must be a non-empty string")
        if ticker is not None and ticker not in tickers:
            raise ToolError(f"search_filings: unknown ticker {ticker!r}; valid: {sorted(tickers)}")
        capped = max(1, min(int(k), MAX_SEARCH_RESULTS))
        return search(query, ticker, capped)

    return Tool(
        name="search_filings",
        description=(
            "Search eight companies' Form 10-K risk factors for passages that answer a "
            f"question. Pass `ticker` to hold the search to one company. At most "
            f"{MAX_SEARCH_RESULTS} passages. Read-only, offline, reproducible."
        ),
        run=search_filings,
    )
