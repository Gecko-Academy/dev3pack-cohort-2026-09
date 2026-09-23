"""The one tool that leaves the machine: DuckDuckGo web search, through LangChain.

It is optional, and everything about it is arranged so that a learner with no
network and a CI runner with no extras still run every cell:

- the dependency is imported inside `run`, so BUILDING the tool always works and
  the registry looks the same on every machine;
- a machine without the extra gets a `ToolError` that names the install command,
  not a traceback;
- an empty result and a rate limit are `ToolError` too, because "the endpoint
  said no today" is a normal Tuesday for a free search endpoint.

It stays OUT of the measured comparison, and that is not shyness. A web result
changes between two runs, the endpoint rate-limits, and a number measured against
a corpus that moves under you is not a number. The measured lane is the local
index, which returns the same passages in October that it returns today.
"""

from __future__ import annotations

import warnings

from bootcamp_agent.projects.analyst_team import Passage
from bootcamp_agent.tools import Tool, ToolError

#: Untrusted text, so it is capped before anything reads it. Session 4's rule.
MAX_CHARS = 1200

INSTALL = "uv sync --extra projects --extra agents"


def _search_run() -> object:
    """Import the LangChain wrapper, or say which command installs it."""
    try:
        with warnings.catch_warnings():
            # langchain-community is being sunset upstream. The notice is real and
            # it is in the prose; it is filtered here so a learner's first web
            # search is not a wall of red about a package they did not choose.
            warnings.simplefilter("ignore", DeprecationWarning)
            from langchain_community.tools import DuckDuckGoSearchRun
    except ImportError as error:
        raise ToolError(
            f"web_search needs the optional extra, which is not installed here. Run: {INSTALL}"
        ) from error
    return DuckDuckGoSearchRun()


def missing() -> str | None:
    """The install command when the extra is absent, or None when it is present."""
    try:
        _search_run()
    except ToolError as error:
        return str(error)
    return None


def build() -> Tool:
    """Wrap DuckDuckGo as a Tool. Building never fails; only calling it can."""

    def web_search(query: str, k: int = 3) -> list[Passage]:
        """Search the public web for recent context. Not reproducible, so not measured."""
        if not query or not query.strip():
            raise ToolError("web_search: 'query' must be a non-empty string")
        runner = _search_run()
        try:
            text = str(runner.invoke(query.strip()))  # type: ignore[attr-defined]
        except Exception as error:  # the endpoint rate-limits, and that is not a crash
            raise ToolError(
                f"web_search: DuckDuckGo refused this query ({type(error).__name__}: "
                f"{str(error)[:160]}). Free endpoints rate-limit; wait, or use search_filings."
            ) from error
        snippets = [part.strip() for part in text.split(". ") if part.strip()][: max(1, int(k))]
        if not snippets:
            raise ToolError("web_search: DuckDuckGo returned nothing for this query")
        # The score is the rank DuckDuckGo gave it, not a measurement of anything.
        # It is NOT comparable with the index's scores, which is the second reason
        # this tool stays out of the Measure step.
        return [
            (round(1.0 / (rank + 1), 2), f"web#{rank}", snippet[:MAX_CHARS])
            for rank, snippet in enumerate(snippets)
        ]

    return Tool(
        name="web_search",
        description=(
            "Search the public web with DuckDuckGo for context a 10-K filing cannot have, "
            "such as this week's news. Returns at most `k` snippets. Not reproducible: two "
            "runs differ, the endpoint rate-limits, and it is never used in a measurement."
        ),
        run=web_search,
    )
