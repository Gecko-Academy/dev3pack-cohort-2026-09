"""Grade the capstone with deterministic support, citation, refusal, and safety gates.

Public practice:
    uv run python final_assignment/grade.py --name "Your Name"

An agent that lives in another file (your capstone repository, for one):
    uv run python final_assignment/grade.py --agent ../my-capstone/agent.py

Instructor transfer set:
    uv run python final_assignment/grade.py --mode private \
      --questions private.jsonl --question-set-id cohort-2026-private-1 --name "..."

A score report is evidence about a run, not a credential.  New credentials require
a signed private receipt produced by ``final_assignment/receipt.py``.

The scoring itself lives in the package (`bootcamp_agent.final_grade`), so a
capstone repository outside the course grades with the same code
(`bootcamp capstone grade`). This file is the course checkout's front door: it
decides which agent is graded and which files the report hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_ROOT = HERE if (HERE / "src" / "bootcamp_agent").is_dir() else HERE.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(HERE))

from bootcamp_agent import final_grade  # noqa: E402
from bootcamp_agent.final_grade import (  # noqa: E402, F401 - the names callers import from here
    CASE_SCHEMA,
    GRADER_VERSION,
    PASS_THRESHOLD,
    REPORT_SCHEMA,
    AgentLoadError,
    FinalCase,
    QuestionResult,
    evaluate_answer,
    grade,
    load_questions,
    sample,
)

DEFAULT_QUESTIONS = final_grade.PRACTICE_QUESTIONS
DEFAULT_REPORT = HERE / "score_report.json"


def _sha256(path: Path) -> str:
    return final_grade.sha256_file(path)


def _tree_hash(paths: list[Path]) -> str:
    return final_grade.tree_hash(paths, _ROOT)


def _grader_source_sha256() -> str:
    """This front door and the scoring it calls, as one hash."""
    digest = hashlib.sha256()
    for path in (Path(__file__), Path(final_grade.__file__)):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def build_report(
    *,
    name: str,
    mode: str,
    question_set_id: str,
    question_path: Path,
    results: list[QuestionResult],
    agent_path: Path | None = None,
) -> dict:
    agent_file = agent_path if agent_path is not None else HERE / "agent.py"
    return final_grade.assemble_report(
        name=name,
        mode=mode,
        question_set_id=question_set_id,
        question_sha256=_sha256(question_path),
        results=results,
        grader_source_sha256=_grader_source_sha256(),
        artifacts={
            "agent_tree_sha256": _tree_hash([agent_file, _ROOT / "src", _ROOT / "data" / "corpus"]),
            # The generated contract: the table of contents and the index that
            # every count is computed into. Two files rather than a manifest,
            # because those are the files this course actually generates.
            "course_contract_sha256": _tree_hash(
                [_ROOT / "units" / "en" / "_toctree.yml", _ROOT / "docs" / "course-index.md"]
            ),
            "dependencies_lock_sha256": _sha256(_ROOT / "uv.lock"),
        },
    )


def load_agent(spec: str | None) -> tuple[type, Path]:
    """The agent class to grade and the file it came from.

    `None` is the default: `YourAgent` from `agent.py` beside this grader.
    Otherwise `FILE` or `FILE:CLASS`, loaded by path.
    """
    if spec is None:
        from agent import YourAgent  # imported late so a broken agent fails visibly

        return YourAgent, HERE / "agent.py"
    path, class_name = final_grade.parse_agent_spec(spec)
    try:
        return final_grade.load_agent_class(path, class_name), path.resolve()
    except AgentLoadError as error:
        raise SystemExit(f"error: --agent: {error}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="", help="student display name")
    parser.add_argument("--mode", choices=("practice", "private"), default="practice")
    parser.add_argument("--question-set-id", default="public-practice-v2")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--random",
        type=int,
        default=0,
        metavar="N",
        help="grade a random N-question sample, keeping the category mix (practice only)",
    )
    parser.add_argument("--seed", type=int, default=None, help="make --random repeatable")
    parser.add_argument(
        "--agent",
        default=None,
        metavar="FILE[:CLASS]",
        help="grade the agent in another file (default: YourAgent in agent.py beside this)",
    )
    args = parser.parse_args(argv)
    if args.random and args.mode != "practice":
        parser.error("--random is for practice; the private set is graded whole")

    agent_class, agent_path = load_agent(args.agent)

    entries = load_questions(args.questions)
    if args.random:
        entries = sample(entries, args.random, args.seed)
        print(f"practising on {len(entries)} of the set, sampled by category\n")
    results = grade(agent_class(), entries)
    report = build_report(
        name=args.name,
        mode=args.mode,
        question_set_id=args.question_set_id,
        question_path=args.questions,
        results=results,
        agent_path=agent_path,
    )

    for line in final_grade.format_results(results, report):
        print(line)

    final_grade.write_report(report, args.report)
    print(f"report written: {args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
