# Rehearsing on a fork

Optional. Not checked. Nothing in your marks depends on a word of this.

What it buys you: your storefront becomes **real** — on a local fork of mainnet,
signed with a throwaway key that cannot reach the real network. An agent can then
list it, read the menu, and buy something, and the purchase is judged by **what
moved** rather than by what the agent said it did.

## Why this is safe, precisely

The fork is a local node that copies mainnet state on demand. The key that signs
here is generated on the spot and funded by a cheatcode; it holds nothing real
and it cannot reach mainnet. The tool that signs refuses outright unless the node
it is talking to answers `surfnet_getSurfnetInfo` — a method mainnet does not
implement. So the refusal is structural, not a setting you could get wrong.

Seeding a store needs **no key and no signature at all**: the store account is
written straight into the fork's state through a sanctioned cheatcode, then read
back through the same decode path a real purchase uses.

## Two terminals

**One — the fork.**

```bash
surfpool start --no-tui --no-deploy --rpc-url <a mainnet rpc url> --port 8899
```

Leave it running. It forks lazily, so the first read of an account is slow and
the rest are not.

**Two — seed your store, and read it back.**

Export your storefront in the shape the seeder takes:

```python
import json
from pathlib import Path

from bootcamp_agent.shipit.storefront import to_seed_config

Path("my-store.json").write_text(json.dumps(to_seed_config(MY_STORE), indent=2))
```

Then, from the Gecko repository:

```bash
uv run python scripts/semantic_seed_fork.py --config my-store.json
```

It writes the account and reads it back. If the read-back disagrees with what you
sent, stop — you have found something worth reporting rather than working around.

## Demo day

Everyone's store goes on **one** fork the instructor runs, and the agents shop
from each other.

There is one rule, and it is the reason your store name starts with your handle:
a store lives at the address derived from its **name alone**. Two people who both
call a store `coffee` write to the same account, and the second one silently
replaces the first. Distinct names mean distinct addresses, which is why N stores
coexist on one fork with no coordination at all.

Nobody hands out an address. An agent finds every store by reading the program's
accounts off the fork — including shops it has never heard of. That is the whole
claim this track is making, and it is true because the program made it true.

## What this is not

It is not mainnet, and nothing here spends anything. Going to mainnet is your own
wallet and your own decision — read the no-edit rule in the track README first.
