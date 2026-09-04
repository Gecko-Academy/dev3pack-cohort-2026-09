"""The evaluation harness: a golden set, a pass condition, one command.

Pass logic is code-based on purpose (see data/corpus/evaluation-basics.md):
- refusal cases pass iff the agent flagged human review AND cited nothing;
- grounded cases pass iff every expected doc_id appears in the citations.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from bootcamp_agent.agent import answer_question
from bootcamp_agent.documents import Document
from bootcamp_agent.llm import LLMClient


class EvalError(Exception):
    """Raised when the golden set file is missing or malformed."""


@dataclass(frozen=True)
class EvalCase:
    question: str
    expected_doc_ids: tuple[str, ...]
    expect_refusal: bool


@dataclass(frozen=True)
class EvalOutcome:
    case: EvalCase
    passed: bool
    reason: str


@dataclass(frozen=True)
class EvalReport:
    outcomes: tuple[EvalOutcome, ...]

    @property
    def pass_rate(self) -> float:
        if not self.outcomes:
            return 0.0
        return sum(outcome.passed for outcome in self.outcomes) / len(self.outcomes)


def load_cases(path: Path) -> list[EvalCase]:
    if not path.is_file():
        raise EvalError(f"Golden set not found: {path}")
    cases: list[EvalCase] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            cases.append(
                EvalCase(
                    question=payload["question"],
                    expected_doc_ids=tuple(payload["expected_doc_ids"]),
                    expect_refusal=bool(payload["expect_refusal"]),
                )
            )
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise EvalError(f"{path.name}:{line_number}: malformed case ({error})") from error
    return cases


def run_evals(
    cases: Sequence[EvalCase], documents: Sequence[Document], client: LLMClient
) -> EvalReport:
    outcomes: list[EvalOutcome] = []
    for case in cases:
        result = answer_question(case.question, documents, client)
        answer = result.answer
        if case.expect_refusal:
            passed = answer.needs_human_review and not answer.citations
            reason = (
                "refused as expected"
                if passed
                else f"expected refusal, got citations={list(answer.citations)}"
            )
        else:
            missing = [d for d in case.expected_doc_ids if d not in answer.citations]
            passed = not missing and not answer.needs_human_review
            reason = (
                f"cited {list(answer.citations)}"
                if passed
                else f"missing citations {missing}; needs_human_review={answer.needs_human_review}"
            )
        outcomes.append(EvalOutcome(case=case, passed=passed, reason=reason))
    return EvalReport(outcomes=tuple(outcomes))


def format_report(report: EvalReport) -> str:
    lines = [
        "| # | Question | Result | Detail |",
        "|---|---|---|---|",
    ]
    for index, outcome in enumerate(report.outcomes, start=1):
        status = "PASS" if outcome.passed else "FAIL"
        question = outcome.case.question[:60]
        lines.append(f"| {index} | {question} | {status} | {outcome.reason} |")
    passed = sum(o.passed for o in report.outcomes)
    lines.append(f"\n**{passed}/{len(report.outcomes)} passed** (pass rate {report.pass_rate:.0%})")
    return "\n".join(lines)
