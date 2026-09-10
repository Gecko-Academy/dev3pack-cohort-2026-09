"""Run every submittable item from its solutions notebook, and hand each one in.

    uv run python scripts/submit_all.py --github <you>            # dry run
    uv run python scripts/submit_all.py --github <you> --write    # write the bundles

THE RELEASE CHECK, not a learner tool. It answers one question a cohort makes
expensive to get wrong: does every unit of this course actually run, score, and
submit? Twenty-seven items is too many to check by hand and exactly the number
at which one broken notebook hides until a learner finds it.

WHY IT SUBMITS FROM THE SOLUTIONS NOTEBOOK. A learner's exercise notebook is
unsolved by design, so submitting it proves only that a zero can be submitted.
The solutions notebook is the one that must score full marks, and CI already
runs it in strict mode. Here it is submitted as EVIDENCE, which is the same
path a learner's finished notebook takes.

WHAT IT REFUSES TO PRETEND. An item that cannot be re-run — an assistant-driven
session — is handed in without a score, exactly as a learner hands it in, and
this reports it as such rather than inventing a result. Demo day has no
notebook and is skipped, which is a property of the session and not a gap.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bootcamp_agent import submission  # noqa: E402
from bootcamp_agent.coursework import CourseworkError, run_notebook  # noqa: E402
from bootcamp_agent.curriculum import CAPSTONE, CHAPTERS, WEEK0_UNITS  # noqa: E402


@dataclass
class Outcome:
    item: str
    title: str
    status: str
    detail: str


def every_item() -> list[str]:
    """Every id that can be handed in, in course order."""
    ids = [unit.prefix for unit in WEEK0_UNITS]
    ids += [chapter.chapter_id for chapter in CHAPTERS if chapter.has_notebook]
    ids.append(CAPSTONE.prefix)
    return ids


def run_one(item_id: str, github: str, cohort: str, into: Path | None) -> Outcome:
    """Score one item from its solutions notebook and, when asked, write the bundle."""
    item = submission.resolve(item_id)

    if not item.verifiable:
        # Cannot be re-run at all: handed in with no result, the way a learner
        # hands it in. Inventing zeroes here would read as failure.
        payload = submission.build(item, None, item.notebook, github=github, cohort=cohort)
        if into:
            submission.write(payload, item.notebook, into / github / item.id)
        return Outcome(item.id, item.title, "handed in", item.note)

    solutions = item.notebook.parent / "solutions" / "notebook.ipynb"
    if not solutions.is_file():
        return Outcome(item.id, item.title, "NO SOLUTIONS", f"expected {solutions}")

    # Run the solutions notebook AT the item's own path, because a notebook
    # resolves its fixtures relative to the course. The original is restored
    # whatever happens, so one run cannot poison the next.
    original = item.notebook.read_bytes()
    try:
        shutil.copyfile(solutions, item.notebook)
        card = run_notebook(item.notebook, item.exercises, item.id, timeout=300)
        evidence = Path(tempfile.mkdtemp()) / "notebook.ipynb"
        shutil.copyfile(item.notebook, evidence)
    except CourseworkError as error:
        return Outcome(item.id, item.title, "DID NOT RUN", str(error)[:120])
    finally:
        item.notebook.write_bytes(original)

    if card.failed or card.not_reached:
        missing = [exercise for exercise, _ in card.failed] + list(card.not_reached)
        return Outcome(item.id, item.title, "INCOMPLETE", f"{card.headline}; {', '.join(missing)}")

    payload = submission.build(item, card, evidence, github=github, cohort=cohort)
    if into:
        submission.write(payload, evidence, into / github / item.id)
    result = payload["result"]
    if not item.scored:
        # Week 0 runs and passes; it is simply never marked. Printing a score of
        # None here would look like a defect rather than the decision it is.
        return Outcome(item.id, item.title, "unmarked", f"{card.headline}, not marked")
    return Outcome(item.id, item.title, "scored", f"{result['score']}/{result['max_score']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github", required=True, help="the GitHub login to file under")
    parser.add_argument("--cohort", default="2026-09")
    parser.add_argument("--only", nargs="+", help="just these ids, e.g. ch03 w05 cap01")
    parser.add_argument(
        "--into", type=Path, help="submissions root (default ./submissions); needs --write"
    )
    parser.add_argument("--write", action="store_true", help="write the bundles; otherwise dry run")
    args = parser.parse_args(argv)

    into = (args.into or ROOT / "submissions") if args.write else None
    wanted = args.only or every_item()

    print(f"{len(wanted)} item(s), from their solutions notebooks\n")
    outcomes = [run_one(item_id, args.github, args.cohort, into) for item_id in wanted]

    width = max(len(outcome.item) for outcome in outcomes)
    for outcome in outcomes:
        print(f"  {outcome.item:<{width}}  {outcome.status:<12}  {outcome.detail}")

    bad = [outcome for outcome in outcomes if outcome.status.isupper()]
    counted = {status: 0 for status in ("scored", "unmarked", "handed in")}
    for outcome in outcomes:
        if outcome.status in counted:
            counted[outcome.status] += 1
    print(
        f"\n{counted['scored']} scored, {counted['unmarked']} ran but unmarked, "
        f"{counted['handed in']} handed in, {len(bad)} problem(s)"
    )
    if into:
        print(f"bundles written under {into}")
    if bad:
        print("\nEvery problem above is a unit a learner would meet.", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
