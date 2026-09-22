"""The final run: the student's agent on every final question, never a crash.

Each question gets a per-question timeout inside a total budget. An agent that
raises, hangs or returns the wrong shape gets a flagged refusal for that
question, in the shape the agent's own `_refusal()` returns, and the run goes
on. One bad question must not cost the other answers.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from bootcamp_agent.agent import REFUSAL_TEXT
from bootcamp_agent.questions_api import Question
from bootcamp_agent.schema import ResearchAnswer

#: The app refuses more than this. Refusing here says which question, and
#: costs nothing; the app refusing costs a pull request and a wait.
MAX_ANSWER_CHARS = 8000
MAX_CITATIONS = 40

DEFAULT_QUESTION_TIMEOUT_S = 120.0
DEFAULT_BUDGET_S = 1800.0

Say = Callable[[str], None]


class CapError(Exception):
    """An answer is larger than the app accepts. Safe to show as is."""


def _flagged_refusal() -> ResearchAnswer:
    # The same shape the agent's own `_refusal()` returns, so a timeout scores
    # exactly like a refusal the agent chose.
    return ResearchAnswer(
        answer=REFUSAL_TEXT, citations=(), confidence=0.0, needs_human_review=True
    )


def _well_formed(answer: object) -> str:
    """Why `answer` cannot be submitted as a ResearchAnswer, or "" when it can."""
    if not isinstance(answer, ResearchAnswer):
        return f"returned {type(answer).__name__}, not a ResearchAnswer"
    if not isinstance(answer.answer, str):
        return "answer is not a string"
    if not all(isinstance(citation, str) for citation in answer.citations):
        return "a citation is not a string"
    confidence = answer.confidence
    if isinstance(confidence, bool) or not isinstance(confidence, int | float):
        return "confidence is not a number"
    if not 0.0 <= float(confidence) <= 1.0:
        return "confidence is outside 0..1"
    if type(answer.needs_human_review) is not bool:
        return "needs_human_review is not true or false"
    return ""


def _ask(agent: Callable[[str], object], question: str, timeout: float) -> tuple[object, str]:
    """(the agent's reply, "") or (None, why it has none).

    A daemon thread, because a hung provider call cannot be interrupted from
    outside: the run moves on and the thread dies with the process.
    """
    box: dict[str, object] = {}

    def work() -> None:
        try:
            box["answer"] = agent(question)
        except Exception as error:  # noqa: BLE001 - any failure is this question's refusal
            box["error"] = error

    worker = threading.Thread(target=work, daemon=True)
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        return None, f"timed out after {timeout:.0f}s"
    if "error" in box:
        error = box["error"]
        return None, f"raised {type(error).__name__}: {str(error)[:120]}"
    return box.get("answer"), ""


@dataclass
class FinalRun:
    answers: dict[str, ResearchAnswer] = field(default_factory=dict)
    flagged: dict[str, str] = field(default_factory=dict)


def answer_all(
    agent: Callable[[str], object],
    questions: Sequence[Question],
    *,
    question_timeout_s: float = DEFAULT_QUESTION_TIMEOUT_S,
    budget_s: float = DEFAULT_BUDGET_S,
    say: Say = print,
    clock: Callable[[], float] = time.monotonic,
) -> FinalRun:
    run = FinalRun()
    started = clock()
    width = len(str(len(questions)))
    for index, item in enumerate(questions, start=1):
        remaining = budget_s - (clock() - started)
        if remaining <= 0:
            reply, problem = None, "the total budget was spent before this question"
        else:
            reply, problem = _ask(agent, item.question, min(question_timeout_s, remaining))
        if not problem:
            problem = _well_formed(reply)
        if problem or not isinstance(reply, ResearchAnswer):
            run.answers[item.task_id] = _flagged_refusal()
            run.flagged[item.task_id] = problem
            outcome = f"flagged refusal ({problem})"
        else:
            run.answers[item.task_id] = reply
            outcome = "refused" if reply.needs_human_review else "answered"
        say(f"[{index:>{width}}/{len(questions)}] {item.task_id}: {outcome}")
    return run


def check_caps(answers: dict[str, ResearchAnswer]) -> None:
    """Refuse locally what the app would refuse: over-long answers, too many citations."""
    over = [
        f"    {task_id}: {len(answer.answer)} characters (the cap is {MAX_ANSWER_CHARS})"
        for task_id, answer in answers.items()
        if len(answer.answer) > MAX_ANSWER_CHARS
    ] + [
        f"    {task_id}: {len(answer.citations)} citations (the cap is {MAX_CITATIONS})"
        for task_id, answer in answers.items()
        if len(answer.citations) > MAX_CITATIONS
    ]
    if over:
        raise CapError(
            "some answers are larger than the app accepts, so nothing was handed in:\n"
            + "\n".join(over)
            + "\nShorten them in your agent, commit, push, and submit again."
        )
