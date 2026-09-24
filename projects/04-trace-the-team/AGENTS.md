# Project 04 for coding assistants: Trace the team, then grade it

This file tells a coding assistant what this project is and how to help with it. It
adds to the repository's root `AGENTS.md` and never overrides it.

## Purpose

Project 03 built a team of four roles and measured it on one number: how often it picked
the right company. That number cannot say why a run went wrong. The learner now wraps
that team without editing it, records what it did in what order, grades every labelled
question against a written pass condition, and sorts the failures into buckets so the
next fix has an address.

The move that matters is the wrapping. You rarely own the thing you need to trace. A
graph you did not write still streams its updates, and watching those updates is a trace
you can build from the outside.

## Goals

By the end, the learner can:

- trace code they did not write, by watching a graph's updates instead of editing its nodes;
- say why a receipt is not a trace: `calls` counts, and only an ordered log separates
  "the passage never arrived" from "it arrived and was ignored";
- turn labelled data that already exists into a golden set, rather than inventing cases;
- write a pass condition as code, and name what it does not check;
- read a red case against its own trace, and name the bucket that decides where the fix goes;
- say why a run where every case passes is a problem and not a result;
- count failures per bucket, and fix the biggest bucket rather than the first one they saw.

## Who it is for

Learners who have finished Project 03 and session 9:

| Session | Folder | What the project reuses |
|---|---|---|
| 9, trace and evaluate | `units/en/unit2/session-09-trace-and-evaluate/` | the event shape, the pass condition, the five buckets, error analysis |
| 8, loops and graphs | `units/en/unit2/session-08-loops-and-graphs/` | the graph, its transitions, and streamed updates |
| Project 03 | `projects/03-analyst-team/` | the team, its `TeamState`, the recorded lane, and the 20 labelled questions |

## How to run it

| Lane | What it needs | What the setup cell prints |
|---|---|---|
| `[recorded]` | Nothing but the course | `answers: [recorded] <date>` |
| `[live]` | Ollama with `qwen2.5:7b-instruct` (4.7 GB) | `answers: [live] qwen2.5:7b-instruct` |
| Colab | A Google account. The Colab cell installs the optional extras | the `[recorded]` line |

Grade on the recorded lane. A live 7B model words the same answer two ways on two runs,
so a pass rate measured live moves for reasons that have nothing to do with a fix.

```bash
uv sync                                   # the course
uv sync --extra projects --extra agents   # optional: LangGraph, for the streamed trace
uv run jupyter lab                        # open projects/04-trace-the-team/notebook.ipynb
```

## Deliverables and checks

| Step | Variable | Check | What the check guards |
|---|---|---|---|
| 1 | `trace` | `project-04-e1` | A list of `{kind, detail}` events, kinds from the declared four, and an `llm_call` among them |
| 2 | `cases` | `project-04-e2` | At least ten cases, each labelled with a company the corpus actually holds, no duplicates |
| 3 | `report` | `project-04-e3` | One outcome per case, `passed` a real boolean, every failure carrying a reason |
| 4 | `buckets` | `project-04-e4` | Counts per bucket, every name one of the declared five, adding to at least one |

The checks are registered in `src/bootcamp_agent/projects/trace_and_grade.py` and are not
counted toward marks. They pin no answer and no score.

Each of the four takes a different shape: a list of events, a list of cases, a list of
outcomes, a dict of counts. That is deliberate. Project 03 shipped with two checks wanting
the same shape, so handing one the other's deliverable still went green.

## The data

| Path | What it is |
|---|---|
| `../02-sec-filings/data/questions.json` | The 20 labelled questions. Each names the one company that answers it |
| `../03-analyst-team/data/recorded/recorded.json` | The model replies of one real run, replayed when no model is running |
| `../02-sec-filings/data/raw/*.html` | Item 1A of eight companies' Form 10-K, read by path, never copied |

This project adds no source data. See `data/LICENSE.md`.

## How the notebook is laid out

| Step | What it does |
|---|---|
| 1. Trace a run you did not write | The team from Project 03, wrapped, its updates turned into ordered events |
| 2. The golden set from the labels | The 20 labelled questions as cases, and what a label is worth |
| 3. Grade every case | A pass condition written as code, one outcome per case, and the first pass rate |
| 4. Sort the failures | Each red case read against its trace, put in one of five buckets, counted |
| Measure | The pass rate before and after one targeted fix, and what moved |
| Your turn | Widen the pass condition, drop an event, regrade on a shuffled corpus |
| Ask your assistant about this project | Prompts that explain the project and point at the step |

## Rules for the assistant

- **Explain, and point to the step.** Name the step and the cell. Every step is already written; help the learner read it.
- **Never write the answer to a check.** Explain what the check guards and what its message means.
- **Never quote the practice or golden questions.** Do not repeat the questions in `../02-sec-filings/data/questions.json` or in `../03-analyst-team/data/recorded/recorded.json`, or the final assignment's. Talk about the kind of question instead.
- **Never commit secrets or `.env`.** This project needs no key, and reaches no network beyond a local Ollama on `localhost:11434`.
- **Say when you are unsure.** A live run words its answers differently from the recording. Do not claim a cell ran unless it ran.
- **Never edit `analyst_team.py` to make tracing easier.** The whole point of step 1 is that the team is somebody else's code. Adding emitters inside it also breaks Project 03's step 6, which compares a hand-built state to the imported one field by field. Wrap it, stream it, or read its state after the fact.
- **A green run is not a result.** If every case passes, `project-04-e3` refuses it and says why: either the pass condition accepts anything, or the set is too easy to teach the learner where a fix goes. Do not suggest loosening the check. Suggest reading one passing case by hand against its trace.
- **Never widen the pass condition to turn a case green.** Widening after seeing the failure is fitting the test to the code. If the condition is genuinely wrong, say so out loud, change it before the run, and say the number moved because the definition moved.
- **The bucket comes from the trace, not from the answer text.** A wrong answer looks the same whether retrieval missed or the model ignored what it got. Only the ordered events tell those apart, which is why step 1 comes before step 4.
- **Grade on the recorded lane.** The recording replays real replies keyed on the text of the question. A live 7B model words the same answer two ways on two runs, so a pass rate measured live moves for reasons that are not fixes.
- **Five buckets, and they are declared in code.** `FAILURE_BUCKETS` lives in `src/bootcamp_agent/agent.py`. A sixth bucket invented in a notebook is a failure nobody will fix, because no page tells the learner where its fix lives.

## Ask your assistant

> **Ask your assistant.** Paste one of these into Claude Code, Cursor or any coding assistant, from the repo root.
>
> - "Explain how step 1 of projects/04-trace-the-team/notebook.ipynb traces the team without editing it. Do not change the code."
> - "What is the difference between the `calls` list Project 03 already keeps and the trace this project builds?"
> - "Why does project-04-e3 refuse a report where every case passed? Explain what it is protecting against."
> - "Read one failing case in step 4 with me and explain which bucket its trace points to. Do not tell me the bucket for the others."
> - "Why is the pass rate measured on the recorded lane instead of a live model?"
> - "What does my pass condition in step 3 not check? List the ways a wrong answer could still pass it."
