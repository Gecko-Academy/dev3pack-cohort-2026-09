# Harness Engineering

*Thread sessions: 4 (assistant configuration), 9 (tracing and evaluation),
14 (hardening). Reference implementations: `AGENTS.md`, `src/bootcamp_agent/evals.py`,
`.github/workflows/test.yml`.*

The model is the smallest part of a reliable agent system. Everything around it
— the instructions it reads, the contracts on its tools, the traces it leaves,
the evaluations that grade it, the CI that reruns those evaluations on every
change — is the **harness**. Models are interchangeable and improve on their
own; the harness is the part you engineer, and it is where reliability actually
lives.

## The layers, mapped to this repository

| Harness layer | What it does | Where it lives here |
|---|---|---|
| Project instructions | Durable context: architecture, commands, rules, "do not"s | `AGENTS.md` (+ `CLAUDE.md`, `.cursor/rules/`) |
| Output contract | Makes responses machine-checkable | `schema.py` — strict parse, reject unknown fields |
| Tool contracts | Bounds what actions are possible | `tools.py` — validation, caps, read-only |
| Loop bounds | Budgets and defined exits | `agent.py` — see [loop-engineering](loop-engineering.md) |
| Traces | Records what actually happened | `TraceEvent`s on every result |
| Evaluation | Repeatable measurement | `evals.py` + `data/evals/golden.jsonl` |
| Regression suite | Keeps fixed things fixed | `tests/` — every bugfix starts with a failing test |
| CI | Reruns all of it on every change | `.github/workflows/test.yml` |

Two observations. First, **most of the harness is boring, classical software
engineering** — dataclasses, validation, pytest. That is the point: the
probabilistic component is fenced in by deterministic ones. Second, the layers
compose: an injection that survives the instructions still has to produce valid
schema output, using only bounded tools, within a budget, in front of a trace.

## Instructions are code — review them like code

`AGENTS.md` is executed by every assistant that touches the repo, thousands of
times. A wrong sentence there is a bug with fan-out. Treat it accordingly:
version it, review diffs to it, and improve it from observed failures (Session
4's homework — fix the instruction that let the assistant make a wrong
assumption — is a bugfix workflow). Keep one canonical policy file and make the
per-assistant files point to it; duplicated policy drifts.

## A claim needs a probe

"The assistant handles unsupported questions" is a claim. The golden set's
refusal cases are its probe. The discipline that keeps a harness honest:

- Every property you care about appears as a case in the evaluation set or a
  test — including the unhappy ones (refusal, tool error, injection).
- "It worked when I tried it" is a report about one run; the eval command is a
  report about the system. Only the second survives a model upgrade.
- Inspect the evaluator itself for false positives (Session 9's lab). An eval
  that passes everything is worse than no eval — it manufactures confidence.
- Change **one** component between measurements, and report the regressions
  your improvement caused, not just the improvement.

## Traces make failures cheap

When case 7 fails, the trace answers the diagnostic question in minutes: was
the right chunk retrieved (retrieval failure) or retrieved-but-ignored
(generation failure)? Did the tool get called with bad arguments, or did a good
call get misused? Without a trace, every failure is an investigation; with one,
it's a lookup. That is why `answer_question` refuses to return an answer
without also returning what it did.

## Security is a harness property

Session 14's failure clinic is harness engineering under adversarial pressure:
retrieved text containing an embedded instruction must be *quoted*, not obeyed
— which is enforced not by hoping the model resists, but by the layers above
(data-vs-instruction framing in the system prompt, strict output schema,
read-only bounded tools, citations verified against retrieval). And note what
never appears in any layer the model can see: credentials. Secrets are injected
at the transport edge by the application; the model cannot leak what it never
had. The harness is precisely the set of properties that hold **even when the
model misbehaves**.

## Exercises

- Pick one sentence of `AGENTS.md`, break it deliberately, and observe the
  assistant's behavior change. Instructions-as-code becomes visceral fast.
- Add one golden case for a property you currently only believe. Watch whether
  it passes.
- Read your last failing trace bottom-up and classify the failure into one of:
  retrieval, tool selection, instruction-following, formatting, unsupported
  claim. That classification *is* your next work item.
