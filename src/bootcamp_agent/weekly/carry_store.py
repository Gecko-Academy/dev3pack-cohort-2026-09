"""Carry the student's `store.json` into the ch10 hand-in.

WHY. On Monday every student's store goes onto the shared course fork, and the
instructor needs the file to seed it. Founder decision: the store travels with
the ch10 submission the student already makes, rather than through a second
channel somebody has to remember. Demo 10 ends with the lines that write it, and
`to_seed_config` refuses a store that cannot exist, so the file only appears
once every rule passes.

WHERE IT IS LOOKED FOR. Those lines write `store.json` next to whichever
notebook ran them. Run in demo 10, that is `demos/store.json`; run in the session
10 notebook, it is that notebook's folder. Both are read. Two DIFFERENT files is
refused rather than guessed: handing the instructor the wrong store is worse than
handing in none.

WHAT IS NEVER CARRIED.
  * Anything over MAX_STORE_BYTES. A store is a few hundred bytes; a larger file
    is not one, and the submissions repository is cloned by every grader.
  * Anything that does not parse as a JSON object. The file is parsed, never
    executed or imported.
  * A symlink. A link is how a bundle picks up a file from outside the course.

A MISSING STORE IS A WARNING, NOT A FAILURE. A student who has not finished the
store still hands in their notebook and their challenge points.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from bootcamp_agent.submission import STORE_FILE

#: Only session 10 carries a store. Must match `STORE_ITEMS` in `check_bundle.py`.
STORE_ITEM = "ch10"

#: Must match `MAX_STORE_BYTES` in `check_bundle.py`, which refuses a larger file.
MAX_STORE_BYTES = 64 * 1024

#: Where demo 10's lines write the file when run in the demo, course-relative.
STORE_PLACE = f"demos/{STORE_FILE}"


@dataclass(frozen=True)
class StoreOutcome:
    """The store's bytes to attach, if any, and the one line to tell the learner."""

    raw: bytes | None = None
    message: str = ""


def _shown(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _places(root: Path, session: Path | None) -> list[Path]:
    places = [root / STORE_PLACE]
    if session is not None:
        beside = session.parent / STORE_FILE
        if beside.absolute() != places[0].absolute():
            places.append(beside)
    return places


def carry_store(item_id: str, root: Path, session: Path | None = None) -> StoreOutcome:
    """Decide whether `item_id`'s hand-in carries the student's `store.json`.

    `session` is the session notebook being handed in; a store written beside it
    counts as much as one written beside demo 10.
    """
    if item_id != STORE_ITEM:
        return StoreOutcome()

    found = [p for p in _places(root, session) if p.exists() or p.is_symlink()]
    if not found:
        return StoreOutcome(
            message=(
                f"no {STORE_FILE} at {STORE_PLACE}, so your store is not in this hand-in. "
                "Your notebook is handed in without it. To add it, run the lines under "
                '"For Monday" at the end of demo 10: they write the file once every rule '
                "passes. Then submit ch10 again."
            )
        )

    stores: list[tuple[Path, bytes]] = []
    for path in found:
        shown = _shown(path, root)
        if path.is_symlink() or not path.is_file():
            return StoreOutcome(message=f"not carrying {shown}: it must be a regular file.")
        # Checked before reading, so an enormous file is never pulled into memory.
        size = path.stat().st_size
        if size > MAX_STORE_BYTES:
            return StoreOutcome(
                message=(
                    f"not carrying {shown}: it is {size} bytes, over the "
                    f"{MAX_STORE_BYTES}-byte cap. A store is a few hundred bytes. "
                    "Write it again with the lines in demo 10, then submit again."
                )
            )
        raw = path.read_bytes()
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError) as error:
            return StoreOutcome(
                message=(
                    f"not carrying {shown}: it is not JSON ({error}). "
                    "Write it with the lines in demo 10, then submit again."
                )
            )
        if not isinstance(document, dict):
            return StoreOutcome(
                message=(
                    f"not carrying {shown}: a store is a JSON object, and this is "
                    f"a {type(document).__name__}. Write it with the lines in demo 10."
                )
            )
        stores.append((path, raw))

    if len({raw for _, raw in stores}) > 1:
        names = " and ".join(_shown(path, root) for path, _ in stores)
        return StoreOutcome(
            message=(
                f"not carrying a store: there are two different {STORE_FILE} files, "
                f"{names}. Delete the one you do not mean, then submit again."
            )
        )

    path, raw = stores[0]
    return StoreOutcome(raw=raw, message=f"carrying your store from {_shown(path, root)}")


__all__ = ["MAX_STORE_BYTES", "STORE_ITEM", "STORE_PLACE", "StoreOutcome", "carry_store"]
