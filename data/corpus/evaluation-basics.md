<!-- title: Evaluation Basics -->
<!-- tags: evaluation, testing, golden-set, tracing, reliability -->

# Evaluation Basics

"It seemed to work when I tried it" is not evidence. Evaluation replaces
anecdotes with a repeatable measurement: a fixed set of cases, a defined pass
condition, and a command anyone can run. For LLM applications this is the single
highest-leverage engineering habit, because model behavior changes under your
feet — a new model version, a reworded prompt, a different retrieval setting —
and only a rerunnable measurement tells you whether things got better or worse.

## The golden set

Start with a small labeled set — eight to twenty cases is genuinely useful. Each
case pairs an input with an expected property, not necessarily an exact string:
"the answer cites document X", "the system refuses", "the JSON parses and
confidence is below 0.5". Include the unhappy paths deliberately: at least one
question whose correct answer is "not found", and one adversarial input. A
golden set without refusal cases grades a system on charisma, not reliability.

## Code checks vs LLM-as-judge

Prefer code-based checks whenever the property is mechanical: did it cite the
expected source, did it parse, did it stay under the tool budget. They are fast,
free, and deterministic. LLM-as-judge — using a model to grade another model's
output — earns its place for genuinely fuzzy properties like tone or coherence,
but it inherits the judge's own biases and must itself be spot-checked against
human labels. A common failure is an evaluator that passes everything; inspect
your evaluator's false positives before trusting its pass rate.

## Traces turn failures into diagnoses

A trace is the ordered record of what the system actually did: what was
retrieved, which tools were called with which arguments, what the model
returned. When a case fails, the trace answers the diagnostic question — was it
retrieval, tool selection, instruction-following, or formatting? — in minutes.
Classify each failure into one of those buckets, fix the biggest bucket first,
and add a regression case so the same failure cannot return unnoticed.

## The loop

Baseline, change one thing, rerun, compare. Never change two things between
measurements, and never report an improvement without also reporting what got
worse. An honest evaluation report includes the regression it caused.
