# Fixtures

## `geckocoffee-store.b64`

The `Receipts` account bytes for a two-product storefront, **produced by the real
encoder in the Gecko repository** (`gecko.store_directory.encode_store`) and
pasted here once.

It exists because `bootcamp_agent.shipit.borsh_store` is a hand-written copy of
that layout, kept in the standard library so this track needs no dependency. A
copy can drift, and a drifted copy goes on passing its own tests while describing
an account the program no longer writes.

So the copy is pinned from both sides:

- `tests/test_shipit_borsh.py`, here, asserts our encoder reproduces these bytes
  and our decoder reads them;
- `tests/test_bootcamp_layout_parity.py`, in the Gecko repository, asserts the
  real encoder still produces them.

Whichever side moves is the side that turns red. Self-consistency would prove
nothing, which is why one test would not have been enough.

The store is real in shape and fictional in content: the authority is a public
address, the mint is mainnet USDC, and nobody has ever bought anything from it.
