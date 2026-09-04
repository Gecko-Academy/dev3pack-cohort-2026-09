# Depth track — software engineering fundamentals

Optional. Self-paced. Nothing in the fifteen sessions depends on it, nothing here
is graded, and skipping it costs you no marks.

It exists because of one line in the DeepLearning.AI AI Engineering Skills Map:

> Understanding software fundamentals is important for steering your agent to
> make the tradeoffs you want, or to even know what tradeoffs exist to be made.

The failure that line names is not *cannot deploy*. It is that a developer never
knew a tradeoff existed, so they never steered the agent toward it. A coding
agent will write the endpoint. It will not decide whether the trace belongs in
the response, whether a refusal is a 200 or a 422, or what a 500 is allowed to
say. Those decisions stay yours, and this track is five of them.

## The five modules

| # | Module | The decision you make |
|---|---|---|
| 1 | [Building full-stack applications](01-full-stack/) | Where the boundary goes, and what a caller sees when it works, refuses, or breaks |
| 2 | [Managing data](02-managing-data/) | In memory or durable, what to keep, and what you refuse to keep at all |
| 3 | [Designing system architectures](03-architecture/) | Synchronous or not, and the measurement that would reverse the call |
| 4 | [Making systems secure and reliable](04-secure-and-reliable/) | Fail closed or degrade, and the risk you decide to live with |
| 5 | [Scaling and operating in production](05-production/) | Measured or aspirational, and what you would actually page on |

Each is one notebook of two to three exercises, roughly 45 minutes, built on the
same assistant you build during the course. Everything runs offline against
`FakeLLM`. No API key, no cloud account, no cost.

## How to run one

```bash
uv sync --group dev
uv run jupyter lab            # then open depth/01-full-stack/notebook.ipynb
```

Each notebook opens with the same preflight the course uses, so a broken
environment tells you what to fix instead of failing three cells later.

## How you know you got it right

The same way as in the course: every exercise ends with a `check(...)` cell, and
`review("d1")` prints the module's scorecard. There is no answer key to read
past. The solutions sit in `<module>/solutions/notebook.ipynb` if you want to
compare after, not before.

What is unusual here is **what** the checks judge. The course checks behaviour:
it re-runs retrieval, counts model calls, calls your function. Several of these
check a *decision*, because that is what a fundamentals pillar teaches. A
decision is checkable when it carries something falsifiable, so:

- an architecture decision must name the measurement that would reverse it.
  "When it gets slow" is refused; "p95 above 2000 ms for 15 minutes" passes;
- a retention policy must name something it refuses to remember;
- a negative-test row must record what you **observed**, not what you intended.
  "As expected" is refused, because it records nothing;
- a latency figure must say whether it was measured or is a target, and the
  check refuses a target. Run it.

That line, between a decision and an opinion, is the reason this track works
self-paced with nobody reading your answers.

## Order

Take them in any order. If you want one, module 2 first: data is the layer that
is hardest to change afterwards, so it is the one where an early wrong call
costs the most later.

## What this track is not

It is not a production system, and finishing it does not mean you can operate
one. It is the vocabulary and the judgement that let you tell a coding agent
which tradeoff you want, and recognise when it has quietly made a different one.
