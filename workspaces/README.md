# Workspaces — project sandboxes, one per week

DataCamp-style project workspaces: a brief, a dataset, milestones organized as
**Chapter 1 / 2 / 3**, and open *"Start coding here"* cells. Unlike the session
notebooks (guided, with TODOs), a workspace is open-ended — the milestones are
the contract, the route is yours. Every provided cell runs offline on the
course environment; CI executes them.

| Workspace | Week | Project | Chapters |
|---|---|---|---|
| week-1-corpus-qa — not released yet | 1 | Source-grounded Q&A over the course corpus | Know your corpus → structured answers → the refusal contract |
| week-2-retrieval-lab — not released yet | 2 | Measure retrieval, improve one thing honestly | Baseline → one change + its regression → audit the auditor |
| week-3-let-me-buy — not released yet | 3 | **The Autonomous Store** — Waiter, Store Manager, Delivery on LetMeBuy-shaped rails | Waiter + catalog → delivery as a state graph → the receipt makes it real |
| news-to-telegram — not released yet | any | A digest agent that picks the day's three stories and sends them to your phone | Source → judgement → delivery → the proof |

The week-3 workspace is the advanced finale: three bounded agents running a
store whose catalog is `store.json` offline and the **instructor-hosted Gecko
MCP surface** live (Session 13), where `try_purchase` on the fork produces a
real receipt of what moved. Extension paths (SendAI's Solana Agent Kit,
Hermes-style skill learning) are mapped in
[docs/guides/solana-agent-stacks.md](../docs/guides/solana-agent-stacks.md).

`news-to-telegram` is not tied to a week. It is a short, complete pipeline you
can finish in an evening and keep using afterwards: a free API with no key, the
`LLMClient` seam doing the one job a model is needed for, Telegram instead of
email, and a recorded fixture so the whole thing is testable offline. It also
opens with the two-minute checklist for deciding whether somebody else's
repository is worth depending on.

**Suggested rhythm:** open the week's workspace after that week's Friday
session; bring blockers to Monday's warm-up. The week-3 workspace IS the
capstone build, structured.
