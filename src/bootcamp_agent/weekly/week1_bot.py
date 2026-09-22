"""Week 1's challenge: a bot that refuses well, scored out of 500.

    from bootcamp_agent.weekly import week1_bot   # registers the check
    from bootcamp_agent.bonus import bonus
    bonus("week1-bot", respond)

FIVE TIERS OF 100, AND 100 IS THE FLOOR. The floor is "the four exits work and a
person can see which one they got". Everything above it is a thing a real bot
needs and a toy does not: a tool of your own that can refuse, the receipt visible
to the reader, the budget that recovers, and your own loop from `ch05-e2` behind
it. A learner who stops at 100 has finished the week; the other 400 is where the
bot becomes theirs.

WHERE THE SCORE GOES. It lives in `bonus.BONUS`, not `checks.CHECKS`, so session
5's two exercises stay two exercises. The score it prints is added to the ch05
row instead: the learner writes the bot at the end of the session notebook, and
the track reads the `week 1 challenge: S/500` line below out of the saved outputs
(see `bootcamp_agent.weekly`). That line is a contract; do not reword it.

WHAT IT JUDGES. One function:

    respond(text: str, chat: dict) -> dict     # {"stopped_because", "reply", ...}

It never asks where the messages came from. Telegram, a terminal, a web form or a
test are all the same to it, and requiring a bot token would price the challenge
behind an account.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..bonus import register

#: The vocabulary session 5 defines. A fifth word is a different exercise.
STOP_REASONS = ("answered", "budget", "repeated_call", "tool_error")

#: The questions asked when a bot does not say what it answers. Deliberately
#: about this course, because that is the one subject every learner's bot could
#: plausibly share -- but a bot about expenses, or reviews, or anything else says
#: so instead:
#:
#:     respond.examples = ["how much for meals", "convert 900 BRL to EUR"]
#:     respond.broken = "/page does-not-exist"
#:
#: WHY IT IS ASKED RATHER THAN GUESSED. The first version of this check hardcoded
#: course questions and then judged an expenses bot for not knowing them: it
#: scored 0 for answering exactly as designed. A check that assumes the domain
#: judges the wrong thing.
DEFAULT_EXAMPLES = (
    "what is a bounded tool",
    "what stops an agent looping forever",
    "how do I hand in my work",
    "what is a receipt",
)

#: A message that must end in a tool refusing, when the bot does not name its own.
DEFAULT_BROKEN = "/page this-page-does-not-exist"

#: The tiers, in the order they are earned. Each is worth 100.
TIERS = (
    ("the four exits", "every exit is reachable from outside, and each one says why"),
    ("a tool of your own", "something that can refuse, and whose refusal reaches the reader"),
    ("the receipt is visible", "the reader can see which exit they got, without asking"),
    ("the budget recovers", "it refuses, and it says when to come back — then it does"),
    ("your own loop", "`run_loop` from ch05-e2 is behind it, walking a plan"),
)

FULL_MARKS = 100 * len(TIERS)


def _call(respond: Callable[..., Any], text: str, chat: dict) -> dict:
    answer = respond(text, chat)
    if not isinstance(answer, dict):
        raise TypeError(f"respond() returned {type(answer).__name__}, not a dict")
    return answer


def examples_of(respond: Callable[..., Any]) -> tuple[str, ...]:
    """The questions this bot says it can answer, or the course ones."""
    declared = getattr(respond, "examples", None)
    questions = tuple(str(q) for q in declared) if declared else DEFAULT_EXAMPLES
    return questions or DEFAULT_EXAMPLES


def broken_of(respond: Callable[..., Any]) -> str:
    """A message this bot says must fail inside a tool."""
    return str(getattr(respond, "broken", "") or DEFAULT_BROKEN)


def _conversation(respond: Callable[..., Any]) -> tuple[dict[str, dict], list[Any]]:
    """The same question twice, then enough more to spend any budget.

    Invalid stop words are collected rather than ignored: "it answered with a word
    nobody defined" is a better thing to be told than "it never answered".
    """
    questions = examples_of(respond)
    script = [questions[0], questions[0], *(questions * 4)[:10]]
    chat: dict = {"calls": 0}
    seen: dict[str, dict] = {}
    invalid: list[Any] = []
    for text in script:
        answer = _call(respond, text, chat)
        stop = answer.get("stopped_because")
        if stop in STOP_REASONS:
            seen.setdefault(str(stop), answer)
        elif stop not in invalid:
            invalid.append(stop)
    return seen, invalid


def _tier_one(respond: Callable[..., Any], seen: dict[str, dict], invalid: list[Any]) -> str | None:
    """The floor: the exits exist, they are reachable, and each one says why."""
    if invalid:
        return (
            f"stopped_because was {invalid[0]!r}; it must be one of {list(STOP_REASONS)} — "
            "the four words session 5 defines"
        )
    for stop, answer in seen.items():
        reply = str(answer.get("reply", "")).strip()
        if not reply:
            return f"the {stop!r} reply was empty; somebody is reading this"
        if stop != "answered" and len(reply.split()) < 4:
            return (
                f"the {stop!r} reply is {reply!r}. A refusal is written for a reader: "
                "say what happened and what they can do"
            )
    missing = [reason for reason in ("answered", "repeated_call", "budget") if reason not in seen]
    if missing:
        return (
            f"this conversation never reached {missing}. Twelve messages went in: the same "
            "question twice, then ten more. A repeat must not spend a call, and a budget "
            "must refuse before one. If your bot answers about something else, say so: "
            "`respond.examples = ['a question it can answer', ...]`"
        )
    if seen["answered"].get("reply") == seen["repeated_call"].get("reply"):
        return "the repeat answered again instead of refusing: the same reply came back twice"

    asked = broken_of(respond)
    broken = _call(respond, asked, {"calls": 0})
    if broken.get("stopped_because") != "tool_error":
        return (
            f"{asked!r} must end in 'tool_error'. Catch the tool's error and put its own "
            "words in the reply — or set `respond.broken` to a message that does"
        )
    return None


def _tier_two(respond: Callable[..., Any]) -> bool:
    """A tool of your own: something refuses by its own rule, and says so in its own words."""
    refusals = set()
    for probe in (broken_of(respond), "/tool nothing-like-this", "convert 10 XXX to YYY"):
        try:
            answer = _call(respond, probe, {"calls": 0})
        except Exception:  # noqa: BLE001 - a tool that raises has not been caught yet
            return False
        if answer.get("stopped_because") == "tool_error":
            refusals.add(str(answer.get("reply", ""))[:200])
    return len(refusals) >= 2


def _tier_three(seen: dict[str, dict]) -> bool:
    """The receipt reaches the reader: the reply itself says which exit this was."""
    for stop, answer in seen.items():
        if stop == "answered":
            continue
        reply = str(answer.get("reply", "")).lower()
        if stop.replace("_", " ") in reply or stop in reply or "stopped" in reply:
            return True
    return False


def _tier_four(respond: Callable[..., Any]) -> bool:
    """The budget recovers: it refuses, says when, and a later window works again."""
    chat: dict = {"calls": 0}
    questions = examples_of(respond)
    for number in range(12):
        answer = _call(respond, questions[number % len(questions)] + f" ({number})", chat)
        if answer.get("stopped_because") == "budget":
            reply = str(answer.get("reply", "")).lower()
            said_when = any(word in reply for word in ("minute", "hour", "tomorrow", "later"))
            recovered = _call(respond, "a question in a fresh chat", {"calls": 0})
            return said_when and recovered.get("stopped_because") == "answered"
    return False


def _tier_five(respond: Callable[..., Any]) -> bool:
    """`run_loop` behind it: the receipt carries the steps a plan produced."""
    answer = _call(respond, examples_of(respond)[0], {"calls": 0})
    steps = answer.get("steps")
    if isinstance(steps, list) and steps and isinstance(steps[0], dict):
        return {"tool", "args"} <= set(steps[0])
    return bool(answer.get("used_run_loop"))


@register("week1-bot")
def _week1_bot(respond: Any) -> str | None:
    """Score the bot out of 500 and print the ladder. 100 is a pass."""
    if not callable(respond):
        return "pass the function itself, e.g. bonus('week1-bot', respond)"

    try:
        seen, invalid = _conversation(respond)
    except TypeError as error:
        return (
            f"respond(text, chat) must take two arguments and return a dict ({error}). "
            "The chat dict is yours: keep the count of calls in it"
        )

    floor = _tier_one(respond, seen, invalid)
    if floor:
        print(f"   score 0/{FULL_MARKS} — the floor is the four exits")
        return floor

    earned = [True, _tier_two(respond), _tier_three(seen), _tier_four(respond), _tier_five(respond)]
    score = 100 * sum(earned)
    print(f"\n   week 1 challenge: {score}/{FULL_MARKS}")
    for (name, why), got in zip(TIERS, earned, strict=True):
        print(f"     {'✅' if got else '·  '} {name:24} {why}")
    if score < FULL_MARKS:
        print("   the ones without a tick are what is left.\n")
    return None


__all__ = [
    "DEFAULT_BROKEN",
    "DEFAULT_EXAMPLES",
    "FULL_MARKS",
    "STOP_REASONS",
    "TIERS",
    "broken_of",
    "examples_of",
]
