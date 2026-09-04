# Session 1 — Orientation: from LLM calls to agentic systems

**Monday, September 14, 2026 · 2h**

## Learning objectives

- Distinguish: model, prompt, tool, workflow, agent, MCP server, coding assistant.
- Describe the capstone and where an LLM is probabilistic.
- Explain why evaluation and human review are necessary from day one.

## Class flow (rhythm: warm-up → concept → live code → break → lab → share → exit)

1. **Warm-up (10m).** Doctor screenshots on screen; stragglers get a helper, not
   the lecture's attention.
2. **Concept (20m).** The request–context–model–tool–verification mental model.
   The capstone roadmap: what `src/bootcamp_agent/` will look like by Session 12.
3. **Live coding (25m).** One `FakeLLM.complete` call with nothing around it —
   the boundary every framework wraps. Then the same call through the CLI
   (`uv run bootcamp-agent --trace "..."`) to preview where we're going.
4. **Lab (40m).** `notebook.ipynb`: three calls, inspect the provider seam,
   write your reliability bar.
5. **Share (10m).** Two learners read their reliability definitions; class
   spots the differences.
6. **Exit ticket (5m).** Works / unclear / next action.

## Artifact

Working environment, a baseline call, and a written definition of "reliable
enough for this bootcamp."

## Homework

Finish `SETUP.md` if anything is red; write three developer tasks an assistant
could help with but must not complete without review.

## Optional pre-work

DataCamp *AI Engineering with LangChain* intro sections; first lessons of
DeepLearning.AI *Agentic AI*.

## Checking your answers

Every exercise in `notebook.ipynb` has the same shape: context, numbered
instructions, a starter that runs as shipped (case 1 done, the rest marked
`TODO(you)`), the expected output, and a `check(...)` cell that prints ✅ or ❌
with a hint. The last cell, `review("ch01")`, is the scorecard.

Working with a coding assistant: give it the exercise's context and
instructions, let it fill the `TODO(you)` lines, then run the check cell
yourself. You read the verdict, not the assistant. `solutions/notebook.ipynb`
is the reference; open it after the check, not before.
