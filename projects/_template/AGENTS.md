# Project NN for coding assistants: <!-- write this: the project title -->

This file tells a coding assistant what this project is and how to help with it. It
adds to the repository's root `AGENTS.md` and never overrides it.

## Purpose

<!-- write this: two sentences. The client, and the question the project answers for them. -->

## Goals

By the end, the learner can:

- <!-- write this: one skill per line, as a verb -->
- <!-- write this -->

## Who it is for

<!-- write this: the learner this is for, and the sessions they should have done first. -->

## How to run it

| Lane | What it needs | What the setup cell prints |
|---|---|---|
| `[live]` | <!-- write this: the models and their sizes --> | <!-- write this --> |
| `[recorded]` | Nothing but the course | <!-- write this --> |
| Colab | A Google account | <!-- write this --> |

```bash
uv sync --extra projects          # write this: the extra, if the project needs it
uv run jupyter lab                # then open projects/NN-your-project/notebook.ipynb
```

## Deliverables and checks

| Variable | Check | What the check guards |
|---|---|---|
| `deliverable_1` | `project-NN-e1` | <!-- write this --> |

The checks are registered in `src/bootcamp_agent/projects/<short_name>.py` and are
not counted toward marks.

## The data

<!-- write this: the files, where they came from, and the licence. Point to data/LICENSE.md. -->

## How the notebook is laid out

| Step | What it does |
|---|---|
| 1. Load the data and look at it | <!-- write this --> |

## Rules for the assistant

- **Explain, and point to the step.** Name the step and the cell. Let the learner write the code.
- **Never write the answer to a check.** Explain what the check guards and what its message means.
- **Never quote the practice or golden questions**, from `data/` or anywhere else. Talk about the kind of question instead.
- **Never commit secrets or `.env`.** This project needs no key.
- **Say when you are unsure.** Do not claim a cell ran unless it ran.
- **Keep the recorded lane working.** <!-- write this: what in this project the recorded lane depends on, and what change would break it -->

## Ask your assistant

> **Ask your assistant.** Paste one of these into Claude Code, Cursor or any coding assistant, from the repo root.
>
> - "Explain what projects/NN-your-project/notebook.ipynb builds, step by step. Do not change the code."
> - "How do I run this project on the recorded lane, and how on the live lane?"
