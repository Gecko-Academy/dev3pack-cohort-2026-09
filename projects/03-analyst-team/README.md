# Project 03 — The analyst team

One agent answered the question in Project 02. Here four of them do, each with one job,
and you count what that costs.

## The brief

The analyst covers eight companies for a desk now, not for herself, and every answer she
sends is read by someone who can check it. She asks for "a second pair of eyes on every
answer".

Today she pastes a question into Project 02's notebook and reads what comes back. It is
right most of the time. When it is wrong it is wrong quietly: ask *who is exposed to taxes
on sweet drinks* and the passages that come back are **Apple's**, because Coca-Cola writes
*sweetened beverages* and Apple writes about *taxes*. The answer is fluent, the citation is
real, and the company is wrong.

A second pair of eyes is another model call. So is a router, and so is a researcher. This
project builds the team, measures it against the one loop it replaces, and leaves the
decision where it belongs: **a team costs more model calls than one loop, and you say
whether it bought anything.**

## What you ship

| You deliver | Step | What it is | Check |
|---|---|---|---|
| `search` | 1 | a read-only tool over Project 02's index, held to one company on request | `project-03-e1` |
| `routing` | 3 | 20 rows: the predicted company against the labelled one | `project-03-e2` |
| `run` | 4 | the `TeamState` of one finished question | `project-03-e3` |
| `measurement` | Measure | one row per method: the loop and the team | `project-03-e4` |

The team itself lives in `src/bootcamp_agent/projects/analyst_team.py`, so it is the part
you keep after the class:

```python
from bootcamp_agent.projects.analyst_team import TeamState, build_team, route_company
```

| Role | What it does | Model calls |
|---|---|---|
| Coordinator | reads the question, picks the company, sets the budget | 0 |
| Researcher | calls `search` over the index, brings back passages | 0 |
| Writer | writes the answer as strict JSON, citing only what came back | 1 |
| Critic | approves, or sends it back exactly once | 1 |

## The two lanes

| Lane | What it needs | What the setup cell prints |
|---|---|---|
| `[live]` | Ollama with `qwen2.5:7b-instruct` (4.7 GB) | `answers: [live] qwen2.5:7b-instruct` |
| `[recorded]` | Nothing but the course | `answers: [recorded] <date>` |

Every step runs on both. The recorded lane replays one real run from
`data/recorded/`; only asking questions of your own needs `[live]`. A second line,
`team:`, says whether the module the notebook imports is on your clone.

```bash
uv sync                              # the course
uv sync --extra projects --extra agents               # optional: LangGraph, for step 6
ollama pull qwen2.5:7b-instruct      # optional: without it, every model call plays the recording
uv run jupyter lab                   # open projects/03-analyst-team/notebook.ipynb
```

**LangGraph is optional on purpose.** Steps 1 to 5 build the team in plain Python. Step 6
runs the same team through LangGraph if you installed it, and prints what it could not use
if you did not. Nothing in this notebook requires it.

## The ship checklist

Tick every line before you call it done.

| Check | How to tell |
|---|---|
| Both lanes run | The notebook runs with the model and without it, and the setup cell says which |
| The four checks pass | `project-03-e1` to `project-03-e4` print a tick, or a message you have read |
| No citation was invented | Step 4's `invented:` line reads `none` |
| The run says why it stopped | `stopped_because` is one of `answered`, `budget`, `repeated_call`, `tool_error` |
| The critic is capped | `max_revisions=1`, and step 5 shows what an uncapped one does |
| LangGraph is optional | The notebook runs top to bottom on a clone that never installed it |
| The numbers are yours | The Measure table was printed by your run, not copied from the prose |
| You can say what it bought | One sentence: the extra calls, and what came back for them |

## What it costs

$0, and no account. Everything runs on your machine, and the only network this project
touches is your own Ollama on `localhost:11434`. About 90 minutes the first time, most of it
reading. The recorded lane reruns in seconds; live, the whole notebook makes about 25 model
calls.

## The data

This project adds no data. It reads Project 02's filings and labelled questions **by path**
and never copies them. See `data/LICENSE.md`.

## Also read

- `AGENTS.md` — what a coding assistant may and may not do in this folder.
- `../02-sec-filings/` — the index this project reads, and the loop it is measured against.
- `../../units/en/unit2/session-08-loops-and-graphs/` — a chain, a loop, a capped
  reflection, counted calls, and a state machine with declared transitions.
