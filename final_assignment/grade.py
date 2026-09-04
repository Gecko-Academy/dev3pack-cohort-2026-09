"""Grade YourAgent against a question set and write score_report.json.

Usage:
    uv run python final_assignment/grade.py --name "Your Name"
    uv run python final_assignment/grade.py --questions private.jsonl --name "..."  # instructor

Pass logic is identical to the course evals (bootcamp_agent/evals.py):
grounded questions need every expected doc id cited and no human-review flag;
refusal questions need the flag and zero citations. Pass bar: 70%.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
_ROOT = HERE if (HERE / "src" / "bootcamp_agent").is_dir() else HERE.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(HERE))

from bootcamp_agent.evals import EvalCase  # noqa: E402

PASS_THRESHOLD = 0.70
DEFAULT_QUESTIONS = HERE / "questions.jsonl"
DEFAULT_REPORT = HERE / "score_report.json"


@dataclass(frozen=True)
class QuestionResult:
    task_id: str
    question: str
    passed: bool
    detail: str


def load_questions(path: Path) -> list[tuple[str, EvalCase]]:
    if not path.is_file():
        raise SystemExit(f"error: question set not found: {path}")
    entries: list[tuple[str, EvalCase]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            case = EvalCase(
                question=payload["question"],
                expected_doc_ids=tuple(payload["expected_doc_ids"]),
                expect_refusal=bool(payload["expect_refusal"]),
            )
            entries.append((payload.get("task_id", f"q-{line_number}"), case))
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise SystemExit(
                f"error: {path.name}:{line_number}: malformed question ({error})"
            ) from error
    return entries


def grade(agent, entries: list[tuple[str, EvalCase]]) -> list[QuestionResult]:
    results: list[QuestionResult] = []
    for task_id, case in entries:
        try:
            answer = agent(case.question)
        except Exception as error:  # noqa: BLE001 - a crashing agent scores the question 0
            results.append(
                QuestionResult(
                    task_id, case.question, False, f"agent raised {type(error).__name__}: {error}"
                )
            )
            continue
        if case.expect_refusal:
            passed = answer.needs_human_review and not answer.citations
            detail = (
                "refused as expected"
                if passed
                else f"expected refusal, cited {list(answer.citations)}"
            )
        else:
            missing = [d for d in case.expected_doc_ids if d not in answer.citations]
            passed = not missing and not answer.needs_human_review
            detail = (
                f"cited {list(answer.citations)}"
                if passed
                else f"missing {missing}; needs_human_review={answer.needs_human_review}"
            )
        results.append(QuestionResult(task_id, case.question, passed, detail))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grade the final assignment.")
    parser.add_argument("--name", default="", help="Student name (goes into the report)")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)

    from agent import YourAgent  # imported late so a broken agent fails HERE, visibly

    entries = load_questions(args.questions)
    results = grade(YourAgent(), entries)

    passed = sum(r.passed for r in results)
    score = passed / len(results) if results else 0.0

    width = max(len(r.task_id) for r in results)
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        print(f"{mark}  {r.task_id:<{width}}  {r.question[:56]:<56}  {r.detail[:60]}")
    verdict = "PASSED" if score >= PASS_THRESHOLD else "NOT YET"
    bar = f"pass bar {PASS_THRESHOLD:.0%}"
    print(f"\nscore: {passed}/{len(results)} ({score:.0%}) — {bar} — {verdict}")

    report = {
        "name": args.name,
        "date": date.today().isoformat(),
        "question_set": args.questions.name,
        "score_percent": round(score * 100),
        "passed": score >= PASS_THRESHOLD,
        "results": [asdict(r) for r in results],
    }
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"report written: {args.report}")
    return 0 if score >= PASS_THRESHOLD else 1


if __name__ == "__main__":
    raise SystemExit(main())
