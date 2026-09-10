"""The track: who handed in what, and what it was worth.

A PURE FOLD OVER THE SUBMISSIONS TREE. Given the merged bundles, this produces
the track and nothing else produces it. Regenerating from a clean checkout must
reproduce the same bytes, which is what makes the rendered files safe to commit:
if they ever differ, the submissions are right and the rendered file was stale.

WHAT IT NEVER DOES. It does not open a notebook. It parses `submission.json` and
reads the curriculum, and that is the whole of its diet. Two consequences worth
stating: it can hold a write token in CI where the verifier never can, because it
shares no process with untrusted code; and it cannot leak anything a student
wrote, because it never reads it.

SCORES CARRY WHERE THEY CAME FROM. A claim is not a verdict. Until somebody
re-runs the notebook, a row is `claimed`; an item that can never be re-run is
`unverifiable` and says why; an item nobody has to mark is `handed in`. Printing
"unverified" against work that was fine reads to a student as an accusation, so
the tiers are kept apart.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from bootcamp_agent import submission
from bootcamp_agent.curriculum import CAPSTONE, CHAPTERS

#: What a row can honestly say about itself.
VERIFIED = "verified"
CLAIMED = "claimed"
UNVERIFIABLE = "unverifiable"
HANDED_IN = "handed in"


@dataclass(frozen=True)
class Entry:
    """One student's current submission for one chapter or unit."""

    github: str
    item: str
    submitted_at: str
    ran: bool
    passed: tuple[str, ...]
    failed: tuple[str, ...]
    not_reached: tuple[str, ...]
    scored: bool
    score: int | None
    max_score: int | None
    tier: str
    note: str

    @property
    def cell(self) -> str:
        """How this reads in a table, in one short string."""
        if not self.scored:
            return "handed in"
        return f"{self.score}/{self.max_score}"


@dataclass(frozen=True)
class Track:
    """Every current submission, plus whatever could not be read."""

    cohort: str
    entries: tuple[Entry, ...]
    problems: tuple[str, ...]

    @property
    def students(self) -> tuple[str, ...]:
        return tuple(sorted({entry.github for entry in self.entries}))

    def by_student(self, github: str) -> dict[str, Entry]:
        return {entry.item: entry for entry in self.entries if entry.github == github}

    def scored_total(self, github: str) -> tuple[int, int]:
        """Marks earned and marks available, over the scored items handed in."""
        rows = [e for e in self.by_student(github).values() if e.scored and e.score is not None]
        return sum(e.score or 0 for e in rows), sum(e.max_score or 0 for e in rows)


def _tier(claim: dict, item: submission.Submittable, verified: bool) -> str:
    if not item.scored:
        return HANDED_IN
    if not item.verifiable:
        return UNVERIFIABLE
    return VERIFIED if verified else CLAIMED


def read_entry(claim_path: Path, verified_hashes: frozenset[str] = frozenset()) -> Entry:
    """One bundle to one row. Raises `ValueError` naming the file and the reason.

    Every message carries the path, because the reader is an instructor looking
    at two hundred submissions and "Expecting property name" tells them nothing
    about which one to open.
    """
    try:
        claim = json.loads(claim_path.read_text())
    except json.JSONDecodeError as error:
        raise ValueError(f"{claim_path}: not valid JSON ({error})") from error

    if claim.get("schema") != submission.SCHEMA:
        raise ValueError(
            f"{claim_path}: schema {claim.get('schema')!r}, expected {submission.SCHEMA!r}"
        )

    github = str(claim.get("student", {}).get("github", ""))
    owner = claim_path.parent.parent.name
    if github != owner:
        raise ValueError(f"{claim_path}: claims {github!r} but sits in {owner!r}")

    try:
        item = submission.resolve(str(claim.get("chapter", "")))
    except (KeyError, submission.SubmissionError) as error:
        raise ValueError(f"{claim_path}: {error}") from error

    digest = str(claim.get("evidence", {}).get("notebook_sha256", ""))
    result = claim.get("result", {})
    return Entry(
        github=github,
        item=item.id,
        submitted_at=str(claim.get("submitted_at", "")),
        ran=bool(result.get("ran", True)),
        passed=tuple(result.get("passed", []) or ()),
        failed=tuple(result.get("failed", []) or ()),
        not_reached=tuple(result.get("not_reached", []) or ()),
        scored=bool(result.get("scored", item.scored)),
        score=result.get("score"),
        max_score=result.get("max_score"),
        tier=_tier(claim, item, digest in verified_hashes),
        note=str(claim.get("note", "")),
    )


def read_tree(root: Path, cohort: str = "2026-09", verified: frozenset[str] = frozenset()) -> Track:
    """Fold a `submissions/` tree into a track.

    Collects problems rather than raising, because one malformed bundle must not
    hide two hundred good ones. `verified` holds the notebook hashes a re-run has
    agreed with, so a re-submission drops its predecessor's verification instead
    of inheriting it.
    """
    entries: list[Entry] = []
    problems: list[str] = []
    if not root.is_dir():
        return Track(cohort=cohort, entries=(), problems=(f"no submissions tree at {root}",))

    for claim_path in sorted(root.glob("*/*/submission.json")):
        try:
            entries.append(read_entry(claim_path, verified_hashes=verified))
        except ValueError as error:
            problems.append(str(error))
        except OSError as error:
            problems.append(f"{claim_path}: could not be read ({error})")

    return Track(cohort=cohort, entries=tuple(entries), problems=tuple(problems))


def submittable_items() -> tuple[submission.Submittable, ...]:
    """Every chapter that can be handed in, in course order.

    Week 0 is deliberately absent from the table's columns: it is self-paced and
    unmarked, so it belongs in a student's own row rather than in a grid that
    invites comparison. It still appears in that student's summary.
    """
    items = []
    for chapter in CHAPTERS:
        try:
            items.append(submission.resolve(chapter.chapter_id))
        except submission.SubmissionError:
            continue  # demo day has no notebook
    items.append(submission.resolve(CAPSTONE.prefix))
    return tuple(items)
