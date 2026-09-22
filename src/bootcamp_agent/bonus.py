"""The tier above the floor: optional exercises that no denominator can see.

    from bootcamp_agent.bonus import bonus
    bonus("ch02", answer_with_timeout)

WHY A SEPARATE REGISTRY AND NOT `chNN-e9`. `curriculum.exercise_ids` collects
every key in `CHECKS` starting with the session's prefix, so an extra id there
would silently raise ch02 from 400 marks to 500 and make every finished
submission read as incomplete. Uncounted has to be true by CONSTRUCTION, not by
remembering to special-case it -- so these live in their own dict, which nothing
that computes a total ever reads.

WHAT MAKES A GOOD ONE. Every session already ships running and passing: that is
the floor, and it is deliberately reachable by everybody. A bonus is the part
that cannot be reached by running the cell you were given. It must be judged by
BEHAVIOUR rather than by prose, so that "I improved it" is decided by the code
and not by how confidently it was claimed.

AND IT SHIPS FAILING, on purpose. A bonus cell that passes as handed over has
nothing to demonstrate and nothing to earn.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

Checker = Callable[[Any], str | None]

#: id -> checker. Deliberately NOT `checks.CHECKS`.
BONUS: dict[str, Checker] = {}

OK = "\N{WHITE HEAVY CHECK MARK}"
NO = "\N{CROSS MARK}"
#: Not a failure: the cell is still the one that was shipped.
NOT_YET = "\N{MIDDLE DOT}"


def register(exercise_id: str) -> Callable[[Checker], Checker]:
    def wrap(function: Checker) -> Checker:
        BONUS[exercise_id] = function
        return function

    return wrap


class UnknownBonus(Exception):
    """No bonus exercise is registered under that id."""


class NotAttempted(Exception):
    """The learner's cell is still as shipped: nothing to score, and nothing wrong.

    A session notebook ships its weekly-challenge cell unwritten, and it runs in CI.
    Reporting that as a failure (a red cross on every clean clone) would teach
    people to ignore the cross. `NotImplementedError` from the learner's stub means
    the same thing, so it is read the same way.
    """


def bonus(exercise_id: str, value: Any) -> bool:
    """Run the bonus checker, print the verdict, return whether it passed."""
    if exercise_id not in BONUS:
        raise UnknownBonus(f"no bonus registered for {exercise_id!r}; known: {sorted(BONUS)}")
    try:
        problem = BONUS[exercise_id](value)
    except (NotAttempted, NotImplementedError) as error:
        print(f"{NOT_YET} bonus {exercise_id}: not attempted yet. {error}")
        return False
    except Exception as error:  # a bonus must never take the notebook down with it
        problem = f"it raised {type(error).__name__}: {error}"
    if problem:
        print(f"{NO} bonus {exercise_id}: {problem}")
        return False
    print(f"{OK} bonus {exercise_id} passed — above the floor.")
    return True


@register("ch02")
def _ch02(answer_with_timeout: object) -> str | None:
    """A refusal you can debug: it says which lane, and how long it waited.

    `ch02-e4` already requires the timeout to leave as a flagged refusal rather
    than an exception. That is the floor, and it produces a refusal nobody can
    act on: a call that died instantly and one that died after thirty seconds
    are the same two lines.

    This asks for the two facts that tell those apart, and it asks for them in
    the TRACE -- never in the answer, which still must not claim a cause it
    cannot know.
    """
    from bootcamp_agent.agent import AgentResult
    from bootcamp_agent.schema import ResearchAnswer

    if not callable(answer_with_timeout):
        return "pass the answer_with_timeout function itself, not a call to it"

    started = time.monotonic()
    result = answer_with_timeout("How does chunking work in RAG?")
    if not isinstance(result, AgentResult):
        return "return an AgentResult, exactly as ch02-e4 requires"
    answer = result.answer
    if not isinstance(answer, ResearchAnswer):
        return "the answer must still be a ResearchAnswer"

    # Everything ch02-e4 won must stay won.
    if not answer.needs_human_review:
        return "you lost the floor: a timeout still sets needs_human_review"
    if answer.citations:
        return "you lost the floor: a timeout still cites nothing"

    trace = getattr(result, "trace", ())
    if not trace:
        return "the trace is empty; the two facts below belong in it"
    joined = " ".join(f"{getattr(e, 'kind', '')} {getattr(e, 'detail', '')}" for e in trace)

    lanes = ("fake", "ollama", "anthropic", "openai", "timeoutllm", "timeout_llm")
    if not any(lane in joined.lower() for lane in lanes):
        return (
            "the trace does not say WHICH lane failed. Name the provider in a "
            "TraceEvent detail, so a reader knows where to look"
        )

    import re

    numbers = [float(n) for n in re.findall(r"\d+\.\d+|\d+", joined)]
    elapsed = time.monotonic() - started
    plausible = [n for n in numbers if 0 <= n <= max(elapsed * 1000 + 1000, 60_000)]
    if not plausible:
        return (
            "the trace carries no duration. Measure the wait with time.monotonic() "
            "and put it in the trace — a call that died instantly and one that died "
            "after thirty seconds are not the same incident"
        )

    if any(word in str(answer.answer).lower() for word in ("timeout", "timed out", "too slow")):
        return (
            "the ANSWER names a cause the adapter cannot know: 'too slow' and "
            "'no server' are indistinguishable here. Keep the cause in the trace"
        )
    return None


__all__ = ["BONUS", "NotAttempted", "UnknownBonus", "bonus", "register"]
