---
name: ship-my-capstone
description: Use when a learner wants to start, grade, hand in, or check the score of their final assignment (the research assistant, graded privately, which earns the certificate). Walks final new, publish, grade, submit and the score file with the exact commands. Never writes the learner's agent for them.
---

# Create, grade, submit, and read the score

## When to use

The learner says "start my final assignment", "grade my agent", "submit the
final", "where is my score", or pastes an error from `bootcamp final` or
`bootcamp capstone` (the older name of the same command). The full tutorial,
with every step explained, is `units/en/unit3/final-assignment.mdx` in the
course folder. Read it before you start, and send the learner to it.

**The final assignment is not the Gecko capstone.** The final assignment is the
research assistant: graded on a private question set, it earns the certificate.
The Gecko capstone is the store project presented on Friday 2 October, in
https://github.com/Gecko-Academy/Dev3Pack-Gecko-Capstone-Project. This skill is
only about the final assignment. If the learner means the store project, say so
and send them to that repository.

## Two repositories, and they are easy to mix up

| Repository | What it is | How it is handed in |
|---|---|---|
| the course clone, `dev3pack-cohort-2026-09` | lessons, session notebooks and the `cap01` notebook | `uv run bootcamp submit chNN --github LOGIN --push`, from the course clone |
| `my-final-assignment` | the learner's own public repository with their agent | `uv run bootcamp final submit --github LOGIN`, from inside `my-final-assignment` |

Ask which one the learner is in before running anything. `pwd` and
`git remote -v` answer it.

## 1. Create it and publish it

From the course clone, so the new folder sits beside it, never inside it:

```bash
uv run bootcamp final new ../my-final-assignment
cd ../my-final-assignment
uv sync
git add uv.lock && git commit -m "Lock the course package"
gh repo create my-final-assignment --public --source . --push
```

`uv sync` writes `uv.lock`, and `submit` refuses a repository with it
uncommitted, so commit it before publishing. No `gh`? Create an empty public
repository at https://github.com/new, then `git remote add origin ...` and
`git push -u origin main`. If `git remote -v` shows `origin` at
`Gecko-Academy/...`, `submit` refuses: the learner is in a course repository,
not their own.

## 2. An older repository

A repository made earlier with `uv run bootcamp capstone new` is the same thing
under the older name, and still works. If `bootcamp final` says
`invalid choice: 'final'`, that repository pins a course from before the alias:
use `bootcamp capstone ...`, or update the course with
`uv lock --upgrade-package dev3pack-bootcamp-ai-engineering`. If `submit`
refuses with `?? uv.lock`, commit `uv.lock` and push.

## 3. Practise

- The contract tests: the command is in section 6 of the tutorial. They live in
  `my-final-assignment`, not in the course clone.
- The practice grader: `uv run bootcamp final grade`. Its report goes to
  `score_report.json`, which is gitignored, so it never dirties the tree.
- One question, every step: `uv run bootcamp final trace "the question"`.

With no `.env`, the agent runs on the offline fake model: `score: 3/10 (30%)`,
`NOT YET`, and `critical safety gate failed`. That is the starting line, not a
bug. A real score needs a real model in `.env` inside `my-final-assignment`:
`BOOTCAMP_PROVIDER` (`anthropic`, `openai` or `ollama`), `BOOTCAMP_MODEL`, and
the key the provider needs (`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`;
`OPENAI_BASE_URL` for an OpenAI-compatible service; Ollama needs no key). Never
read, print or paste the learner's `.env`. Ask them to edit it.

## 4. Submit (inside my-final-assignment)

Commit and push first. Then:

```bash
export DEV3PACK_API_BASE=https://app.geckovision.tech
uv run bootcamp final submit --github LOGIN --dry-run
uv run bootcamp final submit --github LOGIN
```

`LOGIN` is the GitHub login from the profile URL. Before anything runs,
`submit` checks that the repository has a commit, nothing uncommitted, an
`origin` on GitHub that is the learner's, and that the last commit is pushed.
Then three steps: `1/3` the practice set locally, `2/3` the final questions,
`3/3` the bundle and the pull request to `Gecko-Academy/dev3pack-submissions`,
under `submissions/LOGIN/final/`. `--dry-run` does everything except the pull
request, and writes the bundle to a temporary folder.

Read the `1/3` lines with the learner. If they say `WARNING: this run uses the
fake model`, stop and ask whether they meant that: the fake scores 4/15 (27%)
on the final set and fails both gates.

## 5. Read the score

The score is not printed by `submit`. After the pull request merges, a workflow
in the submissions repository scores the answers and commits
`finals/LOGIN/result.json`:

```
https://github.com/Gecko-Academy/dev3pack-submissions/blob/main/finals/LOGIN/result.json
```

Read `score`, `passed` and `certificate_eligible` with the learner, and the
per-question verdicts in `results`. A pass needs a score of at least 30% **and**
every critical question. The final set has 15 questions, 6 of them critical, so
any pass is at least 6/15 (40%). A new submission replaces the file: the latest
submission counts, not the best. If the pull request shows merged and the file
is not there, tell the learner to report it to the instructor rather than
resubmit.

## When a command refuses

Every refusal says what to run next. Read it out, then do that. The common ones
are in the troubleshooting table at the end of the tutorial.

## Never

- Never write the learner's `agent.py`, and never write into a `TODO(you)` cell
  in the `cap01` notebook. Explain the idea, name the session page that teaches
  it, and let the learner write it. The certificate says they built it.
- Never run `submit` without the learner reading the `1/3` output first.
- Never commit for the learner without showing them the diff.
- Never read, print or commit `.env`.
- Never open a `solutions/` directory.
