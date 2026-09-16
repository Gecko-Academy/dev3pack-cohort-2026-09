"""A storefront read from JSON, and every rule the program would hold it to.

The rules are here rather than in the checker because a learner should be able to
run them on their own file, get a list of what is wrong, and fix it -- offline,
in a second, without a network or a wallet. Every one of them is a rule the
deployed program enforces or a hazard its shape creates:

  - an address is 32 bytes. A placeholder that decodes to 30 is not an address,
    however much it reads like one.
  - twenty products, and no instruction to edit one. Changing a price means
    delete then add, and a partial run leaves a live store with no single-call
    way back. That is why a price change is a refusal here, not a warning.
  - a store is found at the PDA of its NAME ALONE -- no authority in the seed.
    Two learners who both name a store `coffee` write to the same address and
    the second silently overwrites the first. Hence the handle prefix.
  - a price is an integer count of the smallest unit. `1.5` USDC is `1_500_000`,
    and a float here is the bug that ships a store selling at 0.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .borsh_store import MAX_PRODUCTS, Product, Store, StoreBytesError, encode_pubkey

#: Mints whose decimals are not a matter of opinion. A store that disagrees with
#: one of these is priced wrong by a factor of a thousand or a million.
KNOWN_DECIMALS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 6,  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": 6,  # USDT
    "So11111111111111111111111111111111111111112": 9,  # wrapped SOL
}


class StorefrontError(ValueError):
    """Raised when a storefront file is not one, or describes a store that cannot exist."""


@dataclass(frozen=True)
class Problem:
    """One thing wrong, and what to do about it."""

    field: str
    detail: str

    def __str__(self) -> str:
        return f"{self.field}: {self.detail}"


def load(source: Path | str | dict) -> dict:
    """A storefront as a plain dict, from a path, a JSON string, or a dict."""
    if isinstance(source, dict):
        return source
    text = Path(source).read_text(encoding="utf-8") if Path(str(source)).exists() else str(source)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise StorefrontError(f"not JSON: {error}") from error
    if not isinstance(data, dict):
        raise StorefrontError("a storefront is an object, not a list")
    return data


def problems(source: Path | str | dict, *, handle: str | None = None) -> list[Problem]:
    """Everything wrong with this storefront, in the order worth fixing it.

    Returns a list rather than raising on the first one, because a learner fixing
    four things one error message at a time is four round trips through a file
    they can read all at once.
    """
    data = load(source)
    found: list[Problem] = []

    name = data.get("store")
    if not isinstance(name, str) or not name:
        found.append(Problem("store", "a store needs a name; it is the only seed of its address"))
    elif handle and not name.startswith(f"{handle}-"):
        found.append(
            Problem(
                "store",
                f"name it {handle}-something. A store lives at the address derived from its "
                f"NAME ALONE, so two people who both pick {name!r} write to the same account "
                "and the second one silently replaces the first",
            )
        )

    for field in ("authority",):
        value = data.get(field)
        if not isinstance(value, str):
            found.append(Problem(field, "missing"))
            continue
        try:
            encode_pubkey(value)
        except StoreBytesError as error:
            found.append(Problem(field, str(error)))

    products = data.get("products")
    if not isinstance(products, list):
        found.append(Problem("products", "missing; a store with no menu sells nothing"))
        return found
    if len(products) > MAX_PRODUCTS:
        found.append(
            Problem(
                "products",
                f"{len(products)} products, and the program takes at most {MAX_PRODUCTS}",
            )
        )

    seen: set[str] = set()
    for index, product in enumerate(products):
        where = f"products[{index}]"
        if not isinstance(product, dict):
            found.append(Problem(where, "each product is an object"))
            continue
        found.extend(_product_problems(where, product, seen))
    return found


def _product_problems(where: str, product: dict, seen: set[str]) -> list[Problem]:
    found: list[Problem] = []
    name = product.get("name")
    if not isinstance(name, str) or not name:
        found.append(Problem(where, "a product needs a name"))
    elif name in seen:
        found.append(
            Problem(
                where,
                f"{name!r} is listed twice. There is no instruction to edit a product, so two "
                "rows with one name can only be separated by deleting both",
            )
        )
    else:
        seen.add(name)

    price = product.get("price_raw")
    if isinstance(price, bool) or not isinstance(price, int):
        found.append(
            Problem(
                f"{where}.price_raw",
                f"{price!r} is not an integer. A price counts the smallest unit, so 1.5 USDC "
                "is 1500000 -- a float here is how a store ends up selling at zero",
            )
        )
    elif price <= 0:
        found.append(Problem(f"{where}.price_raw", "a price of zero is not a price"))

    mint = product.get("mint")
    if not isinstance(mint, str):
        found.append(Problem(f"{where}.mint", "missing; a price means nothing without its mint"))
        return found
    try:
        encode_pubkey(mint)
    except StoreBytesError as error:
        found.append(Problem(f"{where}.mint", str(error)))
        return found

    decimals = product.get("decimals")
    if not isinstance(decimals, int) or isinstance(decimals, bool) or not 0 <= decimals <= 18:
        found.append(Problem(f"{where}.decimals", f"{decimals!r} is not a decimals count"))
    elif mint in KNOWN_DECIMALS and decimals != KNOWN_DECIMALS[mint]:
        found.append(
            Problem(
                f"{where}.decimals",
                f"that mint has {KNOWN_DECIMALS[mint]} decimals, not {decimals}. Every price "
                "in this store is wrong by a factor of "
                f"{10 ** abs(decimals - KNOWN_DECIMALS[mint])}",
            )
        )
    return found


def to_store(source: Path | str | dict, *, handle: str | None = None) -> Store:
    """A validated :class:`Store`, or a refusal listing everything wrong."""
    found = problems(source, handle=handle)
    if found:
        listed = "\n  ".join(str(problem) for problem in found)
        raise StorefrontError(f"this storefront cannot exist:\n  {listed}")
    data = load(source)
    return Store(
        store_name=data["store"],
        authority=data["authority"],
        products=tuple(
            Product(
                name=product["name"],
                price_raw=product["price_raw"],
                decimals=product["decimals"],
                mint=product["mint"],
            )
            for product in data["products"]
        ),
        telegram_channel_id=str(data.get("telegram_channel_id", "")),
    )


def to_seed_config(source: Path | str | dict, *, handle: str | None = None) -> dict:
    """The dict the fork seeder consumes, so one script can seed a whole cohort.

    This is the ONLY place the course and the Gecko repository agree on a shape
    rather than on bytes, and it is deliberately one function: `semantic_seed_fork.py
    --config` reads exactly this.
    """
    store = to_store(source, handle=handle)
    return {
        "store": store.store_name,
        "authority": store.authority,
        "telegram_channel_id": store.telegram_channel_id,
        "items": [
            {
                "name": product.name,
                "price_lamports": product.price_raw,
                "decimals": product.decimals,
                "mint": product.mint,
            }
            for product in store.products
        ],
    }
