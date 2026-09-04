# Solana Agent Stacks — SendAI vs Hermes (and where this course sits)

Two names come up constantly in the Solana agent community, and they are
**different layers**, not competitors. Neither is used in the course's core
exercises — this guide exists so you leave knowing the map, and so the
Autonomous Store workspace has named extension paths.

## SendAI — the Solana Agent Kit

[SendAI](https://www.sendai.fun/) is an applied AI lab building the
infrastructure layer for agents operating on Solana. Its
[Solana Agent Kit](https://github.com/sendaifun/solana-agent-kit) is the most
direct path to an agent that *acts* on-chain: **60+ pre-built actions** (token
operations, transfers, NFT minting, DeFi interactions) behind a modular plugin
architecture, with clean integrations for LangChain and the Vercel AI SDK.

**The mental model:** a box of pre-built, named verbs. You install the plugins
you need and your agent gains those actions — fast, batteries included.

**The contrast with what you built here:** the Agent Kit ships *pre-built*
actions for known protocols; Gecko *derives* actions from comprehension of any
program's surface, with provenance on every claim. Pre-built wins on speed for
covered protocols; comprehension wins on the long tail and on "how do I know
this call is right?" They compose: a comprehended surface can tell you when a
pre-built action is the right one to reach for.

## Hermes — the self-improving agent framework

[Hermes](https://techjacksolutions.com/ai-tools/hermes/hermes-breakdown/) is
Nous Research's open-source agent framework, and its distinguishing idea is
**self-improvement**: the agent keeps a persistent memory of its own successes
and failures and distills the patterns into **reusable skills** — so the agent
you run after a month is measurably different from the one you started with.
It is general-purpose (multi-platform, multi-model), not Solana-specific.

**The mental model:** your Session-10 `SKILL.md` discipline, automated — the
agent writes and refines its own skills from experience.

**The caution this course equips you to state:** a memory that feeds future
behavior is an *injection surface that persists* (Session 11's staleness and
poisoning risks, Session 14's untrusted-content rule). Self-improvement without
an evaluation harness is drift with good marketing — if you adopt Hermes-style
skill learning, your golden set is what tells you whether the agent actually
got better.

## The one-table version

| | SendAI Solana Agent Kit | Hermes (Nous Research) |
|---|---|---|
| Layer | On-chain **actions** for agents | Agent **framework / harness** |
| Scope | Solana-specific | General-purpose |
| Superpower | 60+ pre-built verbs, plugins, LangChain/Vercel integration | Persistent memory → self-generated reusable skills |
| Course thread it extends | Session 5 tools · Session 13 acting on-chain | Session 10 skills · Session 11 memory |
| What to demand before trusting it | The same receipt discipline as Session 13 — a pre-built action that spends still needs verification before it counts | An eval set — self-improvement claims are measurable or they are vibes |

## Where to try them

The [Autonomous Store workspace](../../workspaces/week-3-let-me-buy/) names
both as extension paths: give the store more on-chain verbs with the Agent
Kit, or give the Waiter a Hermes-style learned-skill loop — and in both cases,
keep the receipt rule and the golden set from the core project.
