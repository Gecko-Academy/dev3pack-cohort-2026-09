"""The capstone as a LangGraph graph — OPTIONAL appendix to Session 14.

The graded capstone stays framework-free: `bootcamp_agent.agent.answer_question`
is a plain Python loop you can read top to bottom. This script builds the SAME
assistant as an explicit graph, over the same corpus and the same `LLMClient`
seam, so you can compare the two by their traces rather than by taste.

What a graph buys, and what it costs, are both visible here:

* buys — the state and the edges are declared, so "what happens after a parse
  failure" is a line you can point at instead of a branch you have to find;
* costs — one more dependency, one more vocabulary, and a call count that grows
  with every node you add. Read the two traces before you decide it is worth it.

Setup (NOT a course dependency — this is optional material):
    uv add langgraph
    # then either keep BOOTCAMP_PROVIDER=fake, or point it at your local model

Run:
    uv run python units/en/session-08-loops-and-graphs/langgraph_capstone.py

Without langgraph installed the script says so and exits 0, the same
graceful-skip convention every notebook uses. It never needs a paid key: the
default `fake` lane drives it fine, and that is the point — the comparison is
about structure, not about model quality.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))


class State(TypedDict, total=False):
    """The graph's whole state, declared once.

    It lives at module scope on purpose: langgraph resolves a routing
    function's type hints with `get_type_hints`, which cannot see a class
    defined inside a function once `from __future__ import annotations`
    turns the annotations into strings. Measured, not guessed: with State
    inside main() both scripts raise on `add_conditional_edges`.
    """

    question: str
    context: str
    answer: Any
    critique: str
    revised: bool
    path: list[str]


def _skip(reason: str, fix: str) -> int:
    """Say what would have happened, name the fix, and exit cleanly."""
    print(f"skipped: {reason}")
    print(f"   fix:  {fix}")
    print()
    print("What this script would have done:")
    print("  retrieve -> answer -> critique -> (revise once) -> end, as a LangGraph")
    print("  graph over the same corpus and the same LLMClient, printing the node")
    print("  path and the model-call count so you can compare them with the")
    print("  framework-free loop's trace from the notebook.")
    return 0


def main() -> int:
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        return _skip("langgraph is not installed", "uv add langgraph")

    from bootcamp_agent.config import load_settings
    from bootcamp_agent.documents import load_corpus
    from bootcamp_agent.llm import get_client
    from bootcamp_agent.retrieval import retrieve
    from bootcamp_agent.schema import (
        ANSWER_JSON_INSTRUCTIONS,
        AnswerParseError,
        parse_research_answer,
    )

    documents = load_corpus(REPO_ROOT / "data" / "corpus")
    settings = load_settings()
    client = get_client(settings)
    if settings.provider == "fake":
        # The plain fake answers every question with the refusal, which makes the
        # graph run but hides the path. Seed it so the NODES are demonstrable at
        # zero cost: the words are canned, and the path is the lesson.
        from bootcamp_agent.llm import FakeLLM

        client = FakeLLM(
            responses={
                "stopping": json.dumps(
                    {
                        "answer": (
                            "Stop on a final answer, empty retrieval, a double "
                            "parse failure, or an exhausted budget."
                        ),
                        "citations": ["agent-loops"],
                        "confidence": 0.9,
                        "needs_human_review": False,
                    }
                )
            }
        )
        print("lane: fake (canned replies; read the node path, not the prose)\n")
    calls: list[str] = []

    def node_retrieve(state: State) -> State:
        scored = retrieve(state["question"], documents, top_k=3)
        context = "\n\n".join(f"[{s.chunk.doc_id}]\n{s.chunk.text}" for s in scored)
        return {"context": context, "path": [*state.get("path", []), "retrieve"]}

    def node_answer(state: State) -> State:
        calls.append("answer")
        raw = client.complete(
            system=ANSWER_JSON_INSTRUCTIONS,
            user=f"{state['context']}\n\nQ: {state['question']}",
        )
        try:
            answer = parse_research_answer(raw)
        except AnswerParseError as error:
            answer = f"parse failed: {error}"
        return {"answer": answer, "path": [*state.get("path", []), "answer"]}

    def node_critique(state: State) -> State:
        calls.append("critique")
        critique = client.complete(
            system="You are a strict reviewer. Reply APPROVE or one concrete fix.",
            user=f"Q: {state['question']}\nDraft: {state['answer']}",
        )
        return {"critique": critique, "path": [*state.get("path", []), "critique"]}

    def route(state: State) -> str:
        """The whole revision policy, as one declared edge. Cap: exactly one."""
        if state.get("revised"):
            return END
        return (
            "revise" if not state.get("critique", "").strip().upper().startswith("APPROVE") else END
        )

    def node_revise(state: State) -> State:
        calls.append("revise")
        fix = state.get("critique", "")[:80]
        raw = client.complete(
            system=ANSWER_JSON_INSTRUCTIONS,
            user=f"{state['context']}\n\nQ: {state['question']}\nFix: {fix}",
        )
        try:
            answer = parse_research_answer(raw)
        except AnswerParseError as error:
            answer = f"parse failed: {error}"
        return {"answer": answer, "revised": True, "path": [*state.get("path", []), "revise"]}

    builder = StateGraph(State)
    builder.add_node("retrieve", node_retrieve)
    builder.add_node("answer", node_answer)
    builder.add_node("critique", node_critique)
    builder.add_node("revise", node_revise)
    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "answer")
    builder.add_edge("answer", "critique")
    builder.add_conditional_edges("critique", route, {"revise": "revise", END: END})
    builder.add_edge("revise", END)
    graph = builder.compile()

    question = "What stopping conditions should an agent loop have?"
    final = graph.invoke({"question": question, "path": []})

    print(f"question: {question}")
    print(f"node path: {' -> '.join(final.get('path', []))}")
    print(f"model calls: {len(calls)} ({', '.join(calls)})")
    print(f"answer: {final.get('answer')}")
    print()
    print("Compare with the notebook's framework-free run: same corpus, same seam,")
    print("same refusal rule. Count the calls in both before you decide.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
