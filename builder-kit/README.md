# Builder Kit — the bootcamp as a Claude Code plugin

The course's working patterns, packaged so any repo can use them. This
repository is its own Claude Code **marketplace** serving one plugin.

## Install (inside Claude Code)

```text
/plugin marketplace add ernanibmurtinho/Dev3Pack-bootcamp-AI-Engineering
/plugin install dev3pack-builder-kit@dev3pack
```

Commands and skills are namespaced: `/bootcamp-doctor` becomes
`/dev3pack-builder-kit:bootcamp-doctor`.

## What ships

| Piece | What it does |
|---|---|
| `store-builder` skill | Scaffolds the **Waiter / Store Manager / Delivery** pattern: bounded tools, an explicit state graph, the receipt rule, a golden set with an injection case |
| `corpus-answers` skill | Grounded Q&A discipline: verified citations, refusal on unsupported questions, trace-first debugging |
| `/bootcamp-doctor` command | Runs the setup doctor + test suite and reports the exact next command for anything red |

## The design rules the kit encodes

1. **Refusal paths first** — an agent that cannot refuse will fabricate (or
   sell what it doesn't have).
2. **Validation at the boundary** — no tool trusts model-produced arguments.
3. **The receipt rule** — nothing that counts happens without a verifiable
   record of what moved.
4. **Evals over vibes** — every skill ends with the command that proves it.

Format follows [Agent Plugins](https://code.claude.com/schemas/plugin.json)
as adopted by Superteam Brasil's solana-ai-kit — same marketplace shape, so
both kits can live side by side in one Claude Code setup.
