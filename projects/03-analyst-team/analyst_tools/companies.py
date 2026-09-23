"""The roster tool: which companies this desk covers, and under which ticker.

A question about the desk is not a question about a filing. Searching the
filings for "which companies do you cover" returns whichever filing happens to
use those words, which is how step 2's misses happen.
"""

from __future__ import annotations

from bootcamp_agent.projects.analyst_team import Passage
from bootcamp_agent.tools import Tool


def build(tickers: dict[str, str]) -> Tool:
    """Wrap the ticker table as a Tool. It takes no arguments, so it cannot be misaimed."""

    def list_companies() -> list[Passage]:
        """Return the desk's eight companies, ticker and name, as one passage."""
        roster = "; ".join(f"{ticker} = {name}" for ticker, name in sorted(tickers.items()))
        return [(1.0, "roster#0", f"This desk covers {len(tickers)} companies: {roster}.")]

    return Tool(
        name="list_companies",
        description=(
            "List every company this desk covers, with its ticker. Takes no arguments. "
            "Use it for questions about the coverage itself, not about a filing."
        ),
        run=list_companies,
    )
