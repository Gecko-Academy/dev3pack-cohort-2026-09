"""The ``let_me_buy`` store account, encoded and decoded in the standard library.

This is a MIRROR of ``gecko.store_directory.encode_store`` / ``decode_store``,
written out in stdlib so the track needs no dependency. A mirror is a liability:
the original can change and this copy would go on passing its own tests while
quietly describing an account the program no longer writes.

SO THE MIRROR IS PINNED, NOT TRUSTED. ``fixtures/geckocoffee-store.b64`` holds
bytes produced by the real encoder on a fixed listing. ``tests/test_shipit_borsh.py``
asserts this module reproduces them exactly, and a matching test in the Gecko
repository asserts the real encoder still produces the same bytes. Either side
drifting turns a test red on the side that moved. Self-consistency proves
nothing; that pair is what makes this file safe to keep.

THE LAYOUT, in the order the account is written:

    8   discriminator          sha256("account:Receipts")[:8]
    4   receipts vec length    always 0 here -- a receipt names a real buyer
    8   total_purchases        u64, little endian
    ..  store_name             u32 length prefix, then utf-8
    32  authority              raw pubkey bytes
    4   products length        u32
        per product:
    8       price_raw          u64, in the mint's smallest unit -- never a float
    1       decimals           u8
    32      mint               raw pubkey bytes
    ..      name               u32 length prefix, then utf-8
    ..  telegram_channel_id    u32 length prefix, then utf-8

``price_raw`` is the field most often got wrong: it is an integer count of the
smallest unit, so one USDC at six decimals is ``1_000_000`` and never ``1.0``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

#: Base58, in Bitcoin's alphabet -- the one Solana uses.
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

#: A Solana public key is exactly this many bytes. Nothing else is a pubkey,
#: however much it looks like one.
PUBKEY_BYTES = 32

#: The program refuses a store above this. `gecko/showcase.py` carries the same
#: number, and there is no instruction to edit a product -- so a store that hits
#: the cap can only be changed by deleting, which is the hazard the planner
#: exercise is about.
MAX_PRODUCTS = 20


class StoreBytesError(ValueError):
    """Raised for bytes that are not a store, and for a store that cannot exist."""


def b58decode(text: str) -> bytes:
    """Decode base58 into bytes, leading zeros preserved.

    Raises on any character outside the alphabet rather than skipping it, because
    a silently-dropped character produces a valid-looking key that is not the one
    the caller meant.
    """
    if not text:
        raise StoreBytesError("an empty string is not an address")
    number = 0
    for character in text:
        index = ALPHABET.find(character)
        if index < 0:
            raise StoreBytesError(
                f"{character!r} is not a base58 character, so {text!r} is not an address"
            )
        number = number * 58 + index
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    padding = len(text) - len(text.lstrip("1"))
    return b"\x00" * padding + body


def b58encode(raw: bytes) -> str:
    number = int.from_bytes(raw, "big")
    out = ""
    while number:
        number, remainder = divmod(number, 58)
        out = ALPHABET[remainder] + out
    return "1" * (len(raw) - len(raw.lstrip(b"\x00"))) + out


def encode_pubkey(address: str) -> bytes:
    """The 32 raw bytes of an address, or a refusal naming the length it got.

    The refusal matters more than the success. A placeholder like
    ``DemoAuthority1111...`` decodes to 30 bytes and looks entirely plausible in
    a JSON file; it is only here, at the byte boundary, that it stops being an
    address.
    """
    raw = b58decode(address)
    if len(raw) != PUBKEY_BYTES:
        raise StoreBytesError(
            f"{address!r} decodes to {len(raw)} bytes; a Solana address is "
            f"{PUBKEY_BYTES}. It reads like an address but cannot be one."
        )
    return raw


def receipts_discriminator() -> bytes:
    """Anchor's 8-byte tag for the ``Receipts`` account, derived rather than pasted.

    A wrong discriminator is the quietest possible mistake: reading a store skips
    these bytes, so a store seeded with the wrong tag lists perfectly and cannot
    be bought from.
    """
    return hashlib.sha256(b"account:Receipts").digest()[:8]


@dataclass(frozen=True)
class Product:
    name: str
    price_raw: int
    decimals: int
    mint: str


@dataclass(frozen=True)
class Store:
    store_name: str
    authority: str
    products: tuple[Product, ...] = ()
    telegram_channel_id: str = ""
    total_purchases: int = 0


@dataclass
class _Cursor:
    raw: bytes
    at: int = 0

    def take(self, count: int) -> bytes:
        end = self.at + count
        if end > len(self.raw):
            raise StoreBytesError(
                f"wanted {count} bytes at offset {self.at}, but the account holds "
                f"{len(self.raw)} -- these are not a whole store"
            )
        chunk = self.raw[self.at : end]
        self.at = end
        return chunk

    def u8(self) -> int:
        return self.take(1)[0]

    def u32(self) -> int:
        return int.from_bytes(self.take(4), "little")

    def u64(self) -> int:
        return int.from_bytes(self.take(8), "little")

    def string(self) -> str:
        return self.take(self.u32()).decode("utf-8")

    def pubkey(self) -> str:
        return b58encode(self.take(PUBKEY_BYTES))


def _encode_string(text: str) -> bytes:
    body = text.encode("utf-8")
    return len(body).to_bytes(4, "little") + body


def encode_store(store: Store) -> bytes:
    """A :class:`Store` as the account bytes the program would write.

    The receipts vec is always seeded empty. A receipt names a real buyer, and
    inventing buyers would make the fork tell a story that never happened.
    """
    parts = [
        receipts_discriminator(),
        (0).to_bytes(4, "little"),
        store.total_purchases.to_bytes(8, "little"),
        _encode_string(store.store_name),
        encode_pubkey(store.authority),
        len(store.products).to_bytes(4, "little"),
    ]
    for product in store.products:
        parts.append(product.price_raw.to_bytes(8, "little"))
        parts.append(bytes([product.decimals]))
        parts.append(encode_pubkey(product.mint))
        parts.append(_encode_string(product.name))
    parts.append(_encode_string(store.telegram_channel_id))
    return b"".join(parts)


def decode_store(raw: bytes) -> Store:
    """Account bytes back into a :class:`Store`.

    The receipts vec is walked past without being returned. Those rows carry real
    buyers, and a teaching exercise has no business holding them.
    """
    cursor = _Cursor(raw, at=8)
    for _ in range(cursor.u32()):
        cursor.take(PUBKEY_BYTES)
        cursor.u64()
        cursor.string()
    total_purchases = cursor.u64()
    store_name = cursor.string()
    authority = cursor.pubkey()
    products = []
    for _ in range(cursor.u32()):
        price_raw = cursor.u64()
        decimals = cursor.u8()
        mint = cursor.pubkey()
        products.append(
            Product(name=cursor.string(), price_raw=price_raw, decimals=decimals, mint=mint)
        )
    # A store written before this field existed simply ends here. Absent is a
    # fact about the store, not a reason to refuse to read it.
    try:
        telegram_channel_id = cursor.string()
    except StoreBytesError:
        telegram_channel_id = ""
    return Store(
        store_name=store_name,
        authority=authority,
        products=tuple(products),
        telegram_channel_id=telegram_channel_id,
        total_purchases=total_purchases,
    )
