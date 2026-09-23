"""Record one real run of the analyst team, so the notebook has a free lane.

    uv run python projects/03-analyst-team/data/recorded/record.py

It needs Ollama with `qwen2.5:7b-instruct`, and nothing else: no embedding model,
no numpy, no vectors.

IT RECORDS AGAINST THE NOTEBOOK'S OWN INDEX, and that is the whole point of this
file. The first version recorded against project 02's embedding vectors while the
notebook searched by keyword, so every recorded draft cited chunk ids the notebook
never retrieved. The writer dropped all of them, and a learner on the recorded
lane saw an answer with no citations and a `needs_human_review` flag on every
single run. A recording made against a different retrieval is not a recording of
this notebook. So the index here is built by executing the notebook's own cells.

The questions come from `analyst_team.DEMO_QUESTIONS` plus project 02's twenty
labelled ones. ONE list, imported, never retyped: a demo question that drifts out
of the recording replays as a refusal, and the notebook still prints something
that looks like an answer.

Nothing here is a benchmark. It is one run of one 7B model on one day, kept so
that a learner with no local model still sees the team move.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from bootcamp_agent.ollama import DEFAULT_MODEL, OllamaClient  # noqa: E402
from bootcamp_agent.projects import sec_filings  # noqa: E402
from bootcamp_agent.projects.analyst_team import (  # noqa: E402
    DEMO_QUESTIONS,
    Passage,
    build_team,
)

NOTEBOOK = HERE.parents[1] / "notebook.ipynb"
OUT = HERE / "recorded.json"


def notebook_search() -> Any:
    """The notebook's own `search`, built by running the notebook's own cells.

    Two cells, cut at the line where each stops defining and starts printing. No
    reimplementation, so the recording cannot drift from what a learner runs.
    """
    cells = json.loads(NOTEBOOK.read_text("utf-8"))["cells"]
    code = ["".join(cell["source"]) for cell in cells if cell["cell_type"] == "code"]
    index_cell = next(c for c in code if "def passages_of(" in c)
    search_cell = next(c for c in code if "def search(" in c)
    namespace: dict[str, Any] = {
        "re": re,
        "math": math,
        "Counter": Counter,
        "HTMLParser": HTMLParser,
        "sec_filings": sec_filings,
    }
    exec(index_cell.split('print(f"{len(INDEX)}')[0], namespace)  # noqa: S102 - our own notebook
    exec(search_cell.split("QUESTION = ")[0], namespace)  # noqa: S102 - our own notebook
    print(f"index: {len(namespace['INDEX'])} passages from {len(namespace['TICKERS'])} companies")
    return namespace["search"]


def main() -> int:
    search = notebook_search()

    def searcher(question: str, ticker: str | None, top_k: int) -> list[Passage]:
        return list(search(question, ticker, top_k))

    replies: dict[str, str] = {}

    class Recorder:
        """Wraps the live model and files each reply under the prompt's first two lines.

        Those two lines are `analyst_team.reply_key`, which is what `FakeLLM`
        matches on, so the recording replays without storing whole prompts.
        """

        def __init__(self) -> None:
            self.model = OllamaClient(model=DEFAULT_MODEL, timeout=300)

        def complete(self, system: str, user: str) -> str:
            reply = self.model.complete(system=system, user=user)
            replies.setdefault("\n".join(user.split("\n")[:2]), reply)
            return reply

    # The notebook's demo questions first, then project 02's labelled twenty. A
    # question in both lists is recorded once: the key is the question.
    labelled = [item["question"] for item in sec_filings.questions()]
    asked: list[str] = list(dict.fromkeys([*DEMO_QUESTIONS.values(), *labelled]))

    team = build_team(searcher, Recorder(), framework="plain")
    runs = []
    for number, question in enumerate(asked, start=1):
        state = team.run(question)
        runs.append(
            {
                "question": question,
                "ticker": state.get("ticker"),
                "routed_by": state.get("routed_by"),
                "calls": state.get("calls", []),
                "revisions": state.get("revisions", 0),
                "stopped_because": state.get("stopped_because"),
                "approved": state.get("approved", False),
                "cited": list(getattr(state.get("answer"), "citations", ()) or ()),
                "dropped": list(state.get("rejected", [])),
            }
        )
        print(
            f"{number:3}/{len(asked)} {question[:56]:58} "
            f"{runs[-1]['stopped_because']:11} {runs[-1]['calls']}"
        )

    dropped = sum(len(run["dropped"]) for run in runs)
    payload = {
        "_provenance": {
            "recorded": date.today().isoformat(),
            "model": DEFAULT_MODEL,
            "auth_sent": "none",
            "retrieval": (
                "the notebook's own keyword search, built by executing the notebook's "
                "index and search cells. No embeddings, no vectors, no second model"
            ),
            "lane": "one real run of the local model, replayed when no model is running",
            "is_evidence_of": (
                "what this model wrote for these prompts, on these passages, on that run"
            ),
            "is_not_evidence_of": (
                "what it writes every time, nor that the answers are right. No temperature "
                "is pinned, a 7B model words things differently on every run, and nobody "
                "graded the content. Run it live to see yours."
            ),
        },
        "questions": {
            "demo": list(DEMO_QUESTIONS.values()),
            "labelled": labelled,
            "note": (
                "'demo' is analyst_team.DEMO_QUESTIONS, the questions the notebook asks a "
                "model. It is imported, never retyped, so it cannot drift out of this file."
            ),
        },
        "queries": asked,
        "runs": runs,
        "replies": replies,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    approved = sum(1 for run in runs if run["approved"])
    calls = sum(len(run["calls"]) for run in runs)
    print(
        f"\n{len(asked)} questions, {calls} model calls, {approved} approved on the first draft, "
        f"{dropped} citation(s) dropped -> {OUT.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
