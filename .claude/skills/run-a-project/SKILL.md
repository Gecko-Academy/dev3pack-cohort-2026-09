---
name: run-a-project
description: Use when a learner opens one of the optional projects under projects/. Installs both extras in one command, pulls the right local models, and reads the live or recorded lane off the first line of output. Never writes the project's answers.
---

# Run an optional project

## When to use

The learner wants to run something in `projects/`: the clothing reviews, the SEC
filings, or the analyst team. These are optional and **never counted**. Nothing
here affects a grade or the certificate.

Say that out loud once, at the start. A learner who thinks a project is graded
will rush it, and rushing is the opposite of the point.

## Install, once, and name both extras

```bash
uv sync --extra projects --extra agents
```

Both, in one command, every time.

`uv sync` syncs the environment **exactly**: it installs what you name and
uninstalls what you do not. Name only one of those two extras and the other is
removed, taking ChromaDB with it. The projects that index into ChromaDB then
fail with an import error that looks like a broken install. It is not broken. It
was uninstalled by the last sync. Name both.

## Pull the models

```bash
ollama pull nomic-embed-text       # 274 MB, turns text into vectors
ollama pull qwen2.5:7b-instruct    # 4.7 GB, writes the answers
ollama list                        # both must appear here
```

`nomic-embed-text` is the embedding model, used wherever a project builds an
index. `qwen2.5:7b-instruct` is the chat model, used where a project needs
sentences written. A project that does neither needs neither.

## Read the first line of output

The setup cell prints the lane before anything else runs:

| Line | What it means |
|---|---|
| `[live]` and a model name | Ollama answered. The output is generated on this machine, now. |
| `[recorded]` and a date | No model was reachable, so the notebook replays one real run captured on that date. |

`[recorded]` is not a failure and not a downgrade of the lesson. Every step
still runs, and a small laptop can do the whole project. The one thing it cannot
do is answer a question the recording does not contain: the notebook says so
when that happens. If the learner wants to ask their own questions, they need
the model pulled and Ollama running, which puts them on `[live]`.

If the lane says `[recorded]` and the learner expected `[live]`, check that
Ollama is running and that `ollama list` shows the model.

## While working

- Each project folder has its own `AGENTS.md` and `README.md`. Read them first.
  They say what the project is for and how it runs.
- Run the cells from the top, in order. After changing an imported file, restart
  the kernel.
- Open a notebook with `uv run jupyter lab`.

## Never

- Never write the project's answers or its conclusions for the learner. The
  project asks them to look at real data and say what they see. Explain the
  idea, name the page or the README section that teaches it, and let the learner
  write it. The same rule covers any `TODO(you)` cell inside a project.
- Never suggest a project instead of a session exercise to raise a score. A
  project is never counted.
- Never add a dependency the project does not ask for.
