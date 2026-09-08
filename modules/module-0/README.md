# Week 0 — the prerequisite

A fast lane of four units, self-paced, about **45 minutes each**, and beside
it the long-form courses in the DataCamp lesson shape. Do the fast lane before
Monday 14 September. Nothing in the fifteen sessions waits for you to finish,
but session 1 assumes the floor these units build.

Everything runs offline. No API key, no cloud account, no cost.

Short on time? Do units 1–4 and come back for the courses.

## The fast lane

| # | Unit | The thing you leave with |
|---|---|---|
| 1 | [The environment](unit-01-environment/) | Which Python is running, why it must be the one `uv` made, and the four-line walk every notebook here opens with |
| 2 | [Packages and documentation](unit-02-packages-and-docs/) | How to read `bootcamp_agent` rather than guess at it, and what a docstring owes a caller |
| 3 | [Classes and contracts](unit-03-classes-and-contracts/) | Enough dataclass to read the typed contracts the course is built on, and the two mistakes that bite hardest |
| 4 | [Calling a real API](unit-04-real-apis/) | A call built right the first time, and what a specification does **not** tell you |

Take them in order. Unit 1 fixes the setup problem that otherwise ruins unit 2.

## Course A — Software engineering foundations

Four units, about **60 minutes each**, one per chapter of the DataCamp course
*Software Engineering Principles in Python*, translated and pointed at this
repo. Each unit has slides, a notebook and a solutions notebook.

| # | Unit | The thing you leave with |
|---|---|---|
| 5 | [Packages, PyPI and PEP 8](unit-05-packages-and-pep8/) | `help()` before you call, `ruff` before you share, and the three shapes modular Python comes in |
| 6 | [A portable package](unit-06-portable-packages/) | A requirement that pins and one that floats, a package a script can import, and the docstring `help()` shows |
| 7 | [Classes in a package](unit-07-classes-in-packages/) | A class that keeps its docstring's promise, inheritance that calls the parent, and the `_` that marks a method non-public |
| 8 | [Documentation, tests and readability](unit-08-docs-tests-readability/) | A docstring `doctest` can run, a `pytest` file that goes red then green, and a name that says what the function is for |

## Course B — MCP: AI apps as easy as 1, 2, 3

Three units, about **60 minutes each**, one per chapter of the DataCamp course
*Introduction to Model Context Protocol*. You write a real server and talk to
it with a real client. Everything runs offline: the conversion behind the tool
is computed locally from a recorded table of zone offsets, the model in the
loop is the repo's deterministic fake, and the third-party surface is a
recorded tool list, so no key and no network are needed.

| # | Unit | The thing you leave with |
|---|---|---|
| 9 | [Your first MCP server](unit-09-mcp-first-server/) | A tool whose hints are its schema and whose docstring is its description, a client that starts it over stdio, and one call made with the argument names the schema declares |
| 10 | [Resources, prompts, and the LLM](unit-10-mcp-resources-prompts-llms/) | A resource that lists one thing per line, a prompt whose name is not its title, a five-step tool call whose result reaches the model, and a clarifying question where a converted time would have been a guess |
| 11 | [Databases, APIs, and third-party servers](unit-11-mcp-data-apis-third-party/) | A query the caller cannot finish writing, a credential the client never sees, and the three questions to ask a server somebody else runs |

## Course C — Data structures for agents

One unit, about **60 minutes**, four lessons. Every example is the course's
own data: the corpus, the golden set, the agent loop, and the storefront
program graph session 13 walks.

| # | Unit | The thing you leave with |
|---|---|---|
| 12 | [Data structures for agents](unit-12-dsa-for-agents/) | A lookup you timed before trusting it, a dedupe that keeps the order seen, a tree walk that stops at its budget, and a derive order that is a topological sort, or `None` on a cycle |

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
