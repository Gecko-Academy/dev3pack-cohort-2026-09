"""Turn a chapter's result into a submission somebody else can check.

WHAT IS VERIFIABLE, AND WHAT IS NOT. This is the whole design, so it is stated
first.

  * `result` — which exercises passed, failed, or were never reached. This is a
    CLAIM in the file and a FACT after `scripts/verify_submission.py` re-runs the
    submitted notebook. The notebook is the arbiter, here as everywhere else.
  * `evidence.notebook_sha256` — binds the claim to one exact file, so nobody
    submits the score of one notebook next to a different notebook.
  * `help` — whether a hint or a reveal was taken. This comes from the learner's
    own machine and CANNOT be verified by re-running, because the progress
    database never leaves their laptop. It is on the honour system, and it only
    ever COSTS marks, so there is no incentive to over-report it. Under-reporting
    inflates a score by at most the help that was taken, which we accept.

WHY THERE IS NO SIGNATURE. A secret that ships to the learner's machine is not a
secret, so a locally-produced signature would prove only that our own code ran.
Verification happens by re-running the work, which is a stronger claim than any
signature we could issue here. The one HMAC in this course is on the certificate,
where the founder holds the key and signs at demo day.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from bootcamp_agent.coursework import Scorecard
from bootcamp_agent.curriculum import (
    CAPSTONE,
    WEEK0_UNITS,
    Chapter,
    exercise_ids,
    get_chapter,
    unit_exercise_ids,
)

__all__ = [
    "SCHEMA",
    "Help",
    "SubmissionError",
    "build",
    "compare",
    "exercise_ids",
    "help_taken",
    "score_for",
    "write",
]
from bootcamp_agent.hints import FULL_MARKS, HINT_COST, REVEAL_COST, all_attempts

SCHEMA = "dev3pack.submission.v2"

#: The file names a submission directory holds. CI refuses anything else, because
#: the 30-days repository shows what happens without that rule: files land at the
#: submissions root, in folders named after nobody, and nothing can be graded.
SUBMISSION_FILE = "submission.json"
NOTEBOOK_FILE = "notebook.ipynb"


@dataclass(frozen=True)
class Submittable:
    """One thing a learner can hand in, and what may honestly be said about it.

    TWO AXES, AND THEY ARE NOT THE SAME. `verifiable` is whether CI can re-run the
    notebook at all; `scored` is whether marks are awarded. They come apart in
    both directions:

      * a week-0 unit runs perfectly well in CI and is NOT scored, because the
        prerequisite is self-paced and the founder chose to keep it ungraded;
      * chapters 4 and 10 are assistant-driven, so they can never be re-run, and
        are handed in rather than marked.

    Collapsing the two would print "unverified" against work that was fine, which
    reads to a student as an accusation.
    """

    id: str
    title: str
    notebook: Path
    exercises: tuple[str, ...]
    verifiable: bool
    scored: bool
    note: str

    @property
    def max_score(self) -> int | None:
        return len(self.exercises) * FULL_MARKS if self.scored else None


def resolve(token: str) -> Submittable:
    """A chapter id (`ch03`, `3`) or a week-0 unit id (`w05`, `unit-05-...`)."""
    stripped = token.strip().lower()

    for unit in WEEK0_UNITS:
        if stripped in {unit.prefix, unit.slug, unit.dirname, str(unit.number)}:
            return Submittable(
                id=unit.prefix,
                title=unit.title,
                notebook=unit.notebook,
                exercises=unit_exercise_ids(unit.prefix),
                verifiable=True,
                scored=False,
                note="week 0 is handed in as a record of the work, and is not marked",
            )

    if stripped in {CAPSTONE.prefix, CAPSTONE.slug}:
        return Submittable(
            id=CAPSTONE.prefix,
            title=CAPSTONE.title,
            notebook=CAPSTONE.notebook,
            exercises=unit_exercise_ids(CAPSTONE.prefix),
            verifiable=True,
            scored=True,
            note="",
        )

    chapter = get_chapter(stripped)
    if chapter.notebook is None:
        raise SubmissionError(f"{chapter.chapter_id} has no notebook to submit")
    runs_in_ci = chapter.runs_in_ci
    return Submittable(
        id=chapter.chapter_id,
        title=chapter.title,
        notebook=chapter.notebook,
        exercises=exercise_ids(chapter.chapter_id),
        verifiable=runs_in_ci,
        scored=runs_in_ci,
        note=(
            ""
            if runs_in_ci
            else "assistant-driven, so it cannot be re-run; handed in rather than marked"
        ),
    )


class SubmissionError(Exception):
    """The submission could not be built or does not hold together."""


@dataclass(frozen=True)
class Help:
    """How much help was taken. COUNTS, never exercise ids.

    A submission is committed to a PUBLIC repository under the learner's real
    GitHub identity, permanently. Ids here would publish which exercise defeated
    which person, which is the inference the Week 0 privacy promise exists to
    prevent. The cost arithmetic only ever needed the count.
    """

    hinted: int = 0
    revealed: int = 0

    @classmethod
    def of(cls, hinted: int = 0, revealed: int = 0) -> Help:
        return cls(hinted=hinted, revealed=revealed)

    def cost(self) -> int:
        """Marks given up. A reveal supersedes a hint on the same exercise."""
        return self.revealed * REVEAL_COST + self.hinted * HINT_COST

    def as_dict(self) -> dict[str, int]:
        return {"hinted": self.hinted, "revealed": self.revealed, "cost": self.cost()}

    @classmethod
    def from_dict(cls, payload: object) -> Help:
        """Read a claim's help block. A malformed one counts as no help declared."""
        if not isinstance(payload, dict):
            return cls()
        hinted = payload.get("hinted", 0)
        revealed = payload.get("revealed", 0)
        if not isinstance(hinted, int) or not isinstance(revealed, int):
            return cls()
        return cls(hinted=max(hinted, 0), revealed=max(revealed, 0))


def help_taken(chapter_id: str) -> Help:
    """Read help for one chapter off this machine. Empty when nothing is recorded.

    A reveal supersedes a hint on the same exercise, so the two counts never
    double-charge one exercise.
    """
    prefix = f"{chapter_id}-"
    attempts = [a for a in all_attempts() if a.exercise.startswith(prefix)]
    revealed = [a for a in attempts if a.revealed]
    hinted = [a for a in attempts if a.hinted and not a.revealed]
    return Help(hinted=len(hinted), revealed=len(revealed))


def _canonical_bytes(payload: dict) -> bytes:
    """One byte-form for a claim, so two machines hash it the same way.

    Sorted keys, no incidental whitespace, UTF-8. The pretty-printed file on
    disk is for people; this is what an id or a signature is taken over.
    """
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def claim_sha256(payload: dict) -> str:
    """The hash of a claim, excluding nothing that is in it."""
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def submission_id_for(payload: dict) -> str:
    """The id a claim gets, derived from the claim itself.

    Taken over the payload WITHOUT its own `submission_id`, so recomputing it is
    how a reader checks that a claim was not edited after it was written. Two
    honest submissions of the same work at the same second collide, and that is
    correct: they are the same claim.
    """
    body = {key: value for key, value in payload.items() if key != "submission_id"}
    return f"sub_{claim_sha256(body)[:24]}"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score_for(passed: tuple[str, ...], help: Help) -> int:
    """Full marks per passing exercise, less whatever help was taken.

    The same arithmetic `review()` prints, so a submission can never disagree
    with the scorecard the learner read in their own notebook.
    """
    return max(len(passed) * FULL_MARKS - help.cost(), 0)


def build(
    item: Submittable | Chapter,
    card: Scorecard | None,
    notebook: Path,
    github: str,
    cohort: str,
    help: Help | None = None,
    now: datetime | None = None,
) -> dict:
    """The submission payload for one chapter or week-0 unit.

    `card` is None for an item that was never run, which is the honest state for
    an assistant-driven chapter: it cannot be re-run unattended, so there are no
    verdicts to report and inventing zeroes would read as failure.
    """
    if isinstance(item, Chapter):  # callers that still hand us a Chapter
        item = resolve(item.chapter_id)
    if not github.strip():
        raise SubmissionError("a submission needs the GitHub username it will be filed under")
    if not notebook.is_file():
        raise SubmissionError(f"no notebook at {notebook}")

    taken = help_taken(item.id) if help is None else help
    stamp = (now or datetime.now(UTC)).replace(microsecond=0)

    payload = {
        "schema": SCHEMA,
        "cohort": cohort,
        "chapter": item.id,
        "student": {"github": github.strip()},
        "submitted_at": stamp.isoformat().replace("+00:00", "Z"),
        "result": {
            "ran": card is not None,
            "passed": list(card.passed) if card else [],
            "failed": [exercise for exercise, _ in card.failed] if card else [],
            "not_reached": list(card.not_reached) if card else list(item.exercises),
            "scored": item.scored,
            "score": score_for(card.passed, taken) if (item.scored and card) else None,
            "max_score": item.max_score,
        },
        "note": item.note,
        "help": taken.as_dict(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.system().lower(),
        },
        "evidence": {"notebook": NOTEBOOK_FILE, "notebook_sha256": sha256_of(notebook)},
        "verified": None,
    }
    # Last, because it is taken over everything above it.
    payload["submission_id"] = submission_id_for(payload)
    return payload


def write(payload: dict, notebook: Path, into: Path) -> Path:
    """Write the bundle a learner commits: the claim and the evidence beside it.

    STAGED, THEN SWAPPED. A submission is a claim and the exact notebook it is
    a claim about, and the pair is the whole point. Writing them one at a time
    means an interrupted run leaves a new claim next to an old notebook, whose
    hashes disagree, and the learner is told their own work is forged. So the
    pair is built in a staging directory and moved into place in one step; if
    anything fails, the previous bundle is still there.

    It also refuses to write through a symlink. A submissions tree is a path a
    learner controls and a verifier walks, and following a link out of it is
    how a bundle escapes its own folder.
    """
    github = str(payload.get("student", {}).get("github", ""))
    item = str(payload.get("chapter", ""))
    if into.name != item or into.parent.name != github:
        raise SubmissionError(
            f"bundle path must end in {github}/{item}, got {into.parent.name}/{into.name}"
        )
    if not notebook.is_file() or notebook.is_symlink():
        raise SubmissionError("the notebook must be a regular file, not a symlink")

    into.parent.mkdir(parents=True, exist_ok=True)
    for parent in (into.parent, *into.parent.parents):
        if parent.is_symlink():
            raise SubmissionError(f"refusing to write through the symlinked directory {parent}")
    if into.exists() and (into.is_symlink() or not into.is_dir()):
        raise SubmissionError(f"the submission target is not a directory: {into}")

    stage = Path(tempfile.mkdtemp(prefix=f".{item}.stage-", dir=into.parent))
    backup = into.parent / f".{item}.previous-{os.getpid()}"
    try:
        (stage / SUBMISSION_FILE).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        (stage / NOTEBOOK_FILE).write_bytes(notebook.read_bytes())
        if into.exists():
            if backup.exists():
                shutil.rmtree(backup)
            os.replace(into, backup)
        try:
            os.replace(stage, into)
        except OSError:
            if backup.exists() and not into.exists():
                os.replace(backup, into)  # put the old bundle back
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return into
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def id_problem(claimed: dict) -> str | None:
    """Why a claim's own id does not match its content, or None.

    A claim written before ids existed carries none, and that is not a problem:
    the id is additive, and refusing an older bundle would invalidate work that
    was honest when it was handed in.
    """
    stated = claimed.get("submission_id")
    if stated is None:
        return None
    if not isinstance(stated, str):
        return f"submission_id must be a string, got {type(stated).__name__}"
    expected = submission_id_for(claimed)
    if stated != expected:
        return (
            f"submission_id is {stated}, but this claim hashes to {expected}. "
            "Re-run `uv run bootcamp submit` rather than editing the file"
        )
    return None


def compare(claimed: dict, observed: Scorecard) -> list[str]:
    """Every way the claim and the re-run disagree. Empty means the claim holds.

    Only `result` is checked, because only `result` is re-runnable. `help` is
    read from a database this process has never seen, and the module docstring
    says why that is acceptable.
    """
    problems: list[str] = []
    result = claimed.get("result", {})

    # The score is the one number a gradebook consumes, and the notebook's hash
    # does not cover it: the claim is a separate file. So it is recomputed here
    # from the claimed passes and the declared help, and the denominator from the
    # chapter's own exercise count. Understating help to inflate a score fails the
    # same check, because the cost is part of the arithmetic.
    try:
        item = resolve(str(claimed.get("chapter", "")))
    except (KeyError, SubmissionError):
        problems.append(
            f"chapter: {claimed.get('chapter')!r} is not something that can be handed in"
        )
        return problems

    if result.get("scored") != item.scored:
        problems.append(
            f"scored: claimed {result.get('scored')}, {item.id} is scored={item.scored}"
        )

    if item.scored:
        declared = Help.from_dict(claimed.get("help"))
        claimed_passed = tuple(result.get("passed", []) or ())
        expected_score = score_for(claimed_passed, declared)
        if result.get("score") != expected_score:
            problems.append(
                f"score: claimed {result.get('score')}, the claim's own passes and help make "
                f"{expected_score}"
            )
        if result.get("max_score") != item.max_score:
            problems.append(
                f"max_score: claimed {result.get('max_score')}, "
                f"{item.id} is out of {item.max_score}"
            )
    else:
        for field in ("score", "max_score"):
            if result.get(field) is not None:
                problems.append(f"{field}: {item.id} is not marked, so it must be null")

    if not result.get("ran", True):
        if item.verifiable:
            problems.append(f"ran: {item.id} can be re-run, so a submission must report verdicts")
        return problems

    observed_by_field = {
        "passed": sorted(observed.passed),
        "failed": sorted(exercise for exercise, _ in observed.failed),
        "not_reached": sorted(observed.not_reached),
    }
    for field, actual in observed_by_field.items():
        claimed_field = sorted(result.get(field, []))
        if claimed_field != actual:
            problems.append(f"{field}: claimed {claimed_field}, the re-run said {actual}")

    return problems
