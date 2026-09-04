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


def _check(chapter_id: str) -> int:
    from bootcamp_agent.coursework import CourseworkError, render, run_chapter
    from bootcamp_agent.curriculum import UnknownChapter, get_chapter

    try:
        chapter = get_chapter(chapter_id)
    except UnknownChapter as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if chapter.manual_reason:
        print(f"{chapter.chapter_id}: {chapter.manual_reason}")
        print("Run this one in Jupyter and read its review() cell there.")
        return 0
    print(f"running {chapter.chapter_id} ({chapter.title})…")
    try:
        card = run_chapter(chapter)
    except CourseworkError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(render(card))
    return 0 if not card.failed and not card.not_reached else 1


def _progress() -> int:
    from bootcamp_agent.coursework import CourseworkError, run_chapter
    from bootcamp_agent.curriculum import CHAPTERS

    worst = 0
    for chapter in CHAPTERS:
        label = f"{chapter.chapter_id}  {chapter.weekday}  {chapter.title[:44]:<44}"
        if not chapter.has_notebook:
            print(f"{label} demo day")
            continue
        if chapter.manual_reason:
            print(f"{label} in Jupyter")
            continue
        try:
            card = run_chapter(chapter)
        except CourseworkError as error:
            print(f"{label} error: {str(error)[:40]}")
            worst = 1
            continue
        print(f"{label} {len(card.passed)}/{card.total}")
        if card.failed or card.not_reached:
            worst = 1
    return worst


def bootcamp(argv: list[str] | None = None) -> int:
    """The participant's own command: check the setup, a chapter, or everything."""
    parser = argparse.ArgumentParser(
        prog="bootcamp",
        description="Check your setup and your chapter exercises.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("doctor", help="check this machine: Python, kernel, corpus, provider lane")
    checker = sub.add_parser("check", help="run one chapter's notebook and print its scorecard")
    checker.add_argument("chapter", help="a chapter id: ch03, 3 or 03")
    sub.add_parser("progress", help="run every runnable chapter and tally the checks")
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return _doctor()
    if args.command == "check":
        return _check(args.chapter)
    if args.command == "progress":
        return _progress()
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
