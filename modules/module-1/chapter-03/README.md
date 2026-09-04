# Session 3 — Prompts and structured outputs

**Wednesday, September 16, 2026 · 2h**

## Learning objectives

- Separate system instructions from user input and retrieved context.
- Write prompts with explicit constraints; request structured output.
- Validate strictly at the boundary; handle refusal and parse failure.

## Class flow

1. **Warm-up (10m).** One loader test from homework, shown and discussed.
2. **Concept (20m).** Prompt anatomy (system / user / context); output schemas;
   "parsing is an application responsibility"; why a schema must make refusal
   expressible (`needs_human_review`).
3. **Live coding (25m).** The `ResearchAnswer` schema and `parse_research_answer`
   — demonstrate it rejecting prose, missing fields, unknown fields, and
   `confidence: 7`. Then the retry-once-then-refuse pattern in `agent.py`.
4. **Lab (40m).** `notebook.ipynb`: unconstrained vs typed comparison; try to
   sneak bad output past the parser; author three golden questions
   (answerable / ambiguous / unsupported) and run them through the agent with
   traces on.
5. **Share (10m).** The best "valid JSON, wrong answer" example found — schema
   conformance is not correctness.
6. **Exit ticket (5m).**

## Artifact

A structured-output call with validation and three golden questions with
expected behaviors.

## Homework

Two adversarial questions (one embedding an instruction in the question);
compare unstructured vs structured behavior.

## Optional pre-work

DataCamp prompt-engineering modules (OpenAI API track).

## Checking your answers

Every exercise in `notebook.ipynb` has the same shape: context, numbered
instructions, a starter that runs as shipped (case 1 done, the rest marked
`TODO(you)`), the expected output, and a `check(...)` cell that prints ✅ or ❌
with a hint. The last cell, `review("ch03")`, is the scorecard.

Working with a coding assistant: give it the exercise's context and
instructions, let it fill the `TODO(you)` lines, then run the check cell
yourself. You read the verdict, not the assistant. `solutions/notebook.ipynb`
is the reference; open it after the check, not before.
