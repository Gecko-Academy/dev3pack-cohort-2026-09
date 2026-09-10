"""Session 9: a redacted trace.

`ch09-e1` lives in `checks.py` and judges the failure bucket the learner reads
off a trace. This module adds `ch09-e2`, which judges the function that makes a
trace safe to keep: `redact(event: dict) -> dict`.

WHY THIS IS A CHECK AND NOT A REVIEW. "Did you remove the secrets" is answerable
by machine, and the four ways to get it wrong are all mechanical:

  scrub everything      the trace survives and says nothing
  delete the field      the reader cannot tell a secret was ever there
  one placeholder       two different keys read as one
  crash on a number     a trace that raises stops being a trace

So the check drives the learner's function with its own events, where it already
knows every secret and every innocent value, and reads the result back byte for
byte. No model, no network, the same verdict on every machine.

The four fixtures below are the four properties:

  the call event          three kinds of secret, replaced and not deleted
  the retried call        the same key twice, and a second key that must differ
  the retrieve event      nothing secret, and three values that look like it
  the sparse event        a missing field, a None, an int, a float, a bool
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bootcamp_agent.checks import register

#: The API key in the fixtures. Fake, and shaped like the pattern the notebook ships.
API_KEY = "sk-a1b2c3d4e5f60718293a"
#: A second key, so "the same placeholder for everything" is a failure and not a pass.
OTHER_KEY = "sk-9f8e7d6c5b4a39281706"
#: The token after "Bearer ". The word "Bearer" is context, not a secret.
BEARER = "eyJhbGciOiJIUzI1NiJ9.ZmFrZS1wYXlsb2Fk"
#: An address on a reserved example domain.
EMAIL = "analyst@dev3pack.example.com"


@dataclass(frozen=True)
class _Failure:
    """A scenario's verdict, kept distinct from a `redact` that returns a string."""

    message: str


@dataclass(frozen=True)
class _Secret:
    """One secret inside one field, with the text that has to survive around it."""

    field: str
    prefix: str
    value: str
    suffix: str
    label: str


def _event(**fields: Any) -> dict[str, Any]:
    return dict(fields)


def _call(redact: Any, scenario: str, event: dict[str, Any]) -> Any:
    """Call the learner's function. A raised exception is that scenario's failure.

    The event is copied first, so a `redact` that edits in place still gets a
    fair reading against the pristine fixture.
    """
    try:
        return redact(dict(event))
    except Exception as error:  # noqa: BLE001 - an escaping error is the bug under test
        return _Failure(
            f"{scenario}: redact raised {type(error).__name__}: {error}; "
            "hint: a trace that raises stops being a trace — handle every value it can carry"
        )


def _shape(result: Any, event: dict[str, Any], scenario: str) -> str | None:
    """Same type, same keys. Checked before anything is read out of the result."""
    if not isinstance(result, dict):
        return (
            f"{scenario}: redact returned {type(result).__name__}; "
            "hint: return a dict — the event as it came in, with its secrets replaced"
        )
    dropped = sorted(set(event) - set(result))
    added = sorted(set(result) - set(event))
    if dropped:
        return (
            f"{scenario}: the returned event lost {dropped}; "
            "hint: replace the value, never delete the field — a field that vanishes "
            "hides that it was ever there"
        )
    if added:
        return f"{scenario}: the returned event invented {added}; hint: redaction adds no fields"
    return None


def _placeholder(result: dict[str, Any], secret: _Secret, scenario: str) -> tuple[str, str | None]:
    """Return what replaced `secret.value`, or ("", a failure message)."""
    value = result[secret.field]
    if not isinstance(value, str):
        return "", (
            f"{scenario}: {secret.field}={value!r}; "
            f"hint: {secret.field} is a string with {secret.label} in it — return a string"
        )
    if secret.value in value:
        return "", (
            f"{scenario}: {secret.label} is still in {secret.field}; "
            f"hint: match it and replace it — a trace with {secret.label} in it is a copy "
            "of the secret, kept forever, in a file nobody guards"
        )
    end = len(value) - len(secret.suffix) if secret.suffix else len(value)
    if not value.startswith(secret.prefix) or not value.endswith(secret.suffix) or end < 0:
        return "", (
            f"{scenario}: {secret.field}={value!r}; "
            f"hint: replace {secret.label} and keep every byte around it — "
            f"the line still has to read {secret.prefix!r} ... {secret.suffix!r}"
        )
    inner = value[len(secret.prefix) : end]
    if not inner:
        return "", (
            f"{scenario}: {secret.label} was cut out of {secret.field} and nothing took its place; "
            "hint: leave a placeholder, so a reader knows a value was removed here"
        )
    if "redact" not in inner.lower():
        return "", (
            f"{scenario}: {secret.label} became {inner!r}; "
            "hint: say it is a redaction, like [redacted:api_key:9f2a1c] — a reader has to "
            "tell a removed value from one that was never logged"
        )
    return inner, None


def _fields_touched(secrets: tuple[_Secret, ...]) -> set[str]:
    return {secret.field for secret in secrets}


def _untouched(
    result: dict[str, Any], event: dict[str, Any], secrets: tuple[_Secret, ...], scenario: str
) -> str | None:
    """Every field with no secret in it comes back exactly as it went in."""
    touched = _fields_touched(secrets)
    for field in event:
        if field in touched:
            continue
        if result[field] != event[field] or type(result[field]) is not type(event[field]):
            return (
                f"{scenario}: {field}={result[field]!r}, and it was {event[field]!r}; "
                "hint: nothing in that value is a secret — copy it through byte for byte. "
                "A blanket scrub keeps the trace and throws away what it was for"
            )
    return None


def _call_event(redact: Any) -> str | None:
    scenario = "the call event"
    secrets = (
        _Secret("detail", "POST /v1/messages key=", API_KEY, " status=200", "the API key"),
        _Secret("headers", "authorization: Bearer ", BEARER, "", "the bearer token"),
        _Secret("actor", "run opened by ", EMAIL, " at 09:12", "the email address"),
    )
    event = _event(
        kind="llm_call",
        detail=f"POST /v1/messages key={API_KEY} status=200",
        headers=f"authorization: Bearer {BEARER}",
        actor=f"run opened by {EMAIL} at 09:12",
        question="How do I rotate an API key without downtime?",
        attempt=1,
    )
    result = _call(redact, scenario, event)
    if isinstance(result, _Failure):
        return result.message
    if problem := _shape(result, event, scenario):
        return problem
    if problem := _untouched(result, event, secrets, scenario):
        return problem
    placeholders: list[str] = []
    for secret in secrets:
        placeholder, problem = _placeholder(result, secret, scenario)
        if problem:
            return problem
        placeholders.append(placeholder)
    if len(set(placeholders)) != len(placeholders):
        return (
            f"{scenario}: three different secrets became {placeholders}; "
            "hint: derive the placeholder from the secret, so two different values never "
            "collapse into one line a reader cannot tell apart"
        )
    return None


def _retried_call(redact: Any) -> str | None:
    scenario = "the retried call"
    secrets = (
        _Secret("detail", "attempt 1 key=", API_KEY, " -> 401", "the API key"),
        _Secret("retry", "attempt 2 key=", API_KEY, " -> 401", "the API key"),
        _Secret("fallback", "attempt 3 key=", OTHER_KEY, " -> 200", "the second API key"),
    )
    event = _event(
        kind="llm_call",
        detail=f"attempt 1 key={API_KEY} -> 401",
        retry=f"attempt 2 key={API_KEY} -> 401",
        fallback=f"attempt 3 key={OTHER_KEY} -> 200",
    )
    result = _call(redact, scenario, event)
    if isinstance(result, _Failure):
        return result.message
    if problem := _shape(result, event, scenario):
        return problem
    seen: list[str] = []
    for secret in secrets:
        placeholder, problem = _placeholder(result, secret, scenario)
        if problem:
            return problem
        seen.append(placeholder)
    if seen[0] != seen[1]:
        return (
            f"{scenario}: one key appears twice and became {seen[0]!r} then {seen[1]!r}; "
            "hint: the same secret gets the same placeholder inside one event, or the "
            "trace reads as two keys where there was one"
        )
    if seen[2] == seen[0]:
        return (
            f"{scenario}: two different keys both became {seen[2]!r}; "
            "hint: the third attempt used a different key, and the trace has to show that — "
            "derive the placeholder from the secret, not from its kind"
        )
    return None


def _retrieve_event(redact: Any) -> str | None:
    scenario = "the retrieve event"
    event = _event(
        kind="retrieve",
        detail="top_k=3 -> [('rag-basics', 0), ('agent-loops', 1), ('mcp-overview', 0)]",
        policy="the API key is read from the environment, never from the prompt",
        note="escalate in #on-call and mention @sre-oncall",
        model="fake-llm@2026-09-24",
    )
    result = _call(redact, scenario, event)
    if isinstance(result, _Failure):
        return result.message
    if problem := _shape(result, event, scenario):
        return problem
    if problem := _untouched(result, event, (), scenario):
        return problem
    return None


def _sparse_event(redact: Any) -> str | None:
    scenario = "the sparse event"
    events = (
        _event(kind="decision", detail=None, attempt=2, latency_ms=431.5, ok=True),
        _event(kind="decision", stopped_because="budget", steps=3),
    )
    for event in events:
        result = _call(redact, scenario, event)
        if isinstance(result, _Failure):
            return result.message
        if problem := _shape(result, event, scenario):
            return problem
        if problem := _untouched(result, event, (), scenario):
            return problem
    return None


@register("ch09-e2")
def _ch09_e2(redact: Any) -> str | None:
    """The trace survives redaction: secrets replaced, everything else untouched."""
    if not callable(redact):
        return "pass the redact function itself, not the result of calling it"
    for scenario in (_call_event, _retried_call, _retrieve_event, _sparse_event):
        if problem := scenario(redact):
            return problem
    return None
