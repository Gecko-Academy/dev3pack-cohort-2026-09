# Loop Engineering

*Thread sessions: 5 (tools) and 8 (agentic patterns). Reference implementation:
`src/bootcamp_agent/agent.py`.*

"Agent" is a loop, and the loop is yours. The model contributes one thing per
iteration — a decision — while the application owns everything that makes the
loop safe: what the model sees, what it is allowed to do, when it must stop, and
what happens when it fails. Loop engineering is the discipline of designing
those parts on purpose.

## The four beats of an iteration

1. **Perceive** — assemble the context: the question, retrieved passages,
   previous tool results. (You choose what enters; see
   [harness-engineering](harness-engineering.md) for the context budget.)
2. **Decide** — the model chooses: answer now, or call a tool with these
   arguments. This is the only probabilistic beat.
3. **Act** — the application validates the arguments **at the boundary** and
   executes. In this repo, `tools.py` clamps `max_results`, rejects empty
   queries, and answers unknown ids with the list of valid ones — the model
   never gets to act on an unchecked input.
4. **Observe** — the result (or the typed error) is appended to the context for
   the next beat.

## Stopping conditions: write them first

An unbounded loop is a bug. Before writing the loop body, enumerate every way
it ends:

| Condition | This repo's implementation |
|---|---|
| Final answer produced | `parse_research_answer` succeeds → return |
| Nothing to work with | empty retrieval → refuse **before any LLM call** |
| Output contract violated twice | one corrective retry, then a flagged refusal |
| Budget exhausted | `max_tool_calls` parameter — the loop cannot exceed it |
| Repetition detected | same tool + same args twice = spinning; stop and refuse |

Notice the pattern: every exit is a *defined state*, and the worst exits set
`needs_human_review=True` rather than truncating silently.

## Budgets are product decisions, not constants

`max_tool_calls=3` is not a magic number — it is a statement about how much
latency, cost, and blast radius this feature is worth. Make budgets parameters,
surface them in traces, and revisit them with evaluation data. When a budget is
hit in production you want a trace that says "budget exhausted after
search→search→metadata", not a mystery timeout.

## Refusal is the load-bearing path

Design the refusal before the happy path. In `agent.py` the refusal object is
built by `_refusal()` and reached from three places: empty retrieval, double
parse failure, and fabricated citations. Every other safeguard in the system
ultimately falls back to it. If your loop cannot refuse, it will fabricate —
the model always has *something* plausible to say.

## The autonomy ladder

Climb one rung at a time, and only when a **measured** failure justifies it:

1. **Fixed chain** — no decisions. If the steps are known, use this. It is not
   less impressive; it is more correct.
2. **Tool loop** — the model picks tools within a budget (this repo's level).
3. **Reflection** — the model critiques its own draft. Cap revisions at one
   until an eval proves two helps (Session 8 measures exactly this).
4. **Multi-agent** — models delegating to models. Each hop multiplies failure
   modes; you need traces and evals *per agent* before this is debuggable.

The professional question is never "how autonomous can I make it" but "what is
the least autonomy that passes the eval." Session 8's homework — *where should
autonomy stop in the capstone?* — is this guide in one page.

## Exercises

- Set `max_tool_calls=1` in a notebook and find the question that degrades.
  What does the trace show?
- Add a repetition guard (same tool, same arguments) to a copy of the loop and
  write the test that proves it fires.
- Take any workflow you built this week and write down its exit table like the
  one above. If you can't fill it in, the loop isn't finished.
