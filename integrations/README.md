# Integrations — real stacks, real calls, course-grade safety

Optional, hands-on integrations with the agent stacks the Solana community
actually uses. Each one runs the smallest honest real thing and degrades
gracefully when a credential or a hosted service is missing.

| Integration | What it does | Real calls |
|---|---|---|
| [sendai-txs](sendai-txs/) | SendAI's Solana Agent Kit driving **devnet** reads and a real (tiny) transfer through the kit's own actions | `getTPS`, `get_balance`, `request_faucet_funds`, `transfer` — devnet enforced in code, `DEVNET_LIVE=1` to run |
| [hermes-telegram](hermes-telegram/) | Hermes (Nous Research) as a Telegram bot — your agent in your pocket, with the course's safety lens on self-improving memory | guided setup + `check_hermes.py` verifier (needs your BotFather token) |
| [gecko-orquestra](gecko-orquestra/) | The cross-runtime **test matrix**: the instructor's Gecko-comprehended Orquestra surface probed by Claude Code, Hermes, and a SendAI agent — same questions, graded on receipts | `probe_matrix.py` scorecard; live when the hosted surface is up |

Background reading: [docs/guides/solana-agent-stacks.md](../docs/guides/solana-agent-stacks.md)
(SendAI vs Hermes, honestly compared) and the
[Autonomous Store workspace](../workspaces/week-3-let-me-buy/), which these
integrations extend.

## House rules (all three)

- Secrets in `.env` / platform secret stores, never in git.
- Devnet or fork only — no integration here has a mainnet path, and the
  SendAI example refuses non-devnet RPCs in code.
- Every claim a runtime makes gets checked against ground truth (receipts,
  graphs, balances) — Session 9's discipline applied to other people's agents.
