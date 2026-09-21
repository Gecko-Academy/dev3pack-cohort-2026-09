<p align="center">
  <img src="docs/assets/github-cover.png"
       alt="Dev3Pack AI Engineering Bootcamp — from an LLM call to a verified agent. 14 September to 2 October 2026, demo day 2 October. MCP, loop engineering, graph engineering, RAG."
       width="100%" />
</p>

# Dev3Pack AI-Engineering Bootcamp

![Python](https://img.shields.io/badge/python-3.11+-blue)
![uv](https://img.shields.io/badge/uv-managed-6e56cf)
![License](https://img.shields.io/badge/license-MIT-blue)
![Claude Code](https://img.shields.io/badge/Claude_Code-ready-orange)

Three weeks. **15 sessions**. One source-grounded research assistant you can test, cite, and defend.

**14 September – 2 October 2026**, Monday to Friday, two hours a day. Optional showcase on Saturday 3 October.

## Contents

- [Start here](#start-here)
- [Find your way](#find-your-way)
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
git clone https://github.com/Gecko-Academy/dev3pack-cohort-2026-09.git
cd dev3pack-cohort-2026-09
uv run bootcamp start          # installs everything, then says whether it worked
```

`start` is safe to run as many times as you like, and it ends by telling you the
one command to type next. On macOS and Linux `make setup` is the same thing.

**Windows:** run these in **Git Bash** or WSL2, not PowerShell. The repository
is public — there is nothing to request and nothing to wait for.

If you have SSH keys set up, `git clone git@github.com:Gecko-Academy/dev3pack-cohort-2026-09.git`
works too. HTTPS is above because it needs nothing configured first.

Open **`00-START-HERE.ipynb`**. It lists every notebook in order and ticks what you have finished.

New to the repo? [`SETUP.md`](SETUP.md) is the half-hour path to a green doctor. No API key is required: every scored notebook runs offline against `FakeLLM`. This repository is read-only for you — hand in to [the submissions repository](https://github.com/Gecko-Academy/dev3pack-submissions) instead (see [Handing in](#handing-in)); week 0 is here now, later weeks land on 14 / 21 / 28 September — `git pull` at the start of each week.

## Find your way

**Looking for today's exercise?** It is the `notebook.ipynb` inside the session's
folder. Every link below opens the file itself, not a folder to search.

| I want to… | Go straight to |
|---|---|
| **do today's exercise** | the **Exercise** column in [the sessions table](#weeks-1-3) |
| **watch it work first** | the **Demo** column in the same table, or [`demos/`](demos/) |
| **build something real** | [`projects/`](projects/) — open data, a local model, ChromaDB |
| **see the ideas visually** | [Demos and explainers](https://gecko-academy.github.io/dev3pack-cohort-2026-09/tracks/demos/introduction) — interactive pages, mapped to sessions |
| **ask from your phone** | [**@gecko_coach_bot**](https://t.me/gecko_coach_bot) on Telegram — answers from the course pages, names the page, no install |
| **get unstuck** | `coach("your question")` in any notebook — answers from the course pages, offline, no key. [Demo 5](demos/05_the_coach_up_close.ipynb) shows how to use it |
| **contribute** | [gecko-ai-coach](https://github.com/Gecko-Academy/gecko-ai-coach/blob/main/CONTRIBUTING.md) — add a question the coach gets wrong: ten minutes, no code |
| **put an agent in a chat** | [`demos/07_the_coach_in_a_chat.ipynb`](demos/07_the_coach_in_a_chat.ipynb), then [the Telegram guide](https://gecko-academy.github.io/dev3pack-cohort-2026-09/unit1/session-05-deterministic-mini-agent/telegram-guide) |
| **run RAG on your laptop** | [`demos/09_rag_on_your_laptop.ipynb`](demos/09_rag_on_your_laptop.ipynb) — today's retriever plus a local model, no key; a recorded run if you have no model |
| **learn Jupyter from zero** | [`demos/06_jupyter_for_beginners.ipynb`](demos/06_jupyter_for_beginners.ipynb) — cells, run order, errors, in fifteen minutes |
| **use a coding assistant well** | [Your coding assistant, step by step](https://gecko-academy.github.io/dev3pack-cohort-2026-09/tracks/coding-assistant/introduction) — Claude Code 101, five prompts, and where the line is |
| **learn git, and contribute anywhere** | [Git, and your first contribution](https://gecko-academy.github.io/dev3pack-cohort-2026-09/tracks/first-contribution/introduction) — the nine commands, the errors, and where to find a first issue |
| **hand in** | `uv run bootcamp submit chNN --github <you> --push` — see [Handing in](#handing-in) |
| **see the leaderboard** | [`TRACK.md` in the submissions repository](https://github.com/Gecko-Academy/dev3pack-submissions/blob/main/TRACK.md) |
| **run a model on a small laptop** | [`demos/04_ollama_on_colab.ipynb`](demos/04_ollama_on_colab.ipynb) |
| **read the course as a website** | [gecko-academy.github.io/dev3pack-cohort-2026-09/](https://gecko-academy.github.io/dev3pack-cohort-2026-09/) |

Inside a notebook, **everything that runs as shipped is already done for you**.
Each session has exactly one cell that does not — its heading says
**"Challenge"**, and it tells you what it is worth, what done looks like, and gives
you a tip.

### Handing in

```bash
git pull                                              # always first: fixes reach you this way
uv run bootcamp check ch04                            # the scorecard, before you submit
uv run bootcamp submit ch04 --github <you> --push     # opens the pull request for you
```

Submissions go to **[Gecko-Academy/dev3pack-submissions](https://github.com/Gecko-Academy/dev3pack-submissions)**, never to this
repository. In the pull request's *Files changed* tab, every file should start
with `submissions/<you>/`. It merges on its own once its check is green.

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
| **Sessions** (`session-01`–`15`) | same tree | Live, weekday, two hours. Introduction, concepts, quiz, exercise notebook, and a demo. Solutions for sessions 1–3 only. Session 15 has no notebook. |
| **Capstone** | [units/en/unit2/capstone/](units/en/unit2/capstone/) | Built between sessions from week 2. `src/bootcamp_agent/` is the finished shape. |
| **Bonus / depth / cookbook / workspaces** | linked below | Optional. Never counted. |

Two sessions are assistant-driven (1 and 10) and show as `in Jupyter` in `bootcamp progress`.

## Repository map

Where everything lives, and what a student receives.

<!-- repo-map:start -->

| Path | What lives there | Students get it |
|---|---|---|
| `00-START-HERE.ipynb` | The map a learner opens first. Lists every notebook in order and ticks what is finished. | day one |
| `Makefile` | Short names for the commands you run most: `make setup`, `make lab`, `make check`. Every target is a one-line wrapper around a `uv run` command, so it is a convenience and never a requirement — Windows has no `make` by default. | day one |
| `units/` | The course. `en/` holds week-0 units, the fifteen sessions, the capstone, and the bonus track, each a directory of pages plus a notebook. | weekly |
| `src/bootcamp_agent/` | The finished shape of the capstone package, and the check registry every exercise is graded by. | day one |
| `tests/` | Behaviour contracts for the package — and the solved value of every exercise, which is why students never receive it. | **never** |
| `data/` | The versioned corpus the retrieval sessions and the capstone answer from. | day one |
| `scripts/` | The course's own tooling: the site generator, the publisher, the submission collector. | day one |
| `docs/` | Curriculum, guides, the generated index, and the instructor material. | in part |
| `depth/` | Six optional software-engineering modules, about 45 minutes each. Never counted. | day one |
| `cookbook/` | Ten Gecko notebooks, from comprehending an OpenAPI spec to a verified loop on a fork. Optional. | day one |
| `workspaces/` | Four open projects to build in. Optional, unmarked, no checks. | day one |
| `projects/` | Real-world projects: a brief, open data, a local model and ChromaDB. Optional, never counted; needs `uv sync --extra projects`. | day one |
| `demos/` | Short notebooks to run in class and again afterwards. Never graded, never submitted; they make one idea concrete in a few minutes. | day one |
| `ship-it/` | The optional launch track: turn the capstone into an MCP server somebody else can call, and a storefront an agent can buy from. Offline and never counted. | day one |
| `integrations/` | Worked integrations the sessions link into rather than re-explain. | day one |
| `builder-kit/` | Templates a learner copies from when starting their own surface. | day one |
| `final_assignment/` | The final's harness and the offline practice grader. The private question set is not here and never will be. | day one |
| `modules/` | A pointer only. The tree lived here until 9 Sep 2026; the file says where it went. | in part |
| `AGENTS.md` | The policy a coding assistant reads before it edits. `CLAUDE.md` and the Cursor rules point at it rather than forking it. | day one |
| `README.md` | This file. | day one |
| `SETUP.md` | The half-hour path from a clone to a green doctor. | day one |
| `llms.txt` | What an agent helping you needs — and what it must not do. Generated. | day one |
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

7 paths are withheld by name, whatever the week: `.github`, `docs/instructor`, `docs/plans`, `docs/specs`, `evals`, `scripts/instructor_pack.py`, `tests`. Each is on that list for a stated reason — `tests/` alone holds the solved value of every exercise. The publisher audits the tree it built rather than trusting the copy, and refuses if one of them appears.

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
| Week 0 | now | Everything above except the sessions: the twelve week-0 units, the welcome pages, the bonus track and the whole toolchain (50 paths). |
| Week 1 | Mon 14 Sep | unit1 |
| Week 2 | Mon 21 Sep | unit2 |
| Week 3 | Mon 28 Sep | unit3 |

**Nothing is hidden behind a permission.** A week that has not opened is not in the repository yet, so `git pull` on the Monday is the whole ritual. Your table of contents lists what you actually have, and names what is still to come in a comment at the end — this table is the schedule, and you have it from day one.

A correction is withdrawn as well as added: the publisher removes a file the current week no longer contains, so a fix actually reaches somebody who already pulled.

<!-- release-plan:end -->
Solutions: week 0 and sessions 1–3 carry a `solutions/` notebook. From session 4
on, they do not. Each session ships with everything running except one cell, and
that cell is yours to solve — a solution would only be that cell, answered. When
you are stuck, `hint(reveal=True)` is the worked answer (it costs marks), and
`coach(...)` answers from the course pages for free.

## Week 0

Self-paced. Handed in as a record, never marked. Short on time? Do the four 45-minute units. Courses A–C stay here for the whole course and nothing in the fifteen sessions waits for them.

### Fast lane

| # | Unit | You leave able to | Exercise |
|---|---|---|---|
| 1 | [The environment](units/en/unit0/w01-environment/) | Prove which Python and repo environment will run the course | [notebook](units/en/unit0/w01-environment/notebook.ipynb) |
| 2 | [Packages and documentation](units/en/unit0/w02-packages-and-docs/) | Read an installed package instead of guessing its API | [notebook](units/en/unit0/w02-packages-and-docs/notebook.ipynb) |
| 3 | [Classes and contracts](units/en/unit0/w03-classes-and-contracts/) | Turn a prose requirement into a typed boundary | [notebook](units/en/unit0/w03-classes-and-contracts/notebook.ipynb) |
| 4 | [Calling a real API](units/en/unit0/w04-real-apis/) | Make one bounded HTTP call through an adapter you own | [notebook](units/en/unit0/w04-real-apis/notebook.ipynb) |

### Course A — Software engineering foundations

| # | Unit | Exercise |
|---|---|---|
| 5 | [Packages, PyPI and PEP 8](units/en/unit0/w05-packages-and-pep8/) | [notebook](units/en/unit0/w05-packages-and-pep8/notebook.ipynb) |
| 6 | [A portable package](units/en/unit0/w06-portable-packages/) | [notebook](units/en/unit0/w06-portable-packages/notebook.ipynb) |
| 7 | [Classes in a package](units/en/unit0/w07-classes-in-packages/) | [notebook](units/en/unit0/w07-classes-in-packages/notebook.ipynb) |
| 8 | [Documentation, tests and readability](units/en/unit0/w08-docs-tests-readability/) | [notebook](units/en/unit0/w08-docs-tests-readability/notebook.ipynb) |

### Course B — MCP

| # | Unit | Exercise |
|---|---|---|
| 9 | [Your first MCP server](units/en/unit0/w09-mcp-first-server/) | [notebook](units/en/unit0/w09-mcp-first-server/notebook.ipynb) |
| 10 | [Resources, prompts, and the LLM](units/en/unit0/w10-mcp-resources-prompts-llms/) | [notebook](units/en/unit0/w10-mcp-resources-prompts-llms/notebook.ipynb) |
| 11 | [Databases, APIs, and third-party servers](units/en/unit0/w11-mcp-data-apis-third-party/) | [notebook](units/en/unit0/w11-mcp-data-apis-third-party/notebook.ipynb) |

### Course C — Data structures for agents

| # | Unit | Exercise |
|---|---|---|
| 12 | [Data structures for agents](units/en/unit0/w12-dsa-for-agents/) | [notebook](units/en/unit0/w12-dsa-for-agents/notebook.ipynb) |

## Weeks 1-3

Each live session is one directory under `units/en/unit1/`, `unit2/` or `unit3/`. **Exercise** opens the notebook you work in; **Demo** is the one run in class. A session that has not happened yet may not be in your copy — `git pull`.

| # | Day | Session | You leave with | Exercise | Demo |
|---|---|---|---|---|---|
| 1 | Mon 14 Sep | [Configure the assistant](units/en/unit1/session-01-assistant-configuration/) | Repo instructions the assistant must read before it edits | [notebook](units/en/unit1/session-01-assistant-configuration/notebook.ipynb) | — |
| 2 | Tue 15 Sep | [Call a model through the adapter](units/en/unit1/session-02-model-adapter/) | One adapter, two lanes, failures that refuse instead of traceback | [notebook](units/en/unit1/session-02-model-adapter/notebook.ipynb) | [demo](units/en/unit1/session-02-model-adapter/demo.ipynb) |
| 3 | Wed 16 Sep | [Structured outputs](units/en/unit1/session-03-structured-outputs/) | A typed answer; retry once, then refuse | [notebook](units/en/unit1/session-03-structured-outputs/notebook.ipynb) | [demo](units/en/unit1/session-03-structured-outputs/demo.ipynb) |
| 4 | Thu 17 Sep | [Bounded tools](units/en/unit1/session-04-bounded-tools/) | Read-only tools whose boundaries you can prove | [notebook](units/en/unit1/session-04-bounded-tools/notebook.ipynb) | [demo](units/en/unit1/session-04-bounded-tools/demo.ipynb) |
| 5 | Fri 18 Sep | [A deterministic mini-agent](units/en/unit1/session-05-deterministic-mini-agent/) | A loop that stops, notices repeats, and exits safely | [notebook](units/en/unit1/session-05-deterministic-mini-agent/notebook.ipynb) | — |
| 6 | Mon 21 Sep | [A retrieval baseline](units/en/unit2/session-06-retrieval-baseline/) | A corpus loader and lexical retrieval — plus the ways it fails | [notebook](units/en/unit2/session-06-retrieval-baseline/notebook.ipynb) | [RAG on your laptop](demos/09_rag_on_your_laptop.ipynb) |
| 7 | Tue 22 Sep | [Retrieval and grounding metrics](units/en/unit2/session-07-grounding-metrics/) | Hit rate, grounding rate, and the cost of one fix | [notebook](units/en/unit2/session-07-grounding-metrics/notebook.ipynb) | — |
| 8 | Wed 23 Sep | [Loops and graphs](units/en/unit2/session-08-loops-and-graphs/) | Chain vs loop vs graph; illegal edges do not move | [notebook](units/en/unit2/session-08-loops-and-graphs/notebook.ipynb) | — |
| 9 | Thu 24 Sep | [Trace and evaluate](units/en/unit2/session-09-trace-and-evaluate/) | A redacted event log and named error buckets | [notebook](units/en/unit2/session-09-trace-and-evaluate/notebook.ipynb) | — |
| 10 | Fri 25 Sep | [Skills and an ADR](units/en/unit2/session-10-skills-and-adr/) | A `SKILL.md` and a decision that names its reversal | [notebook](units/en/unit2/session-10-skills-and-adr/notebook.ipynb) | — |
| 11 | Mon 28 Sep | State and memory — not yet | Session state, a retention policy, cross-user isolation | notebook — not yet | — |
| 12 | Tue 29 Sep | MCP architecture — not yet | Host / client / server; a surface read as claims | notebook — not yet | — |
| 13 | Wed 30 Sep | Build and secure an MCP server — not yet | A fetch guard that refuses *before* it fetches | notebook — not yet | — |
| 14 | Thu 1 Oct | Deploy and operate — not yet | A smoke test and the rollback sentence | notebook — not yet | — |
| 15 | Fri 2 Oct | Defend the capstone — opens Fri 02 Oct | A demo, then a failure diagnosed from your own traces | — | — |

Session 13 uses an instructor-hosted Gecko MCP surface; the URL is handed out in class.

## Capstone and certificate

A **source-grounded developer research assistant**: it answers from `data/corpus/`, cites document ids, and refuses when nothing supports the claim. You rebuild `src/bootcamp_agent/` in the session notebooks, then compare against the shipped package. Brief: [units/en/unit2/capstone/](units/en/unit2/capstone/).

[`final_assignment/`](final_assignment/) is a template that scores 30% as shipped — it refuses correctly and answers nothing. Pass both gates (aggregate bar and every **critical** question) and the course issues an Ed25519-signed certificate anyone can verify. Details: [`final_assignment/README.md`](final_assignment/README.md).

## Bonus and extras

Optional. Never counted. Never required for the certificate.

| # | Bonus |
|---|---|
| 1 | [Graph RAG and hybrid search](units/en/bonus/b01-graph-rag/) |
| 2 | [Multimodal ingestion as untrusted data](units/en/bonus/b02-multimodal-ingestion/) |
| 3 | [Multi-agent orchestration with ADK](units/en/bonus/b03-multi-agent-orchestration/) |
| 4 | [Long-term memory, consent, and deletion](units/en/bonus/b04-memory-consent-deletion/) |
| 5 | [Deploy, evaluate, and tear down](units/en/bonus/b05-deploy-evaluate-teardown/) |

- **[demos/](demos/)** — notebooks run in class, to run again afterwards: [an API request up close](demos/01_api_request_up_close.ipynb) (real calls to a public pet API), [one question three ways](demos/02_one_question_three_ways.ipynb) (prompt vs API vs MCP), [regex, parsing and retrieval](demos/03_regex_parsing_retrieval.ipynb), [Ollama on Colab](demos/04_ollama_on_colab.ipynb) for small laptops, [the coach up close](demos/05_the_coach_up_close.ipynb), [Jupyter for beginners](demos/06_jupyter_for_beginners.ipynb) [the coach in a chat](demos/07_the_coach_in_a_chat.ipynb), [the weekly challenge](demos/08_the_weekly_challenge.ipynb) and [RAG on your laptop](demos/09_rag_on_your_laptop.ipynb).
- **[projects/](projects/)** — real-world projects on open data with a local model and ChromaDB. [Project 01: what are customers really saying?](projects/01-clothing-reviews/notebook.ipynb) Needs `uv sync --extra projects`.
- **[ship-it/](ship-it/)** — turn the capstone into a surface somebody else can call, and a storefront an agent can buy from.
- **[Demos and explainers](https://gecko-academy.github.io/dev3pack-cohort-2026-09/tracks/demos/introduction)** — Transformer Explainer, LLM Visualization, Tiktokenizer, Regexper, the Embedding Projector and more, each mapped to the session it helps.
- **Two helpers inside every notebook:** `coach("…")` answers from the course pages, and `bootcamp_agent.patterns` builds a regular expression from plain words — `phrase("you must now")`, `near(one_of("send"), one_of("api key"))` — so nobody has to write regex by hand.
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
