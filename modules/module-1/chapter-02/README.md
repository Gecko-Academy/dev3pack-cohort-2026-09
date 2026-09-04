# Session 2 — Python for AI engineers

**Tuesday, September 15, 2026 · 2h**

## Learning objectives

- Work with uv (`uv sync`, `uv run`, dependency groups) instead of raw pip/venv.
- Define typed functions and frozen dataclasses; handle exceptions as contracts.
- Separate reusable package code from a script entry point.

## Class flow

1. **Warm-up (10m).** Yesterday's reliability bars; one-question Python
   diagnostic (used only for pairing).
2. **Concept (20m).** Only the Python the capstone uses: dataclasses, typing,
   exceptions, file I/O, JSON, env vars. Why errors are part of a function's
   contract, not an afterthought.
3. **Live coding (25m).** Walk `config.py` → `llm.py` → `cli.py`: a typed
   package with a provider seam, and the thin-CLI rule ("if logic creeps into
   the CLI, it belongs in the package").
4. **Lab (40m).** `notebook.ipynb`: build `MiniDocument` + `load_mini` with two
   failure modes, pass the self-check, compare with `bootcamp_agent.documents`.
   Then: ask your assistant to propose tests for your loader — review and
   correct at least one of them.
5. **Share (10m).** One failure mode someone's loader missed.
6. **Exit ticket (5m).**

## Artifact

A typed loader with tests for at least two failure cases, and one
assistant-proposed test you corrected.

## Homework

Three more loader tests (empty file, title-only, wrong extension) and a short
CONTRIBUTING note on running the project locally with uv.

## Optional pre-work

DataCamp *Python Programming Fundamentals* (data types, control flow,
functions, modules).

## Checking your answers

Every exercise in `notebook.ipynb` has the same shape: context, numbered
instructions, a starter that runs as shipped (case 1 done, the rest marked
`TODO(you)`), the expected output, and a `check(...)` cell that prints ✅ or ❌
with a hint. The last cell, `review("ch02")`, is the scorecard.

Working with a coding assistant: give it the exercise's context and
instructions, let it fill the `TODO(you)` lines, then run the check cell
yourself. You read the verdict, not the assistant. `solutions/notebook.ipynb`
is the reference; open it after the check, not before.
