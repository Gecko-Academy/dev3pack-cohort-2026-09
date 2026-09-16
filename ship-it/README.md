# Ship It

Turn your capstone into a surface somebody else can call, and a storefront an
agent can buy from.

Optional. Ungraded. Runs offline, costs nothing, and needs no wallet.

```bash
uv run jupyter lab ship-it/notebook.ipynb
```

## The three lanes, and which one you are in

The course draws this table in session 13. This track does not invent a new
safety posture; it uses that one, which is what stops "launch" from meaning
"spend".

| Lane | What it needs | What it can do |
|---|---|---|
| **offline** | nothing | everything this track checks |
| public read-only | a connection | read what a real store charges today |
| fork | the instructor | sign, throwaway key, disposable fork |
| **never** | — | **spend real money because a notebook told it to** |

Everything checked here is in the first row.

## What you hand somebody else

Not a notebook. A **surface**:

1. **An MCP server** over your capstone's tools, with an entry point another
   learner installs in one line. A package plus `uvx` is a launch — you do not
   need a hosting account and there is nothing to pay for.
2. **A storefront** — a `store.json` the deployed `let_me_buy` program would
   actually accept. Checked offline against its real rules.
3. **A buyer** that reads a menu it has never seen, buys under a budget, and
   refuses correctly when it cannot pay.

## The rules that are not arbitrary

Every refusal in `bootcamp_agent.shipit.storefront` is a rule the deployed
program enforces, or a hazard the program's shape creates. Four worth knowing
before you write the file:

**An address is 32 bytes.** The week-3 fixture ships mints like
`EspressoMint111111111111111111111111111111`. That decodes to 31 bytes. It reads
exactly like an address in a text editor and cannot be one. The byte boundary is
the first place it stops being plausible.

**A store lives at the address derived from its NAME alone.** The owner is not in
the seed. Two people who both call their store `coffee` write to the same
account, and the second one silently replaces the first. Prefix yours with your
GitHub handle.

**A price counts the smallest unit.** One and a half USDC is `1500000`, not
`1.5`. A float here is how a store ends up selling at 0.0000015.

**There is no instruction to edit a product.** Changing a price means deleting
and adding, and a run that stops in the middle leaves a live store with no
one-call way back. This is why a duplicate product name is a refusal rather than
a warning.

## Optional, above the line

**Rehearse on a fork.** See [`seed/RUNBOOK.md`](seed/RUNBOOK.md). Your storefront
becomes real on a local fork of mainnet, signed with a throwaway key that cannot
reach the real network.

**Mainnet.** Your own wallet, your own cents, your own call. Nothing in this
track will do it for you and nothing here is graded on it.

## Files

| Path | What it is |
|---|---|
| `notebook.ipynb` | The track. Offline, runs in CI. |
| `fixtures/` | The golden store bytes and the recorded listings. See its README. |
| `seed/RUNBOOK.md` | The two-terminal fork recipe. Prose only; nothing here runs it for you. |
