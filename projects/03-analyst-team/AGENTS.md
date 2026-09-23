# Project 03 for coding assistants: The analyst team

This file tells a coding assistant what this project is and how to help with it. It
adds to the repository's root `AGENTS.md` and never overrides it.

## Purpose

The analyst from Project 02 asks for a second pair of eyes on every answer. The learner
builds the team that gives her one — a coordinator that picks the company with no model
call, a researcher that only searches, a writer that answers in strict JSON, and a critic
that approves or sends it back once — and then measures that team against the single loop
it replaces, in model calls and in routing accuracy.

## Goals

By the end, the learner can:

- read another project's index by path, and wrap it in one read-only tool;
- route a question to a company deterministically, and measure that routing on its own;
- run a team of narrow roles over one shared state, and read why a run stopped;
- count model calls per answer, and name what the extra ones bought;
- cap a reviewer at one revision, and tell a run that finished from a run that ran out;
- keep an optional framework optional: guard the import, say what was not used, and run anyway.

## Who it is for

Learners who have done Project 02 and session 8:

| Session | Folder | What the project reuses |
|---|---|---|
| 8, loops and graphs | `units/en/unit2/session-08-loops-and-graphs/` | a chain, a loop, a capped reflection, counted calls, declared transitions |
| 5, the agent loop | `units/en/unit1/session-05-agent-loop/` | stopping conditions and a budget |
| 3, typed JSON answers | `units/en/unit1/session-03-structured-outputs/` | `ANSWER_JSON_INSTRUCTIONS` and `parse_research_answer` |
| Project 02 | `projects/02-sec-filings/` | the eight filings, the 20 labelled questions, and the one-call pipeline |

## How to run it

| Lane | What it needs | What the setup cell prints |
|---|---|---|
| `[live]` | Ollama with `qwen2.5:7b-instruct` (4.7 GB) | `answers: [live] qwen2.5:7b-instruct` |
| `[recorded]` | Nothing but the course | `answers: [recorded] <date>` |
| Colab | A Google account. The Colab cell installs LangGraph and Ollama and pulls the model | the `[live]` line |

The setup cell prints a second line, `team:`, which says whether
`bootcamp_agent.projects.analyst_team` is on this clone. The notebook starts with
`# manual-run:`, so CI does not execute it.

```bash
uv sync                              # the course
uv sync --extra agents               # optional: LangGraph, for step 6
ollama pull qwen2.5:7b-instruct      # optional: without it, every model call plays the recording
uv run jupyter lab                   # open projects/03-analyst-team/notebook.ipynb
```

On a laptop, skip the Colab cell and run the setup cell after it.

## Deliverables and checks

| Step | Variable | Check | What the check guards |
|---|---|---|---|
| 1 | `search` (the function) | `project-03-e1` | It returns `(score, chunk_id, text)` triples, it can be held to one company, and it only reads |
| 3 | `routing` | `project-03-e2` | One row per labelled question, each with the predicted company, how it was decided, and the labelled truth |
| 4 | `run` (a `TeamState`) | `project-03-e3` | Every citation is a passage retrieval returned, and `stopped_because` is one of the four declared words |
| Measure | `measurement` | `project-03-e4` | Both methods, the same questions behind both rows, counted model calls |

The checks are registered in `src/bootcamp_agent/projects/analyst_team.py` and are not
counted toward marks. They pin no answer and no score.

## The data

| Path | What it is |
|---|---|
| `../02-sec-filings/data/raw/*.html` | Item 1A of eight companies' latest Form 10-K, read by path, never copied |
| `../02-sec-filings/data/questions.json` | The 20 labelled questions. Each names the one company that answers it |
| `data/recorded/` | Ours: the model replies of one real run, replayed when no model is running |

This project adds no source data. See `data/LICENSE.md`, and
`../02-sec-filings/data/LICENSE.md` for the filings themselves.

## How the notebook is laid out

| Step | What it does |
|---|---|
| 1. Build the index | Project 02's filings, by path, into one read-only `search` |
| 2. One agent, one loop | The one-call baseline, and the five questions where it retrieves the wrong company |
| 3. The coordinator | `route_company`, the Predicted against Actual table, and zero model calls |
| 4. The team | `build_team`, one run, and every field of the `TeamState` |
| 5. Fail first | A reviewer that never approves: uncapped, then capped at one revision |
| 6. The framework seam | LangGraph when it is installed, plain Python when it is not |
| Measure | The loop against the team: right company over 20, model calls over 3 |
| Your turn | Break the router, fire the critic, swap the tool |
| Ask your assistant about this project | Four prompts that explain the project and point at the step |

## Rules for the assistant

- **Explain, and point to the step.** Name the step and the cell. Every step is already written; help the learner read it.
- **Never write the answer to a check.** Explain what the check guards and what its message means.
- **Never quote the practice or golden questions.** Do not repeat the questions in `../02-sec-filings/data/questions.json` or in `data/recorded/recorded.json`, or the final assignment's. Talk about the kind of question instead.
- **Never commit secrets or `.env`.** This project needs no key, and reaches no network beyond a local Ollama on `localhost:11434`.
- **Say when you are unsure.** A live run words its answers differently from the recording. Do not claim a cell ran unless it ran.
- **Guard every LangGraph import.** LangGraph is an optional extra (`uv sync --extra agents`), not a course dependency. Any cell or module that imports it must catch `ImportError`, print what to install, and leave a plain-Python path that still runs. A notebook that only runs with an optional library installed is a notebook that does not run.
- **Never invent a citation.** The writer may cite only ids that came back in `passages`. If the learner asks for "a better-looking answer", the rule does not move: a citation retrieval never returned is the one fault this project exists to make impossible.
- **The critic gets one revision, not a conversation.** `max_revisions=1` is the design, and it is the fail-first moment in step 5. Raising it is an experiment the learner runs and measures, never a fix you suggest to make a critic happy.
- **Keep the recorded lane working.** The recording in `data/recorded/` replays real replies keyed on the text of the question. Change a prompt or a question and the key no longer matches, so the lane falls back to a stand-in refusal and the notebook says so. That is correct. If the learner wants to change a prompt, tell them first, and tell them to run live to see a real reply.

## Ask your assistant

> **Ask your assistant.** Paste one of these into Claude Code, Cursor or any coding assistant, from the repo root.
>
> - "Explain what each of the four roles in step 4 of projects/03-analyst-team/notebook.ipynb does, and which of them call a model. Do not change the code."
> - "Why does step 2 retrieve the wrong company for five of the twenty questions, and what in step 3 fixes it?"
> - "How do I run this project with no Ollama and no LangGraph, and what can that lane not do?"
> - "What is the difference between stopped_because 'answered' and 'budget', and why does a caller need both?"
