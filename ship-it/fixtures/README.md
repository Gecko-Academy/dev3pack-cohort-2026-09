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

## `gspike2038-store.b64`

The whole `Receipts` account of devnet store `gspike2038` (PDA
`4kp1ocBmy7a4NZpV6B6hzHSbcpF43izAAumRiFJHnZZC`), fetched read-only with
`getAccountInfo` from `https://api.devnet.solana.com` after two purchases.

Every fixture before it had sold nothing, so the receipt layout was never read,
and the decoder had it wrong: any store with one sale failed to decode. This one
has two receipts, so a wrong receipt layout turns `tests/test_shipit_borsh.py`
red. It is public account data: a store name, a public authority, a devnet mint
and one public buyer address.
