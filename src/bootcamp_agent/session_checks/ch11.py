"""Session 11: per-user memory that does not leak.

`ch11-e1` (the memory record) and `ch11-e2` (the retention policy) live in
`checks.py`. This module adds `ch11-e3`, which judges the store the learner
writes: `remember(user_id, key, value)` and `recall(user_id, key)`.

WHY THIS CHECK EXISTS. A store written for one user works perfectly until the
second user arrives, and then it works perfectly for the wrong person. The bug
is not exotic: a dict keyed on `key` alone, a `user_id` argument that is
accepted and never used, a blank id that quietly becomes one bucket everybody
reads. None of that fails a single-user test, so the second user is the test.

WHAT IT DRIVES, AND WHAT IT NEVER READS. The check calls the two functions with
its own users, keys and values, and judges what comes back out. It never looks
inside the store: no attribute, no dict, no private field. A store that keeps
its data in SQLite, in a dict, or in a text file passes or fails on the same
evidence, which is the evidence the next caller has too.

Four scenarios, one requirement each:

  two users, one key   ana and bruno both store 'locale'; each reads their own
  a key never stored   a miss returns None, never a raise and never a neighbour's value
  a missing user id    '' and None are refused, not turned into a shared bucket
  a mutable value      the list that comes back is a copy, so editing it changes nothing

The learner may pass the store class itself (built fresh per scenario) or
`{'remember': ..., 'recall': ...}` for a module-level pair. Every scenario uses
its own user ids, so the function pair sees no interference from the scenario
before it.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from bootcamp_agent.checks import register

Pair = tuple[Callable[..., Any], Callable[..., Any]]

#: What a store must never accept as the owner of a memory.
MISSING_IDS: tuple[Any, ...] = ("", None)


class _Raised:
    """A call that raised. Kept as a value so a scenario can decide what it means."""

    def __init__(self, error: BaseException) -> None:
        self.error = error

    def __str__(self) -> str:
        return f"{type(self.error).__name__}: {self.error}"


def _call(function: Callable[..., Any], *args: Any) -> Any:
    """Call the learner's function; a raised error becomes a value, not a crash."""
    try:
        return function(*args)
    except Exception as error:  # noqa: BLE001 - whether raising is right depends on the scenario
        return _Raised(error)


def _open(value: Any) -> Pair | str:
    """A fresh `(remember, recall)` pair, or the message that says what to pass."""
    if isinstance(value, dict):
        if set(value) != {"remember", "recall"}:
            return (
                f"expected the MemoryStore class, or {{'remember': ..., 'recall': ...}}; "
                f"got a dict with keys {sorted(value)}"
            )
        remember, recall = value["remember"], value["recall"]
        if not callable(remember) or not callable(recall):
            return "pass the two functions themselves, not the result of calling them"
        return remember, recall
    if isinstance(value, type) or callable(value):
        store = _call(value)
        if isinstance(store, _Raised):
            return (
                f"building the store raised {store}; "
                "hint: MemoryStore() must build an empty store with no arguments"
            )
        remember, recall = getattr(store, "remember", None), getattr(store, "recall", None)
        if not callable(remember) or not callable(recall):
            return (
                "the store needs remember(user_id, key, value) and recall(user_id, key) methods; "
                "hint: pass the class itself, not an instance and not a call"
            )
        return remember, recall
    if hasattr(value, "remember") and hasattr(value, "recall"):
        return (
            "pass the MemoryStore class itself, not an instance; "
            "hint: each scenario needs a store of its own, so the check builds them"
        )
    return (
        f"expected the MemoryStore class or {{'remember': ..., 'recall': ...}}, "
        f"got {type(value).__name__}"
    )


def _store(remember: Callable[..., Any], scenario: str, *args: Any) -> str | None:
    """Write a value that is expected to be accepted. Returns the problem, if any."""
    outcome = _call(remember, *args)
    if isinstance(outcome, _Raised):
        return (
            f"{scenario}: remember({args[0]!r}, {args[1]!r}, ...) raised {outcome}; "
            "hint: a valid user id, key and value is the case that must work"
        )
    return None


def _two_users_one_key(remember: Callable[..., Any], recall: Callable[..., Any]) -> str | None:
    """The leak, in its cheapest form: two people, the same key, one bucket."""
    scenario = "two users, one key"
    written = (("ana", "pt-BR"), ("bruno", "en-GB"))
    for user, locale in written:
        if problem := _store(remember, scenario, user, "locale", locale):
            return problem
    for user, locale in written:
        got = _call(recall, user, "locale")
        if isinstance(got, _Raised):
            return (
                f"{scenario}: recall({user!r}, 'locale') raised {got}; "
                "hint: reading a value this user stored must return it, not raise"
            )
        if got != locale:
            return (
                f"{scenario}: ana stored 'pt-BR' and bruno stored 'en-GB' under the same key; "
                f"recall({user!r}, 'locale') returned {got!r} and must return {locale!r}; "
                "hint: the owner is part of the key — store on (user_id, key), never on key alone"
            )
    return None


def _a_key_never_stored(remember: Callable[..., Any], recall: Callable[..., Any]) -> str | None:
    """A miss is None: not a raise, and not the value the neighbour happens to have."""
    scenario = "a key never stored"
    if problem := _store(remember, scenario, "carla", "locale", "pt-BR"):
        return problem
    for user, key, why in (
        ("carla", "timezone", "carla stored 'locale' and never stored 'timezone'"),
        ("dan", "locale", "dan has stored nothing at all"),
    ):
        got = _call(recall, user, key)
        if isinstance(got, _Raised):
            return (
                f"{scenario}: {why}, and recall({user!r}, {key!r}) raised {got}; "
                "hint: a miss is an answer — return None instead of indexing the store directly"
            )
        if got is not None:
            return (
                f"{scenario}: {why}, and recall({user!r}, {key!r}) returned {got!r}; "
                "hint: return None on a miss, with no fallback to a default or to another user"
            )
    return None


def _a_missing_user_id(remember: Callable[..., Any], recall: Callable[..., Any]) -> str | None:
    """An unowned memory is everybody's memory. Refuse it at the door."""
    scenario = "a missing user id"
    for missing in MISSING_IDS:
        outcome = _call(remember, missing, "locale", "pt-BR")
        if not isinstance(outcome, _Raised):
            return (
                f"{scenario}: remember({missing!r}, 'locale', 'pt-BR') was accepted and "
                f"returned {outcome!r}; hint: raise ValueError before storing anything — "
                "a memory with no owner becomes one bucket every caller can read"
            )
        got = _call(recall, missing, "locale")
        if not isinstance(got, _Raised):
            return (
                f"{scenario}: recall({missing!r}, 'locale') returned {got!r} instead of "
                "refusing; hint: validate the user id in both functions, or the read path "
                "is the way into the bucket the write path refused to make"
            )
    return None


def _a_mutable_value(remember: Callable[..., Any], recall: Callable[..., Any]) -> str | None:
    """A returned reference is a second writer nobody declared."""
    scenario = "a mutable value"
    tags = ["retrieval"]
    if problem := _store(remember, scenario, "erin", "tags", tags):
        return problem
    tags.append("edited by the writer")
    got = _call(recall, "erin", "tags")
    if isinstance(got, _Raised):
        return f"{scenario}: recall('erin', 'tags') raised {got}"
    if got != ["retrieval"]:
        return (
            f"{scenario}: the caller edited its own list after storing it and the store now "
            f"holds {got!r}; hint: copy on the way in — store copy.deepcopy(value), not the "
            "object you were handed"
        )
    got.append("edited by the reader")
    again = _call(recall, "erin", "tags")
    if isinstance(again, _Raised):
        return f"{scenario}: the second recall('erin', 'tags') raised {again}"
    if again != ["retrieval"]:
        return (
            f"{scenario}: a reader appended to what recall returned and the next reader now "
            f"sees {again!r}; hint: copy on the way out — return copy.deepcopy(value), or the "
            "caller edits your store in place"
        )
    return None


@register("ch11-e3")
def _ch11_e3(store: Any) -> str | None:
    """Per-user memory: no leak, no raise on a miss, no unowned bucket, no live reference."""
    for scenario in (
        _two_users_one_key,
        _a_key_never_stored,
        _a_missing_user_id,
        _a_mutable_value,
    ):
        opened = _open(store)
        if isinstance(opened, str):
            return opened
        if problem := scenario(*opened):
            return problem
    return None
