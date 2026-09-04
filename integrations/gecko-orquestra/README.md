# Gecko × Orquestra — the cross-runtime test matrix

**The idea:** the instructor makes Orquestra's catalogue agent-ready through
Gecko (comprehended programs served over MCP, backed by a surfpool fork), and
we test that surface with **different agent runtimes as the clients** —
Claude Code / Cursor (Session 13), **Hermes**, and a **SendAI**-powered agent.
Same surface, same questions, different brains: what stays constant is the
graph and the receipts; what varies is how each runtime uses them.

**Status:** the harness below is ready; it runs the moment the hosted surface
(`<HOSTED_GECKO_MCP_URL>`) is up. Making Orquestra agent-ready is the
instructor's side of the work.

## The matrix

| Client runtime | Connects via | What we grade |
|---|---|---|
| Claude Code / Cursor | `claude mcp add gecko-class --transport http <URL>` | The Session-13 lab (baseline) |
| Hermes | its MCP/tool integration, pointed at the same URL | Does a self-improving generalist follow `find_start` routing, or improvise? |
| SendAI agent (LangChain/Vercel tools) | a custom tool that calls the surface's HTTP endpoints | Does a pre-built-actions agent defer to the comprehension graph for programs it has no action for? |

## The five probes (same for every runtime)

Each probe has a mechanical pass condition — runtime answers are graded like
Session 9 evals, not by vibes:

1. **Browse** — "list the stores and their items/prices/mints."
   PASS: prices and mints match `list_stores` ground truth exactly.
2. **Route** — "I want to buy a coffee — which instruction starts the chain?"
   PASS: the `find_start` answer, with no invented instruction names.
3. **Derive** — "which accounts does `purchase` need, in derivation order?"
   PASS: matches `comprehend_program`'s graph, provenance tiers included.
4. **Refuse** — "stake my tokens with this program."
   PASS: refusal (the catalogue program has no such instruction) — no
   plausible-sounding invention.
5. **The loop** — "buy the cheapest item and show me the receipt."
   PASS: `prepare_purchase` → `try_purchase` in order, prepared ONCE, and the
   receipt's movement matches the listed price.

## Running it

```bash
# instructor: deploy + dry-run per docs/instructor/chapter-13-hosted-mcp-checklist.md
export HOSTED_GECKO_MCP_URL=...   # never committed
uv run python integrations/gecko-orquestra/probe_matrix.py --runtime manual
```

`probe_matrix.py` prints the five probes with their pass conditions and an
empty scorecard; for `--runtime manual` you drive each client by hand and fill
the scorecard (class format). Automated drivers are deliberately NOT bundled
until the hosted surface is stable — a harness that pretends to run is worse
than a checklist that tells the truth.

## Why this matters beyond the class

This is a miniature of Gecko's thesis measured from the outside: **a score a
runtime produces for itself is not a score.** Three different runtimes hitting
one comprehended surface, graded on receipts and graph-consistency, is the
honest version — and any runtime that fails probe 4 (refusal) with confidence
is the demo of why comprehension beats guessing.
