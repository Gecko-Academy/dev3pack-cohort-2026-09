# Week 0 — the prerequisite

Four units, self-paced, about **45 minutes each**. Do them before Monday
14 September. Nothing in the fifteen sessions waits for you to finish, but
session 1 assumes the floor these units build.

Everything runs offline. No API key, no cloud account, no cost.

## The units

| # | Unit | The thing you leave with |
|---|---|---|
| 1 | [The environment](unit-01-environment/) | Which Python is running, why it must be the one `uv` made, and the four-line walk every notebook here opens with |
| 2 | [Packages and documentation](unit-02-packages-and-docs/) | How to read `bootcamp_agent` rather than guess at it, and what a docstring owes a caller |
| 3 | [Classes and contracts](unit-03-classes-and-contracts/) | Enough dataclass to read the typed contracts the course is built on, and the two mistakes that bite hardest |
| 4 | [Calling a real API](unit-04-real-apis/) | A call built right the first time, and what a specification does **not** tell you |

Take them in order. Unit 1 fixes the setup problem that otherwise ruins unit 2.

## How to run one

```bash
uv sync --group dev
uv run jupyter lab        # then open modules/module-0/unit-01-environment/notebook.ipynb
```

Each notebook opens with the same preflight the whole course uses, so a broken
environment tells you what to fix instead of failing three cells later.

## Some cells ship broken. That is deliberate.

You will see this:

```python
result = "a" + "b"  # <------ EDIT THIS LINE
```

**Run it first.** The cell works and gives the wrong answer, and working out why
teaches more than filling in a blank. Every one of these is a mistake people
actually make, including one that hangs a notebook forever until you find the
stopping condition.

## When you get stuck

Three levels, and you can have any of them whenever you want:

| Call | What you get | Cost |
|---|---|---|
| `check("w01-e2", locate_repo_root)` | the verdict, and the fix, named | free |
| `hint("w01-e2")` | the next nudge | 30 marks |
| `hint("w01-e2", reveal=True)` | the worked answer, and why | 70 marks |
| `review("w01")` | the scorecard for this unit | free |

Nothing is locked. If you want the answer immediately you can have it
immediately — the scorecard simply says so. Asking twice never costs twice.

An exercise you passed after a hint is worth more than one you skipped, and the
point of the number is to show you where to spend another ten minutes, not to
rank anybody.

## Your progress stays on your machine

One SQLite file at `~/.bootcamp/progress.db`. It records exercise ids, whether
they passed, how many attempts, and whether you took help.

It does **not** record your answers, your name, your email, or anything you
typed, and nothing is sent anywhere. If you want to share your progress you run
`bootcamp progress --export` and send the file yourself.

That is the same retention rule the optional depth track makes you write down
for your own system, and it would be a poor course that taught a policy it did
not keep.

## What comes next

Session 1 opens on **Monday 14 September**. The fifteen sessions are in
[`modules/module-1`](../module-1/), [`module-2`](../module-2/) and
[`module-3`](../module-3/), and they arrive one week at a time — run `git pull`
each Monday.
