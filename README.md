<p align="center"><img src=".github/assets/banner.svg" alt="Dev3Pack AI-Engineering Bootcamp — from an LLM call to a verified agent" width="100%" /></p>

# Dev3Pack AI-Engineering Bootcamp

[![CI](https://github.com/ernanibmurtinho/Dev3Pack-bootcamp-AI-Engineering/actions/workflows/test.yml/badge.svg)](https://github.com/ernanibmurtinho/Dev3Pack-bootcamp-AI-Engineering/actions/workflows/test.yml)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![uv](https://img.shields.io/badge/uv-managed-6e56cf)
![License](https://img.shields.io/badge/license-MIT-blue)
![Claude Code](https://img.shields.io/badge/Claude_Code-ready-orange)

A three-week, practice-first bootcamp on building small, reliable agentic
applications — **September 14 – October 2, 2026**, Monday–Friday, 2-hour sessions,
with an optional showcase on **Saturday, October 3**. For developers who can write
Python and want to go from "I called an LLM once" to "I shipped an agent I can
test, trace, and trust."

Every session builds toward one capstone: a source-grounded research assistant
that cites what it read and refuses what it can't support. You leave knowing how
to configure a coding assistant for a repo, put an LLM behind a provider seam,
validate structured outputs, ground answers with retrieval, bound an agent's
tools, evaluate its behavior, package a skill, and connect it to an external API
surface through **MCP and Gecko** — safely.

## What This Is

- **15 sessions** of 2 hours each, every one with a guide and Marp slides;
  sessions 1–14 add an exercise notebook plus an executable solutions notebook
  (session 15 is demo day)
- **One capstone** — a source-grounded developer research assistant;
  `src/bootcamp_agent/` is its final shape, which you rebuild piece by piece
  in the session notebooks
- **3 concept guides** that thread the whole course: loop, graph, and harness
  engineering
- **10-notebook Gecko cookbook** — from comprehending an OpenAPI spec to a full
  verified loop against an instructor-hosted fork
- **3 project workspaces** (one per week, DataCamp-style: brief, chapters,
  open coding) — capped by the Autonomous Store: Waiter, Store Manager, and
  Delivery agents on LetMeBuy-shaped rails
- **A graded final assignment with a signed certificate** — HF-agents-course
  style: a template agent you improve, a question set you're scored on, a pass
  bar of 70%, and an instructor-issued certificate with a verification code
- **3 real-stack integrations** — SendAI's Agent Kit on devnet (real txs),
  Hermes on Telegram, and the Gecko × Orquestra cross-runtime test matrix
- **A builder kit** — this repo is a Claude Code plugin marketplace: the
  store-builder and corpus-answers skills plus `/bootcamp-doctor`
- **A setup doctor and a notebook checker**, both wired into CI
- **88 deterministic tests** — FakeLLM by default, no API key, no network
- **A local-model lane** — `BOOTCAMP_PROVIDER=ollama` runs a real model on
  your machine with no key and no SDK (the doctor checks server and model)

## Quick Start

Do this **before September 14** — full instructions in [`SETUP.md`](SETUP.md):

```bash
# The repository is private. Send us the email on your GitHub account, accept
# the invitation, then:
git clone git@github.com:Gecko-Academy/dev3pack-cohort-2026-09.git
cd dev3pack-cohort-2026-09
uv sync --group dev
cp .env.example .env
uv run pytest -q
uv run python scripts/check_setup.py     # the doctor — screenshot the green output
uv run bootcamp-agent "What are structured outputs?"
```

No API key is needed until you make live model calls: tests, the doctor, and
every notebook default to a deterministic offline `FakeLLM`.

**Access and weekly releases.** The repository is private and you are invited by
email, so send us the address on your GitHub account. You get **read** access,
which means nothing you do can break the course for anyone else. The repository
**grows each week**: week 1 is there on day one, week 2 arrives on the Monday of
week 2. Run `git pull` at the start of each week. Full detail, including how to
back up your own work, is in [`SETUP.md`](SETUP.md).

## Checking Your Own Work

Every exercise notebook ends each exercise with a `check("chNN-eN", value)` cell
and closes with `review("chNN")`. The checks judge **behaviour, not wording**:
they re-run retrieval, count model calls, rerun the evaluator, or call the
function you wrote. There is no answer key to read, and no way to pass one by
matching a string.

You do not need Jupyter open to see where you stand:

```bash
uv run bootcamp doctor          # this machine: Python, kernel, corpus, model lane
uv run bootcamp check ch03      # run one chapter and print its scorecard
uv run bootcamp progress        # every chapter, one tally
```

`bootcamp check` prints exactly what the notebook prints, so the terminal and
Jupyter never disagree:

```
running ch01 (Orientation: from LLM calls to agentic systems)…
ch01: 0/3 passed
❌ ch01-e1: expected a list of exactly three replies; hint: one call per question
❌ ch01-e2: runs['live'] must hold exactly two replies
❌ ch01-e3: 'review_when' needs one full sentence (20+ characters); hint: be concrete
```

That is the correct output before you start. Zero is the honest score for an
untouched notebook, and each ❌ names the next thing to do.

Two things that are not failures. A few cells are **checkpoints** rather than
exercises: they verify machinery the repo already ships, so they are green the
first time you run them, and their expected-output block shows them green.
And three sessions are marked `in Jupyter` by `bootcamp progress`, because they
need you or an instructor-hosted surface rather than an unattended run.

The full day-by-day table, with each session's check count, is generated from
the code in [`docs/course-index.md`](docs/course-index.md).

## Going Deeper (optional)

The fifteen sessions teach AI engineering. The software engineering underneath
it — APIs and boundaries, data lifecycles, architecture decisions, reliability,
and operating in production — lives in [`depth/`](depth/) as five optional
self-paced modules.

Nothing in the course depends on them and nothing there is graded. They exist
because a coding agent will write the endpoint for you but will not decide
whether the trace belongs in the response. Same `check()` harness, same offline
`FakeLLM`, roughly 45 minutes each.

## Schedule

| Week | Dates | Focus | Sessions |
|---|---|---|---|
| 1 | Sep 14–18 | Foundations and assistant setup | [1–5](modules/module-1/) |
| 2 | Sep 21–25 | Retrieval, agents, reliability, skills | [6–10](modules/module-2/) |
| 3 | Sep 28–Oct 2 | Production thinking, Gecko, capstone | [11–15](modules/module-3/) |
| — | Oct 3 (optional) | Showcase and office hours | — |

The full class-by-class plan is in [`docs/curriculum.md`](docs/curriculum.md).
Session 13 uses an instructor-hosted Gecko MCP surface; its URL is handed out
in class.

## The Capstone

One project runs through everything: a **source-grounded developer research
assistant**. It answers questions about a small versioned corpus
(`data/corpus/`), cites the documents it used, and refuses to invent
unsupported facts. The final assistant must:

1. answer at least one supported technical question using the local corpus;
2. include source identifiers (doc ids) in its answer;
3. qualify or refuse an unsupported question;
4. use at least one bounded, read-only tool;
5. expose a reusable assistant skill or instruction file;
6. include a regression test and a small evaluation report; and
7. connect to external surfaces only in recorded/offline or an explicitly
   approved instructor-hosted mode.

During the course you rebuild the pieces of `src/bootcamp_agent/` in the
session notebooks, then compare against the shipped package.

## Final Assignment & Certificate

The course ends the Hugging Face way: [`final_assignment/`](final_assignment/)
is a template you make your own. As shipped, its agent honestly scores 30% on
the practice set; your job is to push it past the **70% pass bar**. Final
grading runs on a private question set at demo day, and a passing score plus a
completed demo earns an instructor-signed SVG certificate with an HMAC
verification code. The folder doubles as a Hugging Face Space, so you can
publish your agent as a public milestone. Details in
[`final_assignment/README.md`](final_assignment/README.md).

## Concept Threads

Three ideas recur across sessions, each with its own guide:

- **[Loop engineering](docs/guides/loop-engineering.md)** — budgets, stopping
  conditions, refusal as a first-class outcome (Sessions 5, 8)
- **[Graph engineering](docs/guides/graph-engineering.md)** — from retrieval
  metadata to explicit state graphs to API surface graphs (Sessions 6–8, 13)
- **[Harness engineering](docs/guides/harness-engineering.md)** — instructions,
  evals, traces, CI: everything around the model (Sessions 4, 9, 14)

## Gecko Cookbook

[`cookbook/`](cookbook/) holds 10 runnable notebooks on
[Gecko](https://github.com/GeckoVision/gecko-surf) — the API comprehension
layer for agents — from "comprehend an OpenAPI spec" to "full verified loop
against an instructor-hosted fork". Start at
[`cookbook/README.md`](cookbook/README.md).

## Repository Structure

```text
├── SETUP.md                 # pre-course environment checklist
├── src/bootcamp_agent/      # the capstone package (final shape)
├── tests/                   # deterministic tests — FakeLLM, no keys, no network
├── data/corpus/             # the six-document teaching corpus
├── data/evals/golden.jsonl  # the golden evaluation set
├── scripts/check_setup.py   # the setup doctor
├── scripts/check_notebooks.py  # notebook validity + execution checker (CI)
├── modules/module-{1,2,3}/  # chapters 01-15: guides, slides, notebooks, solutions
├── workspaces/              # open-ended project workspaces, one per week
├── integrations/            # SendAI devnet txs · Hermes Telegram · Gecko×Orquestra matrix
├── builder-kit/             # Claude Code plugin: skills + /bootcamp-doctor
├── final_assignment/        # graded final + certificate (HF-Space-compatible)
├── cookbook/                # runnable Gecko examples
└── docs/                    # curriculum, concept guides, instructor docs, specs
```

## Safe Assistant Workflow

Before asking a coding assistant to change code:

1. Ask it to inspect the relevant files and propose a plan.
2. Review the plan; restrict the allowed files and commands.
3. Ask for the smallest implementation.
4. Inspect the diff yourself.
5. Run the tests and inspect failures.
6. Ask for a concise explanation of the change and its remaining risks.

## Safety Boundary

Never place secrets in `CLAUDE.md`, `AGENTS.md`, Cursor rules, MCP JSON,
issues, prompts, or commits. All external-tool exercises use recorded/offline
mode or the instructor-hosted fork surface. **No wallets, no payment
credentials, no production API keys, no mainnet path — ever — in class
exercises.**

## License

MIT — see [LICENSE](LICENSE).
