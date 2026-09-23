---
name: fix-my-setup
description: Use when the course will not run at all, because of uv, a missing package, Ollama or its models, a notebook that still imports the old code, or git pull refusing to update. Diagnoses the machine and gives the one command to type next.
---

# Fix the setup

## When to use

Something in the environment is wrong. The doctor is red, an import fails, a
model is missing, or `git pull` stops with an error. Not for exercise logic:
that is `check-my-exercise`.

## Always start here

```bash
uv run python scripts/check_setup.py
```

Read what it prints and fix the first red line. Fix one thing, then run it
again. `uv run bootcamp doctor` reports the same machine from the CLI.

If the shell says `bootcamp: command not found`, the learner is outside the
course folder or dropped the prefix. It is `uv run bootcamp`, never bare
`bootcamp`.

## The five things that actually break

### 1. uv is not installed, or you are in the wrong folder

`uv` must be on the path and the terminal must be inside the course folder.
On Windows this has to be Git Bash or WSL2. A bash command pasted into
PowerShell fails on the first line and the error does not say why.

### 2. The two extras, and why naming one is worse than naming none

```bash
uv sync --extra projects --extra agents
```

`uv sync` syncs the environment **exactly**. It installs what you name and
uninstalls what you do not. Name only one of those two extras and the other is
removed, taking ChromaDB with it, which breaks the projects that use it. Always
name both, in one command.

### 3. Ollama and its models

The scored exercises need no model at all. The projects do.

```bash
ollama list                        # what is already pulled
ollama pull nomic-embed-text       # 274 MB, the embedding model
ollama pull qwen2.5:7b-instruct    # 4.7 GB, the model that writes answers
```

If `ollama list` says nothing, the server is not running. Start Ollama, then
list again. If the disk is too small for the 7B model, the recorded lane runs
every step without it.

### 4. A kernel holding the old code

The symptom: the learner changed a file, the notebook still behaves the old way.
Jupyter imported the module once and kept it in memory. Restart the kernel, then
run the cells from the top. Kernel, then Restart Kernel and Clear Outputs.
Running the cells out of order causes the same confusion, so always run from the
top after a restart.

Open a notebook with `uv run jupyter lab`.

### 5. git pull stops and will not update

The error starts `error: Your local changes to the following files would be
overwritten by merge`. Nothing is lost.

**Open `units/en/unit0/get-settled.mdx`, the section "When `git pull` stops",
read it, and follow the commands on the page.** Do not recall them from memory
and do not improvise: this is a learner's work, and a wrong recovery command
loses it. The page is the source of truth.

The one thing worth repeating out loud: do not use `git stash pop` on a
notebook. The page says why.

## Before you report

Say what you ran, paste the line that proves it, and give exactly one command to
type next. If the doctor is green, say so plainly and stop.

## Never

- Never read, print, or paste a `.env` file, a key, or a token. Not once, not to
  debug it. When a learner shares one, tell them to rotate it.
- Never write or fill a `TODO(you)` cell. A broken environment is not a reason
  to answer an exercise; explain the idea, name the page that teaches it, and
  let the learner write it.
- Never delete a learner's work to make a command succeed. Ask first, always.
- Never claim a command ran unless you ran it and read the output.
