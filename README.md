<p align="center">
  <img src=".github/assets/github-cover.png"
       alt="Dev3Pack AI Engineering Bootcamp — from an LLM call to a verified agent. 14 September to 2 October 2026, demo day 2 October. MCP, loop engineering, graph engineering, RAG."
       width="100%" />
</p>

# Dev3Pack AI-Engineering Bootcamp

[![CI](https://github.com/ernanibmurtinho/Dev3Pack-bootcamp-AI-Engineering/actions/workflows/test.yml/badge.svg)](https://github.com/ernanibmurtinho/Dev3Pack-bootcamp-AI-Engineering/actions/workflows/test.yml)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![uv](https://img.shields.io/badge/uv-managed-6e56cf)
![License](https://img.shields.io/badge/license-MIT-blue)
![Claude Code](https://img.shields.io/badge/Claude_Code-ready-orange)

Three weeks. **15 sessions**. One source-grounded research assistant you can test, cite, and defend.

**14 September – 2 October 2026**, Monday to Friday, two hours a day. Optional showcase on Saturday 3 October.

## Contents

- [Start here](#start-here)
- [For coding assistants](#for-coding-assistants)
- [What you will learn](#what-you-will-learn)
- [Units, sessions, extras](#units-sessions-extras)
- [Repository map](#repository-map)
- [Course map](#course-map)
- [What arrives, and when](#what-arrives-and-when)
- [Week 0](#week-0)
- [Weeks 1-3](#weeks-1-3)
- [Capstone and certificate](#capstone-and-certificate)
- [Bonus and extras](#bonus-and-extras)
- [Commands](#commands)
- [Safety](#safety)

## Start here

```bash
git clone git@github.com:Gecko-Academy/dev3pack-cohort-2026-09.git
cd dev3pack-cohort-2026-09
uv sync --group dev
uv run jupyter lab
```

Open **`00-START-HERE.ipynb`**. It lists every notebook in order and ticks what you have finished.

New to the repo? [`SETUP.md`](SETUP.md) is the half-hour path to a green doctor. No API key is required: every scored notebook runs offline against `FakeLLM`. The repository is private and read-only; week 0 is here now, later weeks land on 14 / 21 / 28 September — `git pull` at the start of each week.

## For coding assistants

Read [`AGENTS.md`](AGENTS.md) first. `CLAUDE.md` and `.cursor/rules/bootcamp.mdc` point at it — do not fork the policy.

Then read in this order:

| File | Why |
|---|---|
| [README.md](README.md) | Course map: units, sessions, bonus |
| `00-START-HERE.ipynb` | Progress ticker and notebook links |
| [units/en/_toctree.yml](units/en/_toctree.yml) | Page order a learner opens |
| [src/bootcamp_agent/](src/bootcamp_agent/) | Capstone package (finished shape) |
| tests/ — not in your copy | Behaviour contracts |

Inspect → plan → implement → test → review. No new dependency unless a lesson asks for it.

Optional, local only — never required, never committed:

```bash
uv tool install graphifyy
graphify install
```

Then `/graphify .` in your assistant. Leave `graphify-out/` untracked.

## What you will learn

- **Harness** — assistant instructions, traces, evals, and CI around the model
- **Contracts** — one adapter, typed outputs, bounded read-only tools
- **Loops** — budgets, stopping conditions, refusal as a first-class exit
- **Grounding** — retrieve from a versioned corpus, cite sources, refuse the unsupported
- **Surfaces** — MCP, deployment, and defending a failure from your own traces

Three threads recur: [loop](docs/guides/loop-engineering.md), [graph](docs/guides/graph-engineering.md), and [harness](docs/guides/harness-engineering.md) engineering. The full day-by-day plan is in [`docs/curriculum.md`](docs/curriculum.md).

## Units, sessions, extras

| Kind | Where | Role |
|---|---|---|
| **Week 0 units** (`w01`–`w12`) | [units/en/](units/en/) | Self-paced, ungraded, available now. The fast lane is the floor Session 1 assumes. |
| **Sessions** (`session-01`–`15`) | same tree | Live, weekday, two hours. Introduction, concepts, quiz, exercise notebook, solutions. Session 15 has no notebook. |
| **Capstone** | units/en/capstone/ — opens with week 2 | Built between sessions from week 2. `src/bootcamp_agent/` is the finished shape. |
| **Bonus / depth / cookbook / workspaces** | linked below | Optional. Never counted. |

Two sessions are assistant-driven (1 and 10) and show as `in Jupyter` in `bootcamp progress`.

## Repository map

Where everything lives, and what a student receives.

<!-- repo-map:start -->

| Path | What lives there | Students get it |
|---|---|---|
| `00-START-HERE.ipynb` | The map a learner opens first. Lists every notebook in order and ticks what is finished. | day one |
| `units/` | The course. `en/` holds week-0 units, the fifteen sessions, the capstone, and the bonus track, each a directory of pages plus a notebook. | weekly |
| `src/bootcamp_agent/` | The finished shape of the capstone package, and the check registry every exercise is graded by. | day one |
| `tests/` | Behaviour contracts for the package — and the solved value of every exercise, which is why students never receive it. | **never** |
| `data/` | The versioned corpus the retrieval sessions and the capstone answer from. | day one |
| `scripts/` | The course's own tooling: the site generator, the publisher, the submission collector. | day one |
| `docs/` | Curriculum, guides, the generated index, and the instructor material. | in part |
| `depth/` | Six optional software-engineering modules, about 45 minutes each. Never counted. | day one |
| `cookbook/` | Ten Gecko notebooks, from comprehending an OpenAPI spec to a verified loop on a fork. Optional. | day one |
| `workspaces/` | Four open projects to build in. Optional, unmarked, no checks. | day one |
| `integrations/` | Worked integrations the sessions link into rather than re-explain. | day one |
| `builder-kit/` | Templates a learner copies from when starting their own surface. | day one |
| `final_assignment/` | The final's harness and the offline practice grader. The private question set is not here and never will be. | day one |
| `modules/` | A pointer only. The tree lived here until 9 Sep 2026; the file says where it went. | in part |
| `AGENTS.md` | The policy a coding assistant reads before it edits. `CLAUDE.md` and the Cursor rules point at it rather than forking it. | day one |
| `README.md` | This file. | day one |
| `SETUP.md` | The half-hour path from a clone to a green doctor. | day one |
| `CLAUDE.md` | Points Claude Code at `AGENTS.md`. | day one |
| `LICENSE` | MIT. | day one |
| `pyproject.toml` | The package, its dependency groups, and the tool configuration. | day one |
| `uv.lock` | The resolved dependency set. CI installs from it frozen. | day one |
| `.github/` | CI. It runs every notebook, the full test suite, and the generator's `--check`. | **never** |
| `.claude-plugin/` | The plugin manifest that ships the course's own slash commands. | day one |
| `.cursor/` | Cursor rules, pointing at `AGENTS.md`. | day one |
| `.env.example` | Every variable the course reads, with empty values. | day one |
| `.gitignore` | What never enters git, including keys and a learner's own submissions. | day one |
| `.python-version` | The interpreter `uv` picks. | day one |

6 paths are withheld by name, whatever the week: `.github`, `docs/instructor`, `docs/plans`, `docs/specs`, `evals`, `tests`. Each is on that list for a stated reason — `tests/` alone holds the solved value of every exercise. The publisher audits the tree it built rather than trusting the copy, and refuses if one of them appears.

Sent in part: `docs/`, `modules/`. Guides, the curriculum and the generated index ship; the instructor material, the specs and the plans do not.

<!-- repo-map:end -->
## Course map

| Track | When | What |
|---|---|---|
| [Week 0 — Fast lane](#week-0) | now, ~3h | Environment, packages, contracts, one API call |
| [Week 0 — Courses A–C](#week-0) | now, optional | Packaging, MCP, data structures |
| [Week 1 — Sessions 1–5](#weeks-1-3) | Sep 14–18 | Assistants, adapters, structured outputs, tools, first loop |
| [Week 2 — Sessions 6–10](#weeks-1-3) | Sep 21–25 | Retrieval, grounding, graphs, evals, skills |
| [Week 3 — Sessions 11–15](#weeks-1-3) | Sep 28–Oct 2 | State, MCP, deploy, defend |
| [Capstone + certificate](#capstone-and-certificate) | weeks 2–3 | Source-grounded research assistant |
| [Bonus 1–5](#bonus-and-extras) | optional | Graph RAG, multimodal, multi-agent, memory, teardown |
| [Depth / cookbook / workspaces](#bonus-and-extras) | optional | SE fundamentals, Gecko labs, **4 project workspaces** |

## What arrives, and when

This repository grows during the course. Week 0 is here now; each Monday one
more week lands and you `git pull`.

<!-- release-plan:start -->

| Arrives | Date | What is added |
|---|---|---|
| Week 0 | now | Everything above except the sessions: the twelve week-0 units, the welcome pages, the bonus track and the whole toolchain (45 paths). |
| Week 1 | Mon 14 Sep | Session 1, Configure the assistant and the repository instructions; Session 2, Call a model through the adapter; Session 3, Structured outputs; Session 4, Bounded tools; Session 5, A deterministic mini-agent |
| Week 2 | Mon 21 Sep | Capstone: the source-grounded research assistant; Session 6, A retrieval baseline; Session 7, Retrieval and grounding metrics; Session 8, Loops and graphs; Session 9, Trace and evaluate an agent; Session 10, Skills and an architecture decision record |
| Week 3 | Mon 28 Sep | Session 11, State and memory; Session 12, MCP architecture and primitives; Session 13, Build and secure an MCP server; Session 14, Deploy and operate the capstone; Session 15, Defend the capstone |

**Nothing is hidden behind a permission.** A week that has not opened is not in the repository yet, so `git pull` on the Monday is the whole ritual. Your table of contents lists what you actually have, and names what is still to come in a comment at the end — this table is the schedule, and you have it from day one.

A correction is withdrawn as well as added: the publisher removes a file the current week no longer contains, so a fix actually reaches somebody who already pulled.

<!-- release-plan:end -->
Solutions are separate again: a session's `solutions/` notebook is released
after that session, so you meet an exercise before its answer is one folder
away. Until then, `hint(reveal=True)` is the worked answer, and it costs marks.

## Week 0

Self-paced. Handed in as a record, never marked. Short on time? Do the four 45-minute units. Courses A–C stay here for the whole course and nothing in the fifteen sessions waits for them.

### Fast lane

| # | Unit | You leave able to |
|---|---|---|
| 1 | [The environment](units/en/w01-environment/) | Prove which Python and repo environment will run the course |
| 2 | [Packages and documentation](units/en/w02-packages-and-docs/) | Read an installed package instead of guessing its API |
| 3 | [Classes and contracts](units/en/w03-classes-and-contracts/) | Turn a prose requirement into a typed boundary |
| 4 | [Calling a real API](units/en/w04-real-apis/) | Make one bounded HTTP call through an adapter you own |

### Course A — Software engineering foundations

| # | Unit |
|---|---|
| 5 | [Packages, PyPI and PEP 8](units/en/w05-packages-and-pep8/) |
| 6 | [A portable package](units/en/w06-portable-packages/) |
| 7 | [Classes in a package](units/en/w07-classes-in-packages/) |
| 8 | [Documentation, tests and readability](units/en/w08-docs-tests-readability/) |

### Course B — MCP

| # | Unit |
|---|---|
| 9 | [Your first MCP server](units/en/w09-mcp-first-server/) |
| 10 | [Resources, prompts, and the LLM](units/en/w10-mcp-resources-prompts-llms/) |
| 11 | [Databases, APIs, and third-party servers](units/en/w11-mcp-data-apis-third-party/) |

### Course C — Data structures for agents

| # | Unit |
|---|---|
| 12 | [Data structures for agents](units/en/w12-dsa-for-agents/) |

## Weeks 1-3

Each live session is one directory under `units/en/session-NN-*/`.

| # | Day | Session | You leave with |
|---|---|---|---|
| 1 | Mon 14 Sep | Configure the assistant — not yet | Repo instructions the assistant must read before it edits |
| 2 | Tue 15 Sep | Call a model through the adapter — not yet | One adapter, two lanes, failures that refuse instead of traceback |
| 3 | Wed 16 Sep | Structured outputs — not yet | A typed answer; retry once, then refuse |
| 4 | Thu 17 Sep | Bounded tools — not yet | Read-only tools whose boundaries you can prove |
| 5 | Fri 18 Sep | A deterministic mini-agent — not yet | A loop that stops, notices repeats, and exits safely |
| 6 | Mon 21 Sep | A retrieval baseline — not yet | A corpus loader and lexical retrieval — plus the ways it fails |
| 7 | Tue 22 Sep | Retrieval and grounding metrics — not yet | Hit rate, grounding rate, and the cost of one fix |
| 8 | Wed 23 Sep | Loops and graphs — not yet | Chain vs loop vs graph; illegal edges do not move |
| 9 | Thu 24 Sep | Trace and evaluate — not yet | A redacted event log and named error buckets |
| 10 | Fri 25 Sep | Skills and an ADR — not yet | A `SKILL.md` and a decision that names its reversal |
| 11 | Mon 28 Sep | State and memory — not yet | Session state, a retention policy, cross-user isolation |
| 12 | Tue 29 Sep | MCP architecture — not yet | Host / client / server; a surface read as claims |
| 13 | Wed 30 Sep | Build and secure an MCP server — not yet | A fetch guard that refuses *before* it fetches |
| 14 | Thu 1 Oct | Deploy and operate — opens Thu 01 Oct | A smoke test and the rollback sentence |
| 15 | Fri 2 Oct | Defend the capstone — opens Fri 02 Oct | A demo, then a failure diagnosed from your own traces |

Session 13 uses an instructor-hosted Gecko MCP surface; the URL is handed out in class.

## Capstone and certificate

A **source-grounded developer research assistant**: it answers from `data/corpus/`, cites document ids, and refuses when nothing supports the claim. You rebuild `src/bootcamp_agent/` in the session notebooks, then compare against the shipped package. Brief: units/en/capstone/ — opens with week 2.

[`final_assignment/`](final_assignment/) is a template that scores 30% as shipped — it refuses correctly and answers nothing. Pass both gates (aggregate bar and every **critical** question) and the course issues an Ed25519-signed certificate anyone can verify. Details: [`final_assignment/README.md`](final_assignment/README.md).

## Bonus and extras

Optional. Never counted. Never required for the certificate.

| # | Bonus |
|---|---|
| 1 | [Graph RAG and hybrid search](units/en/bonus-b01-graph-rag/) |
| 2 | [Multimodal ingestion as untrusted data](units/en/bonus-b02-multimodal-ingestion/) |
| 3 | [Multi-agent orchestration with ADK](units/en/bonus-b03-multi-agent-orchestration/) |
| 4 | [Long-term memory, consent, and deletion](units/en/bonus-b04-memory-consent-deletion/) |
| 5 | [Deploy, evaluate, and tear down](units/en/bonus-b05-deploy-evaluate-teardown/) |

- **[depth/](depth/)** — six software-engineering modules (~45 minutes each): boundaries, data, architecture, reliability, production, graph RAG.
- **[cookbook/](cookbook/)** — ten Gecko notebooks, from comprehending an OpenAPI spec to a verified loop on an instructor-hosted fork.
- **[workspaces/](workspaces/)** — four open projects (corpus Q&A, retrieval lab, Autonomous Store, news-to-Telegram).

## Commands

```bash
uv run bootcamp doctor                       # this machine
uv run bootcamp check ch03                   # one session scorecard
uv run bootcamp progress                     # every session, one tally
uv run bootcamp submit ch03 --github <you>   # write submissions/<you>/ch03/
```

Checks judge behaviour, not wording. How to hand work in: [units/en/unit0/how-to-submit.mdx](units/en/unit0/how-to-submit.mdx). The generated index: [`docs/course-index.md`](docs/course-index.md).

## Safety

Never place secrets in `CLAUDE.md`, `AGENTS.md`, Cursor rules, MCP JSON, issues, prompts, or commits. External-tool exercises use recorded/offline mode or the instructor-hosted fork. **No wallets, no payment credentials, no production API keys, no mainnet path — ever — in class exercises.**

Ask a coding assistant to inspect, propose a plan, and make the smallest change. Review the diff yourself. The loop lives in [`AGENTS.md`](AGENTS.md).

## License

MIT — see [LICENSE](LICENSE).
