# Project 04 — Trace the team, then grade it

Project 03 told you how often the team picked the right company. It could not tell you
why it was ever wrong. This one can.

## The brief

The desk now trusts the team enough to act on it, which means somebody eventually asks the
question you cannot answer yet: *what went wrong on that one?*

Project 03 keeps a receipt. `calls` says a model was asked three times, `stopped_because`
says the run finished, `rejected` says a citation was dropped. Every one of those is a
total. None of them says in what order anything happened, so none of them can tell the two
failures apart that look identical from the outside:

- the passage never reached the prompt, and
- the passage reached the prompt and the model ignored it.

The first is a retrieval fix. The second is a prompt fix. Guess wrong and you spend a week
in the wrong file.

So you wrap the team, record what it did in what order, grade all twenty labelled
questions against a pass condition you write down, and sort the failures into buckets.
**The bucket is the work item.** Four buckets holding one case each and one holding nine
is not five problems, it is one.

One rule shapes the whole project: **you do not edit the team.** You rarely own the code
you need to trace, and a graph you did not write still streams its updates. Watching those
updates from the outside is the skill.

## What you ship

| You deliver | Step | What it is | Check |
|---|---|---|---|
| `trace` | 1 | the ordered events of one run, each a `kind` and a `detail` | `project-04-e1` |
| `cases` | 2 | the labelled questions as a golden set, question and expected company | `project-04-e2` |
| `report` | 3 | one outcome per case: passed or not, and the reason | `project-04-e3` |
| `buckets` | 4 | how many failures fell in each of the five buckets | `project-04-e4` |

The four are four different shapes on purpose: a list of events, a list of cases, a list of
outcomes, a dict of counts. Project 03 shipped with two checks wanting the same shape, and
handing one the other's deliverable still went green. These refuse each other by name.

The checks live in `src/bootcamp_agent/projects/trace_and_grade.py`, so they are the part
you keep after the class.

## The data

Nothing new. You read Project 02's twenty labelled questions and Project 03's recording.

| Path | What it is |
|---|---|
| `../02-sec-filings/data/questions.json` | 20 questions, each labelled with the one company that answers it |
| `../03-analyst-team/data/recorded/recorded.json` | one real run's model replies, replayed offline |

## Before you start

```bash
uv sync --extra projects --extra agents
uv run jupyter lab      # open projects/04-trace-the-team/notebook.ipynb
```

Ollama is optional. **Grade on the recorded lane**: a live 7B model words the same answer
two ways on two runs, so a pass rate measured live moves for reasons that are not fixes.

## When you are done

Tick every line before you call it done.

| Check | How to tell |
|---|---|
| The team is untouched | `git status` shows no change to `src/bootcamp_agent/projects/analyst_team.py` |
| The trace is ordered | Step 1 prints retrieval before the model call, not a set of totals |
| The four checks pass | `project-04-e1` to `project-04-e4` print a tick, or a message you have read |
| Something failed | A report where everything passed is refused, and the message says why |
| Every failure has a reason | No red row in step 3 carries an empty `reason` |
| Every bucket is one of five | `retrieval`, `tool_selection`, `instruction_following`, `formatting`, `unsupported_claim` |
| You fixed the biggest bucket | The Measure table names which bucket you aimed at, and what the rate did |

## Your turn

- Widen the pass condition until a case turns green, then say out loud what you stopped
  checking. That is the trade, and it is only honest when you name it.
- Drop one event kind from the trace and re-read a red case. Which bucket can you no longer
  tell apart from which?
- Shuffle the labels so every expected company is wrong, and regrade. Anything still
  passing is measuring your code, not the team.
