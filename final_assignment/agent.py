"""Your final-assignment agent.

----- THIS IS WHERE YOU BUILD WHAT YOU WANT -----

The grader (grade.py) imports `YourAgent` and calls it once per question. It
must return a `bootcamp_agent.schema.ResearchAnswer` — the same contract the
whole course used, so everything you built keeps working here.

As shipped, this template uses your configured provider (`.env`,
BOOTCAMP_PROVIDER) and falls back to the offline FakeLLM — which honestly
scores 30% on the practice set: refusals pass, grounded questions don't,
because the fake cannot read context. Making this agent pass is the
assignment.

Ideas the course equips you for: a real provider behind the seam, better
retrieval parameters, query expansion (Session 7), a capped reflection step
(Session 8), your Session 10 skill as a system-prompt upgrade. The capstone
contract still applies: citations verified, refusal on unsupported questions,
bounded loops, no secrets in code.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Works in both layouts: inside the bootcamp repo (src/ at the parent) and as a
# standalone Space (src/ copied next to this file).
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE if (_HERE / "src" / "bootcamp_agent").is_dir() else _HERE.parent
sys.path.insert(0, str(_ROOT / "src"))

from bootcamp_agent.agent import answer_question
from bootcamp_agent.config import load_settings
from bootcamp_agent.documents import Document, load_corpus
from bootcamp_agent.llm import LLMClient, get_client
from bootcamp_agent.schema import ResearchAnswer

CORPUS_DIR = _ROOT / "data" / "corpus"


class YourAgent:
    """The agent the grader runs. Make it yours."""

    def __init__(self, client: LLMClient | None = None) -> None:
        self.documents: list[Document] = load_corpus(CORPUS_DIR)
        self.client: LLMClient = client if client is not None else get_client(load_settings())

    def __call__(self, question: str) -> ResearchAnswer:
        result = answer_question(
            question,
            self.documents,
            self.client,
            max_tool_calls=3,
            top_k=3,
        )
        return result.answer
