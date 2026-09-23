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
- read an output contract line by line, and say what each verb makes the model do;
- write the prompts a role sends, and name the word in one of them that the code reads;
- build a team by hand, four node functions over one transition dict, before importing the
  built one, and say what `build_team` does because they wrote it;
- write tools as a real Python package inside the project, import it, and hand its registry
  to one role;
- give a researcher more than one tool and a rule that picks between them, including one
  optional tool that leaves the machine, and say why it stays out of the measurement;
- say which role may hold which tool, and what breaks when the writer holds one;
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
| 4, bounded tools | `units/en/unit1/session-04-bounded-tools/` | what a tool is, its narrow contract, and who may hold one |
| 3, typed JSON answers | `units/en/unit1/session-03-structured-outputs/` | `ANSWER_JSON_INSTRUCTIONS` and `parse_research_answer` |
| Project 02 | `projects/02-sec-filings/` | the eight filings, the 20 labelled questions, and the one-call pipeline |

## How to run it

| Lane | What it needs | What the setup cell prints |
|---|---|---|
| `[live]` | Ollama with `qwen2.5:7b-instruct` (4.7 GB) | `answers: [live] qwen2.5:7b-instruct` |
| `[recorded]` | Nothing but the course | `answers: [recorded] <date>` |
| Colab | A Google account. The Colab cell installs the optional extras and Ollama and pulls the model | the `[live]` line |

The setup cell prints a second line, `team:`, which says whether
`bootcamp_agent.projects.analyst_team` is on this clone. The notebook starts with
`# manual-run:`, so CI does not execute it.

```bash
uv sync                                  # the course
uv sync --extra projects --extra agents   # optional: LangGraph (step 12) and the web tool (step 10)
ollama pull qwen2.5:7b-instruct          # optional: without it, every model call plays the recording
uv run jupyter lab                       # open projects/03-analyst-team/notebook.ipynb
```

On a laptop, skip the Colab cell and run the setup cell after it.

## Deliverables and checks

| Step | Variable | Check | What the check guards |
|---|---|---|---|
| 1 | `search` (the function) | `project-03-e1` | It returns `(score, chunk_id, text)` triples, it can be held to one company, and it only reads |
| 3 | `routing` | `project-03-e2` | One row per labelled question, each with the predicted company, how it was decided, and the labelled truth |
| 7 | `run` (a `TeamState`) | `project-03-e3` | Every citation is a passage retrieval returned, and `stopped_because` is one of the four declared words |
| Measure | `measurement` | `project-03-e4` | Both methods, the same questions behind both rows, counted model calls |

The checks are registered in `src/bootcamp_agent/projects/analyst_team.py` and are not
counted toward marks. They pin no answer and no score.

## The data

| Path | What it is |
|---|---|
| `../02-sec-filings/data/raw/*.html` | Item 1A of eight companies' latest Form 10-K, read by path, never copied |
| `../02-sec-filings/data/questions.json` | The 20 labelled questions. Each names the one company that answers it |
| `data/recorded/` | Ours: the model replies of one real run, replayed when no model is running |
| `analyst_tools/` | Ours: the tool package step 9 writes and step 10 adds to. The notebook rewrites these files when it runs, so they are the same bytes either way |

This project adds no source data. See `data/LICENSE.md`, and
`../02-sec-filings/data/LICENSE.md` for the filings themselves.

## How the notebook is laid out

| Step | What it does |
|---|---|
| 1. Build the index | Project 02's filings, by path, into one read-only `search` |
| 2. One agent, one loop | The one-call baseline, and the five questions where it retrieves the wrong company |
| 3. The coordinator | `route_company`, the Predicted against Actual table, and zero model calls |
| 4. The output contract | `ANSWER_JSON_INSTRUCTIONS` line by line, four malformed replies, and the parser as the boundary |
| 5. Every prompt in the open | Both system prompts, both user messages, and the `APPROVE` token the code reads |
| 6. Build the team by hand | Four node functions, one transition dict, a nine-line walker, then `build_team` beside it |
| 7. The team | `build_team`, one run, and every field of the `TeamState` |
| 8. Fail first | A reviewer that never approves: uncapped, then capped at one revision |
| 9. Tools as a package | `analyst_tools/` written from a cell, imported, and read as a registry |
| 10. More than one tool | A rule that chooses, a DuckDuckGo tool through LangChain, and its three states |
| 11. Which role gets which tools | The per-role allow-list, and why the writer's row is empty |
| 12. The framework seam | LangGraph when it is installed, plain Python when it is not |
| Measure | The loop against the team: right company over 20, model calls over 3 |
| Your turn | Break the router, fire the critic, swap the tool, write a fourth one |
| Ask your assistant about this project | Prompts that explain the project and point at the step |

## Rules for the assistant

- **Explain, and point to the step.** Name the step and the cell. Every step is already written; help the learner read it.
- **Never write the answer to a check.** Explain what the check guards and what its message means.
- **Never quote the practice or golden questions.** Do not repeat the questions in `../02-sec-filings/data/questions.json` or in `data/recorded/recorded.json`, or the final assignment's. Talk about the kind of question instead.
- **Never commit secrets or `.env`.** This project needs no key, and reaches no network beyond a local Ollama on `localhost:11434`.
- **Say when you are unsure.** A live run words its answers differently from the recording. Do not claim a cell ran unless it ran.
- **Guard every LangGraph import.** LangGraph is an optional extra (`uv sync --extra projects --extra agents`), not a course dependency. Any cell or module that imports it must catch `ImportError`, print what to install, and leave a plain-Python path that still runs. A notebook that only runs with an optional library installed is a notebook that does not run.
- **Never invent a citation.** The writer may cite only ids that came back in `passages`. If the learner asks for "a better-looking answer", the rule does not move: a citation retrieval never returned is the one fault this project exists to make impossible.
- **The critic gets one revision, not a conversation.** `max_revisions=1` is the design, and it is the fail-first moment in step 8. Raising it is an experiment the learner runs and measures, never a fix you suggest to make a critic happy.
- **The web tool is optional, guarded, and never in a number.** The DuckDuckGo tool in step 10 must build on every machine and refuse with a `ToolError` naming `uv sync --extra projects --extra agents` when the dependency is absent. Never put its results in the Measure table: a web result is not reproducible, the endpoint rate-limits, and its scores are positions in a list rather than anything our index computed.
- **The writer holds no tools.** `project-03-e3` compares every citation against the passages retrieval returned, and that comparison only exists while the writer's evidence is fixed by somebody else. If a learner asks to give the writer a search tool, say what it costs: the check stops being possible, not just weaker.
- **One list of questions.** Every question this notebook asks a model lives in `analyst_team.DEMO_QUESTIONS`, read in the notebook as `DEMO` and imported by `data/recorded/record.py`. Never type a question into a cell that calls a model: two copies drift, the drifted one replays as a refusal, and the notebook still prints something that looks like an answer. Two tests hold this.
- **The slow LangGraph build lives in a tutorial.** `projects/tutorials/03-build-a-team-with-langgraph.ipynb` is where the state, the reducer, the roles as data, one node per prompt, the wiring, the drawn graph and the streamed run are walked through. Step 12 here shows the graph and links there; do not move that material back into this notebook.
- **Keep the recorded lane working.** The recording in `data/recorded/` replays real replies keyed on the text of the question. Change a prompt or a question and the key no longer matches, so the lane falls back to a stand-in refusal and the notebook says so. That is correct. If the learner wants to change a prompt, tell them first, and tell them to run live to see a real reply.

## Ask your assistant

> **Ask your assistant.** Paste one of these into Claude Code, Cursor or any coding assistant, from the repo root.
>
> - "Explain what each of the four roles in step 7 of projects/03-analyst-team/notebook.ipynb does, and which of them call a model. Do not change the code."
> - "Why does step 2 retrieve the wrong company for five of the twenty questions, and what in step 3 fixes it?"
> - "How do I run this project with no Ollama and no LangGraph, and what can that lane not do?"
> - "In step 6 I write the team by hand. Compare my four node functions with build_team and name every difference. Do not change the code."
> - "Explain how the tool package in step 9 is imported, and why the web tool in step 10 is not in the Measure table."
> - "What is the difference between stopped_because 'answered' and 'budget', and why does a caller need both?"
> - "Draw the team's graph for me from step 12, and say which edge goes backwards and what it costs."
