---
name: ship-my-capstone
description: Use when a learner wants to start, grade, hand in, or check the score of their capstone (the final assignment). Walks clone and make it yours, grade, submit and the score file with the exact commands. Never writes the learner's agent for them.
---

# Create, grade, submit, and read the score

## When to use

The learner says "start my capstone", "grade my capstone", "submit the final",
"where is my score", or pastes an error from `bootcamp capstone`. The full
tutorial, with every step explained, is `CAPSTONE.md` in the learner's capstone
repository (https://github.com/Gecko-Academy/Dev3Pack-Gecko-Capstone-Project/blob/main/CAPSTONE.md).
Read it before you start, and send the learner to it.

## Two repositories, and they are easy to mix up

| Repository | What it is | How it is handed in |
|---|---|---|
| the course clone, `dev3pack-cohort-2026-09` | lessons and session notebooks | `uv run bootcamp submit chNN --github LOGIN --push`, from the course clone |
| `my-capstone` | the learner's own public repository with their agent | `uv run bootcamp capstone submit --github LOGIN`, from inside `my-capstone` |

Ask which one the learner is in before running anything. `pwd` and
`git remote -v` answer it.

## 1. Clone it and make it yours

Beside the course clone, never inside it:

```bash
git clone https://github.com/Gecko-Academy/Dev3Pack-Gecko-Capstone-Project.git my-capstone
cd my-capstone
git remote rename origin upstream
gh repo create my-capstone --public --source . --remote origin --push
uv sync
```

`uv.lock` is already committed, so `uv sync` leaves nothing to commit. If
`git remote -v` shows `origin` at `Gecko-Academy/...`, the learner skipped "make it
yours" and `capstone submit` refuses. No `gh`? Create an empty public repository at
https://github.com/new, then `git remote add origin ...` and `git push -u origin main`.

## 2. An older repository

A repository made earlier with `uv run bootcamp capstone new` still works. If
`submit` refuses with `?? uv.lock`, commit `uv.lock` and push.

## 3. Practise

- The contract tests: the command is in step 5 of the tutorial. They live in
  the capstone repository, not in the course clone.
- The practice grader: `uv run bootcamp capstone grade`. Its report goes to
  `score_report.json`, which is gitignored, so it never dirties the tree.
- One question, every step: `uv run bootcamp capstone trace "the question"`.

With no `.env`, the agent runs on the offline fake model: about 30%, `NOT YET`,
and `critical safety gate failed`. That is the starting line, not a bug. A real
score needs a real model in `.env` inside `my-capstone`: `BOOTCAMP_PROVIDER`
(`anthropic`, `openai` or `ollama`), `BOOTCAMP_MODEL`, and the key the provider
needs (`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`; `OPENAI_BASE_URL` for an
OpenAI-compatible service; Ollama needs no key). Never read, print or paste the
learner's `.env`. Ask them to edit it.

## 4. Submit (inside my-capstone)

Commit and push first. Then:

```bash
export DEV3PACK_API_BASE=https://app.geckovision.tech
uv run bootcamp capstone submit --github LOGIN --dry-run
uv run bootcamp capstone submit --github LOGIN
```

`LOGIN` is the GitHub login from the profile URL. Before anything runs,
`submit` checks that the repository has a commit, nothing uncommitted, an
`origin` on GitHub, and that the last commit is pushed. Then three steps:
`1/3` the practice set locally, `2/3` the final questions, `3/3` the bundle and
the pull request to `Gecko-Academy/dev3pack-submissions`, under
`submissions/LOGIN/final/`. `--dry-run` does everything except the pull
request, and writes the bundle to a temporary folder.

Read the `1/3` lines with the learner. If they say `WARNING: this run uses the
fake model`, stop and ask whether they meant that.

## 5. Read the score

The score is not printed by `submit`. After the pull request merges, a workflow
in the submissions repository scores the answers and commits
`finals/LOGIN/result.json`:

```
https://github.com/Gecko-Academy/dev3pack-submissions/blob/main/finals/LOGIN/result.json
```

Read `score`, `passed` and `certificate_eligible` with the learner, and the
per-question verdicts in `results`. A new submission replaces the file. If the
pull request shows merged and the file is not there, tell the learner to
report it to the instructor rather than resubmit.

## When a command refuses

Every refusal says what to run next. Read it out, then do that. The common ones
are in the troubleshooting table at the end of the tutorial.

## Never

- Never write the learner's `agent.py`, and never write into a `TODO(you)` cell
  in the capstone notebook. Explain the idea, name the session page that teaches
  it, and let the learner write it. The defence is six minutes of explaining
  their own code.
- Never run `submit` without the learner reading the `1/3` output first.
- Never commit for the learner without showing them the diff.
- Never read, print or commit `.env`.
- Never open a `solutions/` directory.
