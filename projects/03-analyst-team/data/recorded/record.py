"""Record one real run of the analyst team, so the notebook has a free lane.

    uv run --extra projects python projects/03-analyst-team/data/recorded/record.py

It needs Ollama with `qwen2.5:7b-instruct` and `nomic-embed-text`, and it reuses
project 02's chunks and chunk vectors rather than making its own: the chunks are
rebuilt by running project 02's own `clean` and `chunk_all` cells, and the run
stops if their fingerprint no longer matches the vectors on disk.

Nothing here is a benchmark. It is one run of one 7B model on one day, kept so
that a learner with no local model still sees the graph move.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from bootcamp_agent.documents import Document  # noqa: E402
from bootcamp_agent.ollama import DEFAULT_MODEL, OllamaClient  # noqa: E402
from bootcamp_agent.projects.analyst_team import Passage, build_team  # noqa: E402
from bootcamp_agent.projects.sec_filings import raw_filing, sources  # noqa: E402
from bootcamp_agent.retrieval import Chunk  # noqa: E402

PROJECT_02 = ROOT / "projects" / "02-sec-filings"
RECORDED_02 = PROJECT_02 / "data" / "recorded"
OLLAMA = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
OUT = HERE / "recorded.json"


def notebook_chunks() -> list[Chunk]:
    """Project 02's chunks, rebuilt by running its own cells. No reimplementation."""
    cells = json.loads((PROJECT_02 / "notebook.ipynb").read_text("utf-8"))["cells"]
    code = ["".join(c["source"]) for c in cells if c["cell_type"] == "code"]
    clean_cell = next(c for c in code if "def clean(" in c)
    chunk_cell = next(c for c in code if "def chunk_all(" in c)
    namespace: dict[str, Any] = {"re": re, "HTMLParser": HTMLParser, "Chunk": Chunk}
    exec(clean_cell.split("cleaned = {")[0], namespace)  # noqa: S102 - our own notebook
    exec(chunk_cell.split("chunks = [")[0], namespace)  # noqa: S102 - our own notebook
    documents = [
        Document(
            doc_id=entry["ticker"].lower(),
            title=entry["company"],
            text=namespace["clean"](raw_filing(entry["ticker"])),
            source=entry["url"],
            tags=(),
        )
        for entry in sources()
    ]
    return [chunk for document in documents for chunk in namespace["chunk_all"](document)]


def embed(texts: list[str]) -> list[list[float]]:
    request = urllib.request.Request(
        f"{OLLAMA}/api/embed",
        data=json.dumps({"model": EMBED_MODEL, "input": texts}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return list(json.loads(response.read())["embeddings"])


def main() -> int:
    recorded_02 = json.loads((RECORDED_02 / "recorded.json").read_text("utf-8"))
    chunks = notebook_chunks()
    fingerprint = hashlib.sha256("\n\x00".join(c.text for c in chunks).encode()).hexdigest()
    if fingerprint != recorded_02["chunk_fingerprint"]:
        print("project 02's chunks moved; its recorded vectors no longer match them")
        return 1
    vectors = np.load(RECORDED_02 / "chunk_vectors.npy").astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    ids = [f"{chunk.doc_id}#{chunk.position}" for chunk in chunks]
    tickers = [chunk.doc_id for chunk in chunks]

    def search(question: str, ticker: str | None, top_k: int) -> list[Passage]:
        """The same cosine search the notebook gets from Chroma, without Chroma."""
        query = np.asarray(embed(["search_query: " + question])[0], dtype=np.float32)
        query /= np.linalg.norm(query)
        scores = vectors @ query
        allowed = [i for i in range(len(ids)) if ticker in (None, tickers[i])]
        best = sorted(allowed, key=lambda i: -scores[i])[:top_k]
        return [(round(float(scores[i]), 4), ids[i], chunks[i].text) for i in best]

    replies: dict[str, str] = {}

    class Recorder:
        """Wraps the live model and files each reply under the prompt's first lines.

        Those two lines are `analyst_team.reply_key`, which is what `FakeLLM`
        matches on, so the recording replays without storing whole prompts.
        """

        def __init__(self) -> None:
            self.model = OllamaClient(model=DEFAULT_MODEL, timeout=300)

        def complete(self, system: str, user: str) -> str:
            reply = self.model.complete(system=system, user=user)
            replies.setdefault("\n".join(user.split("\n")[:2]), reply)
            return reply

    team = build_team(search, Recorder(), framework="plain")
    runs = []
    for question in recorded_02["queries"]:
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
            }
        )
        print(f"{question[:60]:62} {runs[-1]['stopped_because']:11} {runs[-1]['calls']}")

    payload = {
        "_provenance": {
            "recorded": date.today().isoformat(),
            "model": DEFAULT_MODEL,
            "embedding_model": EMBED_MODEL,
            "auth_sent": "none",
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
        "chunk_fingerprint": recorded_02["chunk_fingerprint"],
        "vectors": {
            "chunks": "../../../02-sec-filings/data/recorded/chunk_vectors.npy",
            "queries": "../../../02-sec-filings/data/recorded/query_vectors.npy",
            "note": (
                "Project 02's vectors, by path. They are not copied here: one corpus, "
                "one set of vectors. 'queries' below is their order."
            ),
        },
        "queries": list(recorded_02["queries"]),
        "runs": runs,
        "replies": replies,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n{len(replies)} replies -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
