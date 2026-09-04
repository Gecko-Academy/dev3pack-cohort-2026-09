# Gecko Cookbook

Runnable notebooks on using [Gecko](https://github.com/GeckoVision/gecko-surf) —
the API comprehension layer for agents — from "comprehend an OpenAPI spec" to
"full verified loop against a hosted fork". Each notebook states its goal, its
prerequisites, and what you should see.

## The rules (every notebook obeys them)

1. **Offline by default.** Every notebook runs without secrets. Cells that need
   the real gecko CLI opt in via `GECKO_COOKBOOK_LIVE=1` (plus `npx`); cells
   that need the instructor-hosted surface are marked `manual-run` and act as
   lab guides.
2. **Nothing here can spend.** No notebook ever asks for a key that can move
   funds. The only signing anywhere (notebook 10) is a throwaway key on a fork,
   held by the hosted surface — never by you.
3. **Honesty.** Notebooks describe what Gecko does today; miniatures are
   labeled as miniatures.

```bash
uv sync --group dev
uv run python scripts/check_notebooks.py cookbook   # they all pass or skip cleanly
```

## Introduction

| # | Notebook | What it teaches | Runs |
|---|---|---|---|
| 01 | [Welcome to Gecko](introduction/01_welcome_to_gecko.ipynb) | What comprehension/provenance/recorded mode are; the doctor | offline (+opt-in live) |
| 02 | [Comprehend an OpenAPI](introduction/02_comprehend_an_openapi.ipynb) | Spec in → question-shaped tools out; auth surfaced, never valued | offline (+opt-in live) |
| 03 | [Recorded-mode calls](introduction/03_recorded_mode_calls.ipynb) | One code path, two modes; deterministic examples from schemas | offline |
| 04 | [Connect an MCP client](introduction/04_connect_mcp_client.ipynb) | `gecko serve` → Claude Code / Cursor config; sanity checks | manual (edits config) |
| 05 | [Read the report](introduction/05_read_the_report.ipynb) | Provenance tiers; why unknowns are a feature | offline |

## Integrations

| # | Notebook | What it teaches | Runs |
|---|---|---|---|
| 06 | [The capstone meets Gecko](integrations/06_capstone_meets_gecko.ipynb) | A comprehended surface as one more bounded tool in the bootcamp agent | offline |
| 07 | [Two APIs, one assistant](integrations/07_two_apis_one_assistant.ipynb) | Surface-then-operation routing; the routing floor as a safety control | offline |
| 11 | [The Autonomous Petshop](integrations/11_autonomous_petshop.py) | LangGraph pipeline: comprehend a multi-API system → correlate by value domain → emit an **Arazzo** workflow → simulate it → assemble a consumable agent graph with provenance. `uv run` resolves its own deps; `PETSTORE_LIVE=1` executes the GET steps against the real Swagger Petstore | offline (+opt-in live GETs) |

## Advanced

| # | Notebook | What it teaches | Runs |
|---|---|---|---|
| 08 | [Anti-poisoning](advanced/08_anti_poisoning.ipynb) | A poisoned spec fixture, a miniature detector, the fail-closed layers | offline |
| 09 | [Program graph & find_start](advanced/09_program_graph_find_start.ipynb) | Instruction↔account graph, derivation order, intent → starting instruction | offline |
| 10 | [Full loop on the hosted fork](advanced/10_full_loop_hosted_fork.ipynb) | browse → comprehend → prepare → try → **receipt of what moved** | manual (hosted MCP) |

## Fixtures

`fixtures/` contains: `petstore-mini.yaml` and `weather-mini.yaml` (small clean
OpenAPI surfaces), `poisoned-spec.yaml` (a **defensive teaching fixture** — a
spec that attacks its reader; never load anything like it into a credentialed
integration), and `program-graph-example.json` (a comprehension graph in the
shape Gecko produces for a Solana storefront program).

## Different applicabilities, one pattern

The notebooks are ordered so the same pattern repeats at increasing stakes:
comprehend the surface → inspect the evidence (report/graph/provenance) →
exercise it where mistakes are free (recorded/fork) → only then let it count.
That pattern is the bootcamp's thesis; the cookbook is where you practice it on
surfaces beyond the course corpus.
