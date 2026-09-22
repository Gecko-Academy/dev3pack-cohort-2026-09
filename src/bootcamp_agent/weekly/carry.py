"""Carry a weekly challenge done in its DEMO notebook into the session's hand-in.

WHY. The challenge's points are read from the handed-in bundle, and most of week
1 was done in `demos/08_the_weekly_challenge.ipynb`, which is never handed in.
So `bootcamp submit ch05` (and `ch10`) attaches a byte-for-byte copy of the saved
demo as `challenge.ipynb`, and the track reads the same line out of it that it
reads out of `notebook.ipynb`. Nobody has to move code between notebooks.

WHAT IS NEVER CARRIED.
  * A demo whose code is still the code it shipped with. Demo 8 ships SAVED with
    the worked example's `week 1 challenge: 300/500`, so carrying any demo that
    has the line would hand every fresh clone 300 points for nothing -- and so
    would re-running the example unchanged. "Your code" is the test: the digest
    of the code cells must differ from every version the course has shipped.
  * A demo over the checker's notebook cap, which CI would refuse outright and
    take the session's own work down with it.
  * Another week's line: week 2 in demo 8 is not week 1.

The line and the reading of it mirror `render_track.challenge_of` in the
submissions repository; change them together or not at all.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from bootcamp_agent.submission import CHALLENGE_FILE
from bootcamp_agent.weekly import CHALLENGES

#: `check_bundle.MAX_NOTEBOOK_BYTES` in the submissions repository: the same cap
#: the checker applies to `notebook.ipynb`, and it applies to this file too.
MAX_CHALLENGE_BYTES = 8 * 1024 * 1024

CHALLENGE_LINE = re.compile(r"^\s*week (1|2) challenge: (\d{1,3})/500\s*$")
CHALLENGE_MAX = 500

#: Where each session's challenge demo lives, relative to the course root.
DEMOS: dict[str, str] = {
    "ch05": "demos/08_the_weekly_challenge.ipynb",
    "ch10": "demos/10_your_store_and_buyer.ipynb",
}

#: Digests (`code_digest`) of the demo code AS SHIPPED, every version of it. A
#: test holds the current file to this set, so editing a demo without adding its
#: new digest fails before a student can be credited for the course's own code.
SHIPPED_CODE: dict[str, frozenset[str]] = {
    "ch05": frozenset({"6b747c47f35cb21271d33c2e2fc64f7e493abc1dd7f77a0a50e9b7f99bdd1821"}),
    "ch10": frozenset({"2516f811f6c0245daf1f18e91df3bf7fabb1d85ca1afd638dc5d282d59ceb465"}),
}


@dataclass(frozen=True)
class Carried:
    """A demo notebook to hand in beside the session's, and what it scored."""

    source: str  # course-relative, for the line the learner reads
    raw: bytes  # read once: the bytes hashed are the bytes written
    points: int


@dataclass(frozen=True)
class Outcome:
    """What to attach, if anything, and the one line to tell the learner."""

    carried: Carried | None = None
    message: str = ""


def _code_cells(notebook: dict) -> list[dict]:
    cells = notebook.get("cells") or []
    return [c for c in cells if isinstance(c, dict) and c.get("cell_type") == "code"]


def _text(value: object) -> str:
    if isinstance(value, list):
        return "".join(part for part in value if isinstance(part, str))
    return value if isinstance(value, str) else ""


def code_digest(notebook: dict) -> str:
    """One digest over every code cell's source; line endings are not content."""
    joined = "\n\x00\n".join(_text(cell.get("source")) for cell in _code_cells(notebook))
    return hashlib.sha256(joined.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def points_in(notebook: object, week: int) -> int | None:
    """The LAST `week N challenge` line of this week in saved stream output, capped.

    None when there is no such line, which is different from a line saying 0.
    """
    if not isinstance(notebook, dict):
        return None
    points: int | None = None
    for cell in _code_cells(notebook):
        for output in cell.get("outputs") or []:
            if not isinstance(output, dict) or output.get("output_type") != "stream":
                continue
            for line in _text(output.get("text")).splitlines():
                found = CHALLENGE_LINE.match(line)
                if found and found.group(1) == str(week):
                    points = min(int(found.group(2)), CHALLENGE_MAX)
    return points


def _ran_but_unsaved(notebook: dict, bonus_id: str) -> bool:
    """The challenge's `bonus(...)` cell is there, with nothing saved under it."""
    call = f'bonus("{bonus_id}"'
    return any(
        call in _text(cell.get("source")) and not cell.get("outputs")
        for cell in _code_cells(notebook)
    )


def _session_has_line(session: Path | None, week: int) -> bool:
    if session is None or not session.is_file():
        return False
    try:
        return points_in(json.loads(session.read_bytes()), week) is not None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False


def carry(item_id: str, root: Path, session: Path | None = None) -> Outcome:
    """Decide whether `item_id`'s hand-in carries its challenge demo from `root`.

    `session` is the session notebook being handed in. When it already carries
    its own challenge line, the untouched demo is not worth a word: the learner
    did the challenge where the page told them to.
    """
    challenge = CHALLENGES.get(item_id)
    relative = DEMOS.get(item_id)
    if challenge is None or relative is None:
        return Outcome()
    path = root / relative
    if not path.is_file() or path.is_symlink():
        return Outcome()

    raw = path.read_bytes()
    try:
        notebook = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return Outcome()
    # The checker accepts `challenge.ipynb` only as JSON with a `cells` list.
    if not isinstance(notebook, dict) or not isinstance(notebook.get("cells"), list):
        return Outcome()

    week = challenge.week
    points = points_in(notebook, week)
    if points is None:
        if _ran_but_unsaved(notebook, challenge.bonus_id):
            return Outcome(
                message=(
                    f"{relative} has no saved week {week} challenge result: run its "
                    f'bonus("{challenge.bonus_id}", ...) cell, save it, then submit again.'
                )
            )
        return Outcome()

    if code_digest(notebook) in SHIPPED_CODE.get(item_id, frozenset()):
        if _session_has_line(session, week):
            return Outcome()
        return Outcome(
            message=(
                f"not carrying {relative}: its code is still the course's example, so "
                f"its {points}/{CHALLENGE_MAX} is not yours. Write your own there, run it, save."
            )
        )

    if len(raw) > MAX_CHALLENGE_BYTES:
        return Outcome(
            message=(
                f"not carrying {relative}: it is {len(raw)} bytes, over the "
                f"{MAX_CHALLENGE_BYTES}-byte cap. Clear large outputs, save, submit again."
            )
        )

    return Outcome(
        carried=Carried(source=relative, raw=raw, points=points),
        message=f"carrying your week {week} challenge from {relative}: {points}/{CHALLENGE_MAX}",
    )


__all__ = [
    "CHALLENGE_FILE",
    "DEMOS",
    "MAX_CHALLENGE_BYTES",
    "SHIPPED_CODE",
    "Carried",
    "Outcome",
    "carry",
    "code_digest",
    "points_in",
]
