# Session 5 — Tools: controlled capabilities

**Friday, September 18, 2026 · 2h · Thread: loop engineering**

## Learning objectives

- Define a tool with a narrow input/output contract; validate arguments at the
  boundary.
- Separate planning from execution; prevent silent side effects.
- Understand budgets (`max_tool_calls`) and why every loop exit is designed.

## Class flow

1. **Warm-up (10m).** Best instruction-file fix from homework.
2. **Concept (20m).** Tool schemas; tool selection; idempotence; read-only vs
   side-effecting; why caps are clamped by the app, never trusted from the
   model. The loop's exit table (see the loop-engineering guide).
3. **Live coding (25m).** Walk `tools.py`: the capped `search_documents`, the
   helpful-error `get_document_metadata`, the LLM-backed `summarize_document`.
   Show `agent.py` choosing and logging.
4. **Lab (40m).** `notebook.ipynb`: exercise the boundaries, then implement
   `list_documents(tag=None)` to a four-clause contract and pass the boundary
   self-check. Budget experiment: the same question at `max_tool_calls=3` vs
   `1`, traces compared.
5. **Share (10m).** One boundary someone's tool initially failed to enforce.
6. **Exit ticket (5m).** Week-1 checkpoint review.

## Artifact

A tool-using assistant with a fourth tool passing boundary tests.

## Homework

Write one example where the assistant should NOT use a tool, and one where it
should ask for human confirmation. Read `docs/guides/loop-engineering.md`.

## Optional pre-work

LangChain Academy *Introduction to LangChain* (agents with Python). Then try
[`langchain_template.py`](langchain_template.py) — LangChain's
`init_chat_model` is the framework's version of the provider seam you built
this week, and the template asks a live model to explain *loop engineering vs
graph engineering*; grade its answer against the course guides. It skips
cleanly without a key or without LangChain installed:

```bash
uv add langchain langchain-openai   # optional deps, not part of the course env
uv run python modules/module-1/chapter-05/langchain_template.py
```

A second template, [`langchain_api_intent.py`](langchain_api_intent.py), turns
an API operation name (`GET /pets/{petId}`) into a semantic intent description
— what it does, what it returns, when an agent should route here. That is the
Gecko thread in miniature; compare with cookbook notebook 02, which does the
same job from a real spec.

## Checking your answers

Every exercise in `notebook.ipynb` has the same shape: context, numbered
instructions, a starter that runs as shipped (case 1 done, the rest marked
`TODO(you)`), the expected output, and a `check(...)` cell that prints ✅ or ❌
with a hint. The last cell, `review("ch05")`, is the scorecard.

Working with a coding assistant: give it the exercise's context and
instructions, let it fill the `TODO(you)` lines, then run the check cell
yourself. You read the verdict, not the assistant. `solutions/notebook.ipynb`
is the reference; open it after the check, not before.
