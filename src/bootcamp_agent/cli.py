"""Thin CLI over the package. Parse args, call the package, format output.

If logic starts creeping in here, it belongs in the package instead.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bootcamp_agent.agent import answer_question
from bootcamp_agent.config import ConfigError, load_settings
from bootcamp_agent.documents import CorpusError, load_corpus
from bootcamp_agent.evals import EvalError, format_report, load_cases, run_evals
from bootcamp_agent.llm import get_client

ROOT = Path(__file__).resolve().parent.parent.parent
CORPUS_DIR = ROOT / "data" / "corpus"
GOLDEN_PATH = ROOT / "data" / "evals" / "golden.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bootcamp-agent",
        description="Source-grounded developer research assistant (bootcamp capstone).",
    )
    parser.add_argument("question", nargs="?", help="Question to answer from the corpus")
    parser.add_argument("--trace", action="store_true", help="Print the agent trace")
    parser.add_argument("--eval", action="store_true", help="Run the golden evaluation set")
    args = parser.parse_args(argv)

    try:
        settings = load_settings()
        client = get_client(settings)
        documents = load_corpus(CORPUS_DIR)
    except (ConfigError, CorpusError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.eval:
        try:
            report = run_evals(load_cases(GOLDEN_PATH), documents, client)
        except EvalError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        print(format_report(report))
        return 0 if report.pass_rate == 1.0 else 1

    if not args.question:
        parser.print_help()
        return 2

    result = answer_question(args.question, documents, client)
    if args.trace:
        for event in result.trace:
            print(f"[{event.kind}] {event.detail}")
        print()
    answer = result.answer
    print(f"answer: {answer.answer}")
    print(f"citations: {list(answer.citations)}")
    print(f"confidence: {answer.confidence}")
    print(f"needs_human_review: {answer.needs_human_review}")
    return 0


def _doctor() -> int:
    """Delegate to the setup doctor. One implementation, two entry points."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from check_setup import main as check_setup_main

    return check_setup_main()


def _check(item_id: str) -> int:
    """Run one item's notebook and print its scorecard.

    Any submittable item, not only a session: a week-0 unit and the capstone
    have notebooks and checks too, and a learner who can submit them should be
    able to run them the same way.
    """
    from bootcamp_agent import submission
    from bootcamp_agent.coursework import CourseworkError, render, run_notebook
    from bootcamp_agent.curriculum import UnknownChapter

    try:
        item = submission.resolve(item_id)
    except (UnknownChapter, submission.SubmissionError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if not item.verifiable:
        print(f"{item.id}: {item.note}")
        print("Run this one in Jupyter and read its review() cell there.")
        return 0
    print(f"running {item.id} ({item.title})…")
    try:
        card = run_notebook(item.notebook, item.exercises, item.id)
    except CourseworkError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(render(card))
    return 0 if not card.failed and not card.not_reached else 1


def _export(destination: Path | None) -> int:
    """Write this machine's progress to a file the learner can read and send.

    The week-0 page promises exactly this, and the promise is load-bearing: the
    course tells learners their progress database never leaves their machine,
    and offers this as the way to share it if they WANT to. An escape hatch that
    does not exist makes the paragraph around it a lie.

    Outcomes only, which is all the store holds: which exercises passed, how
    many attempts, and whether help was taken. Never what was typed.
    """
    import json

    from bootcamp_agent.hints import FULL_MARKS, all_attempts, store_path

    attempts = all_attempts()
    payload = {
        "schema": "dev3pack.progress.v1",
        "source": str(store_path()),
        "note": "Outcomes only. This file records no answers, no name, and no email.",
        "exercises": [
            {
                "exercise": entry.exercise,
                "passed": entry.passed,
                "attempts": entry.attempts,
                "hinted": entry.hinted,
                "revealed": entry.revealed,
                "score": entry.score,
                "out_of": FULL_MARKS,
            }
            for entry in sorted(attempts, key=lambda a: a.exercise)
        ],
    }
    text = json.dumps(payload, indent=2) + "\n"
    if destination is None:
        print(text, end="")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    print(f"wrote {destination} — {len(attempts)} exercise(s), outcomes only")
    print("Read it before you send it anywhere. Nothing here is sent for you.")
    return 0


def _progress() -> int:
    """Run everything that can be run, and tally it in course order.

    Week 0 and the capstone are here beside the sessions, because a learner who
    did week 0 and asks "where am I" is asking about all of it. They are marked
    for what they are: week 0 runs and is never marked, the capstone is scored,
    and an assistant-driven session cannot be run here at all.
    """
    from bootcamp_agent import submission
    from bootcamp_agent.coursework import CourseworkError, run_notebook
    from bootcamp_agent.curriculum import CAPSTONE, CHAPTERS, WEEK0_UNITS

    rows: list[tuple[str, str, str | None]] = []
    for unit in WEEK0_UNITS:
        rows.append((unit.prefix, f"{unit.title[:44]:<44}", "week 0"))
    for chapter in CHAPTERS:
        rows.append((chapter.chapter_id, f"{chapter.title[:44]:<44}", chapter.weekday))
    rows.append((CAPSTONE.prefix, f"{CAPSTONE.title[:44]:<44}", "project"))

    worst = 0
    for item_id, title, when in rows:
        label = f"{item_id:<6} {when or '':<10} {title}"
        try:
            item = submission.resolve(item_id)
        except submission.SubmissionError:
            print(f"{label} demo day")
            continue
        if not item.verifiable:
            print(f"{label} in Jupyter")
            continue
        try:
            card = run_notebook(item.notebook, item.exercises, item.id)
        except CourseworkError as error:
            print(f"{label} error: {str(error)[:40]}")
            worst = 1
            continue
        tally = f"{len(card.passed)}/{card.total}"
        print(f"{label} {tally}{'' if item.scored else '  (not marked)'}")
        if card.failed or card.not_reached:
            worst = 1
    return worst


def _submit(chapter_id: str, github: str, cohort: str, into: str | None) -> int:
    """Build the bundle a learner opens a pull request with."""
    from pathlib import Path

    from bootcamp_agent import submission
    from bootcamp_agent.coursework import CourseworkError, run_notebook

    try:
        item = submission.resolve(chapter_id)
    except (KeyError, submission.SubmissionError) as error:
        print(f"cannot submit that: {error}")
        return 2

    if not item.verifiable:
        # Sessions 1 and 10 need an assistant open — they edit its configuration
        # and author a skill. Running them unattended would score zero for work
        # that was genuinely done, so they are handed in as they stand and said
        # to be, rather than a failure being manufactured. The ids come from
        # `manual_reason` in the curriculum, never from a list written here.
        print(f"{item.id} ({item.title}) — {item.note}")
        print("submitting your notebook as it stands, with no re-run and no marks.")
        card = None
    else:
        print(f"running {item.id} ({item.title})…")
        try:
            card = run_notebook(item.notebook, item.exercises, item.id)
        except CourseworkError as error:
            print(f"could not run it: {error}")
            return 1

    try:
        payload = submission.build(item, card, item.notebook, github, cohort)
    except submission.SubmissionError as error:
        print(str(error))
        return 2

    root = Path(into) if into else Path.cwd() / "submissions"
    where = submission.write(payload, item.notebook, root / github / item.id)

    result = payload["result"]
    if item.scored:
        print(f"\n{item.id}: {len(result['passed'])}/{len(item.exercises)} passed")
        print(f"score {result['score']}/{result['max_score']}")
    elif card is not None:
        print(f"\n{item.id}: {len(result['passed'])}/{len(item.exercises)} passed, not marked")
    if result["failed"] or result["not_reached"]:
        print("\nnot finished yet, and you can submit anyway:")
        for exercise in result["failed"]:
            print(f"  ❌ {exercise}")
        for exercise in result["not_reached"]:
            print(f"  ·  {exercise} never ran")
    print(f"\nwrote {where}")
    print("commit that folder to your fork and open a pull request.")
    return 0


def bootcamp(argv: list[str] | None = None) -> int:
    """The participant's own command: check the setup, a chapter, or everything."""
    parser = argparse.ArgumentParser(
        prog="bootcamp",
        description="Check your setup and your chapter exercises.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("doctor", help="check this machine: Python, kernel, corpus, provider lane")
    checker = sub.add_parser("check", help="run one item's notebook and print its scorecard")
    checker.add_argument(
        "chapter", help="a session (ch03), a week-0 unit (w05), or the capstone (cap01)"
    )
    progress = sub.add_parser("progress", help="run every runnable chapter and tally the checks")
    progress.add_argument(
        "--export",
        nargs="?",
        const="-",
        metavar="FILE",
        help="write your own progress (outcomes only) to a file instead of running anything",
    )
    submitter = sub.add_parser("submit", help="build the submission bundle to hand in")
    submitter.add_argument(
        "chapter", help="a session (ch03), a week-0 unit (w05), or the capstone (cap01)"
    )
    submitter.add_argument("--github", required=True, help="your GitHub username")
    submitter.add_argument("--cohort", default="2026-09", help="which cohort (default 2026-09)")
    submitter.add_argument("--into", help="submissions root (default ./submissions)")
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return _doctor()
    if args.command == "check":
        return _check(args.chapter)
    if args.command == "progress":
        if getattr(args, "export", None):
            return _export(None if args.export == "-" else Path(args.export))
        return _progress()
    if args.command == "submit":
        return _submit(args.chapter, args.github, args.cohort, args.into)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
