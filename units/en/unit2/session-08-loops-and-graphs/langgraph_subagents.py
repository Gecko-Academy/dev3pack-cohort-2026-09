"""Subagents in a graph — OPTIONAL appendix to Session 14, second half.

`langgraph_capstone.py` turns the loop into a graph. This one splits the work
across four narrow roles, each with its own instruction and its own budget:

    router     -> decides whether the corpus can support the question at all
    retriever  -> fetches passages, and only that
    answerer   -> writes the answer from those passages, cites, or refuses
    critic     -> checks the answer against the passages, once

WHY THIS IS THE APPENDIX AND NOT THE COURSE. Four roles means at least three
model calls where the graded loop spends one, and the split only pays when each
role's instruction is narrower than one combined prompt could be. On a 7B local
model the extra hops are also where quality falls apart first: a critic that
cannot read carefully approves everything, which is worse than no critic,
because it looks like review. Judge it on the traces and the call count, never
on how sophisticated it sounds.

Setup (NOT a course dependency):
    uv add langgraph

Run:
    uv run python units/en/session-08-loops-and-graphs/langgraph_subagents.py

Without langgraph the script explains itself and exits 0. It needs no paid key.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))


class State(TypedDict, total=False):
    """The graph's state, at module scope so langgraph can resolve the hints.

    See the note in langgraph_capstone.py: a State defined inside main()
    makes `add_conditional_edges` raise, because `get_type_hints` cannot
    resolve a stringified annotation that names a function-local class.
    """

    question: str
    verdict: str
    context: str
    answer: Any
    critique: str
    path: list[str]


#: One line per role. The narrowness IS the design; a role whose instruction
#: could be pasted into another role's prompt has not earned its own node.
ROLES = {
    "router": (
        "Answer only CORPUS or OUTSIDE. CORPUS if the question is about agents, RAG, "
        "structured outputs, MCP, prompt injection or evaluation. Nothing else."
    ),
    # the answerer uses the shared strict-JSON contract, so it has no role line
    "critic": (
        "You are a strict reviewer. Reply APPROVE, or name one concrete fix. "
        "Never rewrite the answer yourself."
    ),
}


def _skip(reason: str, fix: str) -> int:
    print(f"skipped: {reason}")
    print(f"   fix:  {fix}")
    print()
    print("What this script would have done:")
    print("  router -> retriever -> answerer -> critic, four narrow roles in one")
    print("  LangGraph, printing each role's decision, the node path and the total")
    print("  model-call count, so you can weigh it against the one-call loop.")
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
        # One fake serves all four roles, and it matches on the USER text, so the
        # keys below are ordered: the critic's prompt is the only one containing
        # "Passages:". Canned on purpose — what this demonstrates is the PATH.
        from bootcamp_agent.llm import FakeLLM

        client = FakeLLM(
            responses={
                "passages": "APPROVE",
                "pizza": "OUTSIDE",
                "stopping": json.dumps(
                    {
                        "answer": (
                            "Stop on a final answer, empty retrieval, or an exhausted budget."
                        ),
                        "citations": ["agent-loops"],
                        "confidence": 0.9,
                        "needs_human_review": False,
                    }
                ),
            },
            default="CORPUS",
        )
        print("lane: fake (canned replies; read the node path, not the prose)")
    calls: list[str] = []

    def step(state: State, name: str) -> list[str]:
        return [*state.get("path", []), name]

    def router(state: State) -> State:
        calls.append("router")
        verdict = client.complete(system=ROLES["router"], user=state["question"])
        return {"verdict": verdict.strip(), "path": step(state, "router")}

    def route_after(state: State) -> str:
        """OUTSIDE stops here, before retrieval and before the answerer."""
        return "retriever" if "OUTSIDE" not in state.get("verdict", "").upper() else END

    def retriever(state: State) -> State:
        scored = retrieve(state["question"], documents, top_k=3)
        context = "\n\n".join(f"[{s.chunk.doc_id}]\n{s.chunk.text}" for s in scored)
        return {"context": context, "path": step(state, "retriever")}

    def answerer(state: State) -> State:
        calls.append("answerer")
        raw = client.complete(
            system=ANSWER_JSON_INSTRUCTIONS,
            user=f"{state.get('context', '')}\n\nQ: {state['question']}",
        )
        try:
            answer: Any = parse_research_answer(raw)
        except AnswerParseError as error:
            answer = f"parse failed: {error}"
        return {"answer": answer, "path": step(state, "answerer")}

    def critic(state: State) -> State:
        calls.append("critic")
        critique = client.complete(
            system=ROLES["critic"],
            user=f"Passages:\n{state.get('context', '')[:600]}\n\nAnswer: {state.get('answer')}",
        )
        return {"critique": critique.strip(), "path": step(state, "critic")}

    builder = StateGraph(State)
    for name, node in (
        ("router", router),
        ("retriever", retriever),
        ("answerer", answerer),
        ("critic", critic),
    ):
        builder.add_node(name, node)
    builder.set_entry_point("router")
    builder.add_conditional_edges("router", route_after, {"retriever": "retriever", END: END})
    builder.add_edge("retriever", "answerer")
    builder.add_edge("answerer", "critic")
    builder.add_edge("critic", END)
    graph = builder.compile()

    for question in (
        "What stopping conditions should an agent loop have?",
        "What is the best pizza in Sao Paulo?",
    ):
        calls.clear()
        final = graph.invoke({"question": question, "path": []})
        print(f"\nQ: {question}")
        print(f"  router said: {final.get('verdict', '')[:40]!r}")
        print(f"  node path:   {' -> '.join(final.get('path', []))}")
        print(f"  model calls: {len(calls)} ({', '.join(calls) or 'none'})")
        print(f"  answer:      {str(final.get('answer'))[:90]}")
        if final.get("critique"):
            print(f"  critique:    {final['critique'][:80]}")

    print()
    print("Read the second question's path: the router should stop it before")
    print("retrieval. If it did not, the router is not doing its job, and a role")
    print("that does not do its job is a call you paid for and did not use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
