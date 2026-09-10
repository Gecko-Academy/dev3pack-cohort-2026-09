"""Session 8: typed transitions.

`ch08-e1` (the pattern comparison) and `ch08-e2` (the graph appendix) live in
`checks.py`. This module adds `ch08-e3`, which judges the state machine the
learner writes: `step(state, event) -> state`.

WHY A TABLE AND NOT A CONDITION. A workflow written as `if`/`elif` has an
implicit edge for every case nobody wrote: the fall-through. A table has none —
a pair that is not in it is refused, and refusing is a state you can read in the
result. The five states and six edges below are the whole research graph, and
the check drives the learner's `step` over every pair of them, legal and not.

The scenarios are the rows of the outcome table:

  answer path       planning -> retrieving -> answering -> done
  out-of-scope path planning -> refusing -> done, never through answering
  empty-retrieval   planning -> retrieving -> refusing -> done
  terminal          no event moves anything out of done
  undeclared edges  refused, unchanged, with a reason naming event and state

Model-free and deterministic: the check supplies its own event sequences, so
every edge is exercised on purpose rather than when a model happens to pick it.
"""

from __future__ import annotations

import copy
from typing import Any

from bootcamp_agent.checks import register

#: The five states of the research graph. `done` is terminal by having no row.
STATES = ("planning", "retrieving", "answering", "refusing", "done")

#: The declared transition table: six edges, and nothing else is legal.
TRANSITIONS: dict[tuple[str, str], str] = {
    ("planning", "plan_ready"): "retrieving",
    ("planning", "out_of_scope"): "refusing",
    ("retrieving", "hits"): "answering",
    ("retrieving", "no_hits"): "refusing",
    ("answering", "answered"): "done",
    ("refusing", "refused"): "done",
}

#: Every event name the table mentions, plus one it never will.
EVENTS = tuple(sorted({name for _, name in TRANSITIONS}))
UNDECLARED_EVENT = "skip_ahead"

#: Where every run starts, and the shape of a state dict.
START: dict[str, Any] = {"state": "planning", "visited": ["planning"], "rejected": None}

State = dict[str, Any]


def _call(step: Any, state: State, event_name: str, scenario: str) -> State | str:
    """One transition. A raised exception is that scenario's failure, as a string."""
    try:
        return step(copy.deepcopy(state), {"name": event_name})  # type: ignore[no-any-return]
    except Exception as error:  # noqa: BLE001 - an escaping error is the bug under test
        return (
            f"{scenario}: step raised {type(error).__name__}: {error}; "
            f"hint: an event the table does not declare is refused, not raised — "
            f"return the state unchanged with a 'rejected' sentence"
        )


def _shape(result: Any, scenario: str) -> str | None:
    """The state contract, checked before anything is read out of it."""
    if not isinstance(result, dict):
        return (
            f"{scenario}: step returned {type(result).__name__}; "
            "hint: return a state dict with 'state', 'visited' and 'rejected'"
        )
    missing = [key for key in ("state", "visited") if key not in result]
    if missing:
        return (
            f"{scenario}: the returned state is missing {missing}; "
            "hint: build the same keys on every return, the refused one included"
        )
    if result["state"] not in STATES:
        return f"{scenario}: state={result['state']!r}; hint: it must be one of {STATES}"
    visited = result["visited"]
    if not isinstance(visited, list) or not all(entry in STATES for entry in visited):
        return (
            f"{scenario}: visited={visited!r}; "
            f"hint: 'visited' is a list of state names, in the order they were entered"
        )
    return None


def _moved(step: Any, state: State, event_name: str, target: str, scenario: str) -> State | str:
    """Take one legal edge and hold it to the contract. A string is the problem."""
    result = _call(step, state, event_name, scenario)
    if isinstance(result, str):
        return result
    if problem := _shape(result, scenario):
        return problem
    if result["state"] != target:
        return (
            f"{scenario}: {event_name!r} from {state['state']!r} left you in "
            f"{result['state']!r}; hint: the table declares that edge as "
            f"{state['state']!r} -> {target!r}, so follow it"
        )
    if result.get("rejected"):
        return (
            f"{scenario}: {event_name!r} is a declared edge and it was rejected "
            f"({result['rejected']!r}); hint: only a pair that is missing from the "
            "table is refused"
        )
    before, after = state["visited"], result["visited"]
    if after[: len(before)] != before:
        return (
            f"{scenario}: visited went from {before!r} to {after!r}; hint: append to "
            "the list, never rewrite or reorder it — the history of a run only grows"
        )
    if len(after) != len(before) + 1 or after[-1] != target:
        return (
            f"{scenario}: visited is {after!r} after moving to {target!r}; hint: one "
            "move appends exactly one entry, and it is the state you entered"
        )
    return result


def _refused(step: Any, state: State, event_name: str, scenario: str) -> str | None:
    """An undeclared edge: nothing moves, and the result says why."""
    result = _call(step, state, event_name, scenario)
    if isinstance(result, str):
        return result
    if problem := _shape(result, scenario):
        return problem
    if result["state"] != state["state"]:
        return (
            f"{scenario}: {event_name!r} moved {state['state']!r} to {result['state']!r}; "
            f"hint: ({state['state']!r}, {event_name!r}) is not in the table, so the "
            "state stays exactly where it was"
        )
    if result["visited"] != state["visited"]:
        return (
            f"{scenario}: visited changed from {state['visited']!r} to "
            f"{result['visited']!r} on a refused event; hint: a run that did not move "
            "visited nothing"
        )
    rejected = result.get("rejected")
    if not isinstance(rejected, str) or not rejected.strip():
        return (
            f"{scenario}: rejected={rejected!r} after {event_name!r}; hint: write one "
            "sentence the caller can read, saying which event was refused and from where"
        )
    for word in (event_name, state["state"]):
        if word not in rejected:
            return (
                f"{scenario}: rejected={rejected!r} does not name {word!r}; hint: an "
                "f-string with the event and the state it was refused from tells the "
                "reader what to fix"
            )
    return None


def _walk(step: Any, path: tuple[tuple[str, str], ...], scenario: str) -> State | str:
    """Drive a whole event sequence from START, one declared edge at a time."""
    state: State = copy.deepcopy(START)
    for event_name, target in path:
        moved = _moved(step, state, event_name, target, scenario)
        if isinstance(moved, str):
            return moved
        state = moved
    return state


#: The one sequence that reaches `done` through an answer.
ANSWER_PATH = (("plan_ready", "retrieving"), ("hits", "answering"), ("answered", "done"))


def _answer_path(step: Any) -> str | None:
    scenario = "the answer path"
    state = _walk(step, ANSWER_PATH, scenario)
    if isinstance(state, str):
        return state
    if state["visited"] != ["planning", "retrieving", "answering", "done"]:
        return (
            f"{scenario}: visited={state['visited']!r}; hint: it starts at 'planning' "
            "and gains one entry per move, so a finished answer run reads "
            "['planning', 'retrieving', 'answering', 'done']"
        )
    return None


def _drive(step: Any, events: tuple[str, ...], scenario: str) -> State | str:
    """Feed a sequence of events and only hold the state contract, not the route.

    The route is what the refusal scenarios are judging, so this walk must not
    decide it in advance the way :func:`_walk` does.
    """
    state: State = copy.deepcopy(START)
    for event_name in events:
        result = _call(step, state, event_name, scenario)
        if isinstance(result, str):
            return result
        if problem := _shape(result, scenario):
            return problem
        before, after = state["visited"], result["visited"]
        if after[: len(before)] != before:
            return (
                f"{scenario}: visited went from {before!r} to {after!r} on {event_name!r}; "
                "hint: append to the list, never rewrite or reorder it"
            )
        state = result
    return state


def _refusal_path(step: Any, events: tuple[str, ...], scenario: str) -> str | None:
    """A refusal reaches 'refusing', then 'done', and never touches 'answering'."""
    state = _drive(step, (*events, "refused"), scenario)
    if isinstance(state, str):
        return state
    if "answering" in state["visited"]:
        return (
            f"{scenario}: visited={state['visited']!r}; hint: a refusal never passes "
            "through 'answering' — there is nothing to answer there, and the hop "
            "spends a model call on a question you already decided not to answer"
        )
    if state["visited"][-2:] != ["refusing", "done"]:
        return (
            f"{scenario}: visited={state['visited']!r}; hint: the refusal path ends "
            "'refusing' then 'done', so the record shows the run stopped on purpose"
        )
    return None


def _terminal(step: Any) -> str | None:
    scenario = "the terminal state"
    state = _walk(step, ANSWER_PATH, scenario)
    if isinstance(state, str):
        return state
    for event_name in (*EVENTS, UNDECLARED_EVENT):
        where = f"{scenario}: {event_name!r} after 'done'"
        if problem := _refused(step, state, event_name, where):
            return problem
    return None


def _undeclared_edges(step: Any) -> str | None:
    """Every pair the table does not declare, from every state, refused the same way."""
    for current in STATES:
        state: State = {"state": current, "visited": [current], "rejected": None}
        for event_name in (*EVENTS, UNDECLARED_EVENT):
            if (current, event_name) in TRANSITIONS:
                continue
            scenario = f"{event_name!r} in state {current!r}"
            if problem := _refused(step, state, event_name, scenario):
                return problem
    return None


def _repeatable(step: Any) -> str | None:
    """The same sequence twice: a transition depends on the state, never on history."""
    scenario = "the same run twice"
    first = _walk(step, ANSWER_PATH, scenario)
    if isinstance(first, str):
        return first
    second = _walk(step, ANSWER_PATH, scenario)
    if isinstance(second, str):
        return second
    if first != second:
        return (
            f"{scenario}: the run gave {first!r} and then {second!r}; hint: read the "
            "next state out of the table and the state you were given — a counter or "
            "a global makes one event mean two different things"
        )
    return None


@register("ch08-e3")
def _ch08_e3(step: Any) -> str | None:
    """Typed transitions: declared edges are followed, undeclared ones are refused."""
    if not callable(step):
        return "pass the step function itself, not the result of calling it"
    scenarios = (
        _answer_path,
        lambda fn: _refusal_path(fn, ("out_of_scope",), "the out-of-scope path"),
        lambda fn: _refusal_path(fn, ("plan_ready", "no_hits"), "the empty-retrieval path"),
        _terminal,
        _undeclared_edges,
        _repeatable,
    )
    for scenario in scenarios:
        if problem := scenario(step):
            return problem
    return None
