"""Session 14: the deployment smoke test.

`ch14-e3` judges `smoke(request) -> dict`, the function a learner points at a
deployment to find out whether it is worth keeping. `request` is supplied by the
caller, so the check hands it four fake deployments and reads the four reports.

WHY THIS IS A CHECK AND NOT A REVIEW. "Does your smoke test work" is only
answerable by running it against a deployment that is broken, and the four ways
to get it wrong are all mechanical:

  never call the service    the report is a claim, not a measurement
  measure the second call   a warm number reported as a cold start
  read a 200 as a pass      the service invents an answer and the report agrees
  crash on the bad one      the smoke test dies exactly when it was needed

So the check supplies the transport. Nothing is fetched, nothing sleeps, and the
same four verdicts come back on every machine.

The four deployments below are the four things a report has to survive:

  warm        up, strict, fast          every field true, and the numbers small
  cold        2.4 s on the first call   a report claiming a zero cold start is wrong
  lax         200 for a malformed body  reported as malformed_rejected: false
  killed      503, memory limit         reported as unhealthy, and not crashed on

WHAT THE REPORT IS JUDGED AGAINST. Not a table of constants: the check reads the
calls the learner's function actually made and what the fake actually answered,
then holds the report to that. A smoke test that probes more is fine. One that
probes less cannot have measured what it reports, and is named for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bootcamp_agent.checks import register
from bootcamp_agent.depth_checks import _UNITS as REVERSAL_UNITS

#: The report contract. Exactly these four keys, in any order.
REPORT_FIELDS = ("cold_start_ms", "malformed_rejected", "healthy", "rollback")

#: What a well-formed request body looks like. Anything else is malformed.
GOOD_QUESTION = "How does chunking work in retrieval-augmented generation?"

#: The four fields the deployment's answer route returns when it is working.
ANSWER_FIELDS = ("answer", "citations", "confidence", "needs_human_review")

#: The unit vocabulary a reversal trigger has to use, imported rather than copied
#: so this course has one standard for a checkable condition instead of two that
#: drift apart — `ch10-e2` reads the same list. A rollback names a version as
#: often as it names a duration, so this adds the ways a release gets identified.
#: The import also registers the optional depth track into the shared registry,
#: which changes nothing a session reads: `review()` scores by id prefix.
_UNITS = REVERSAL_UNITS + ("build", "commit", "version", "tag", "release")

#: Words that turn a rollback into a description of somebody's mood about it.
_INTENTIONS = (
    "would",
    "should",
    "try to",
    "plan to",
    "hopefully",
    "if needed",
    "if necessary",
    "somehow",
    "figure out",
    "asap",
    "probably",
    "maybe",
    "consider",
)

#: A concrete way back. A backticked command counts as one too, see `_rollback`.
_ACTIONS = (
    "roll back",
    "rollback",
    "redeploy",
    "revert",
    "restore",
    "promote",
    "switch",
    "repoint",
    "re-point",
    "disable",
    "re-enable",
    "reenable",
    "alias",
    "restart",
    "deploy",
    "shut down",
    "downgrade",
    "checkout",
    "check out",
    "git ",
    "run ",
    "serve",
    "pin ",
    "stop ",
)


@dataclass
class _Deployment:
    """A fake service that records every call and never sleeps.

    `cold_ms` is charged to the first call and `warm_ms` to every call after it,
    so a cold start is a number in the response rather than a wait in the test.
    """

    name: str
    cold_ms: int
    warm_ms: int
    up: bool = True
    rejects_malformed: bool = True
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, path: str, body: Any = None) -> dict[str, Any]:
        elapsed = self.cold_ms if not self.calls else self.warm_ms
        status, reply = self._route(path, body)
        # The body is copied into the record: a learner who reuses one dict for
        # both probes would otherwise rewrite the history this check reads back.
        kept = dict(body) if isinstance(body, dict) else body
        self.calls.append({"path": path, "body": kept, "status": status, "elapsed_ms": elapsed})
        return {"status": status, "body": dict(reply), "elapsed_ms": elapsed}

    def _route(self, path: str, body: Any) -> tuple[int, dict[str, Any]]:
        if not self.up:
            return 503, {"error": "the function exceeded its memory limit and was killed"}
        if path == "/health":
            return 200, {"ok": True}
        if path != "/answer":
            return 404, {"error": f"no route {path!r}"}
        if _well_formed(body):
            return 200, {
                "answer": "Chunking splits a document into passages.",
                "citations": ["rag-basics"],
                "confidence": 0.82,
                "needs_human_review": False,
            }
        if self.rejects_malformed:
            return 400, {"error": "'question' must be a non-empty string"}
        # The dangerous one: garbage in, a confident answer out, status 200.
        return 200, {
            "answer": "Yes, that is correct.",
            "citations": [],
            "confidence": 0.9,
            "needs_human_review": False,
        }


def _well_formed(body: Any) -> bool:
    """A `question` that is a non-empty string. The boundary from session 3.

    Deliberately the same rule the notebook's own fakes apply, so a probe that
    looked well-formed while the learner was developing is well-formed here.
    """
    return (
        isinstance(body, dict)
        and isinstance(body.get("question"), str)
        and bool(body["question"].strip())
    )


def _deployments() -> tuple[_Deployment, ...]:
    return (
        _Deployment("the warm deployment", cold_ms=45, warm_ms=45),
        _Deployment("the cold deployment", cold_ms=2400, warm_ms=38),
        _Deployment("the lax deployment", cold_ms=60, warm_ms=60, rejects_malformed=False),
        _Deployment("the killed deployment", cold_ms=90, warm_ms=90, up=False),
    )


def _probes(service: _Deployment) -> str | None:
    """Every field in the report has to have been measured on THIS service."""
    answers = [call for call in service.calls if call["path"] == "/answer"]
    if not any(call["path"] == "/health" for call in service.calls):
        return (
            f"{service.name}: you never called '/health'; "
            "hint: send the same probes to every deployment — health, one good "
            "question, one malformed body — whatever the first answer was"
        )
    if not any(_well_formed(call["body"]) for call in answers):
        return (
            f"{service.name}: you never sent a well-formed question to '/answer'; "
            "hint: 'healthy' means it served a real request, so send one"
        )
    if not any(not _well_formed(call["body"]) for call in answers):
        return (
            f"{service.name}: you never sent a malformed body to '/answer'; "
            "hint: you cannot report 'malformed_rejected' without sending a malformed "
            "body — a field you did not measure is a claim"
        )
    return None


def _observed(service: _Deployment) -> tuple[bool, bool]:
    """What the service actually did: (malformed rejected, healthy)."""
    answers = [call for call in service.calls if call["path"] == "/answer"]
    malformed = [call for call in answers if not _well_formed(call["body"])]
    rejected = all(400 <= call["status"] < 500 for call in malformed)
    served = any(call["status"] == 200 and _well_formed(call["body"]) for call in answers)
    alive = any(call["path"] == "/health" and call["status"] == 200 for call in service.calls)
    return rejected, (alive and served and rejected)


def _shape(result: Any, service: _Deployment) -> str | None:
    if not isinstance(result, dict):
        return (
            f"{service.name}: smoke returned {type(result).__name__}; "
            f"hint: return a dict with the keys {list(REPORT_FIELDS)}"
        )
    missing = sorted(set(REPORT_FIELDS) - set(result))
    extra = sorted(set(result) - set(REPORT_FIELDS))
    if missing:
        return (
            f"{service.name}: the report is missing {missing}; "
            "hint: the report has a fixed shape, so a reader can compare two of them"
        )
    if extra:
        return (
            f"{service.name}: the report carries {extra}; "
            f"hint: exactly {list(REPORT_FIELDS)} — put the detail in the rollback sentence"
        )
    if isinstance(result["cold_start_ms"], bool) or not isinstance(result["cold_start_ms"], int):
        return (
            f"{service.name}: cold_start_ms={result['cold_start_ms']!r}; "
            "hint: an int of milliseconds, and the unit is already in the name"
        )
    for boolean in ("malformed_rejected", "healthy"):
        if not isinstance(result[boolean], bool):
            return (
                f"{service.name}: {boolean}={result[boolean]!r}; "
                f"hint: {boolean} is True or False — a report a reader has to interpret "
                "is not a report"
            )
    if not isinstance(result["rollback"], str):
        return f"{service.name}: rollback must be a sentence somebody can follow"
    return None


def _rollback(text: str) -> str | None:
    """The same standard `d3-e1` puts on a reversal trigger, put on a way back."""
    stripped = text.strip()
    if len(stripped) < 25:
        return (
            "'rollback' is one sentence naming the way back to the last good state; "
            "hint: write it now, because the moment you need it is the moment you "
            "cannot think"
        )
    lowered = stripped.lower()
    if not any(action in lowered for action in _ACTIONS) and "`" not in stripped:
        return (
            f"'rollback' does not name an action: {stripped!r}; "
            "hint: say what somebody DOES — redeploy the previous tag, re-point the "
            "alias, `git revert` the commit. A state you want is not a way to reach it"
        )
    for intention in _INTENTIONS:
        if intention in lowered:
            return (
                f"'rollback' reads as an intention, not an action: {intention!r} is in it; "
                "hint: 'we would roll back if it looks bad' is a feeling. Write the "
                "command, and what it costs"
            )
    if not any(character.isdigit() for character in stripped):
        return (
            "'rollback' has no number in it; hint: the same standard as an "
            "architecture decision's reversal trigger — say which version you go back "
            "to, or how long the way back takes, in a number somebody can check"
        )
    if not any(unit in lowered for unit in _UNITS):
        return (
            "'rollback' has a number and no unit; hint: 2 what? Minutes, the previous "
            "build, commit a1b2c3d. A number without a unit compares to nothing"
        )
    return None


def _judge(smoke: Any, service: _Deployment) -> str | None:
    try:
        result = smoke(service)
    except Exception as error:  # noqa: BLE001 - a smoke test that dies is the bug under test
        return (
            f"{service.name}: smoke raised {type(error).__name__}: {error}; "
            "hint: a broken deployment does not answer the way a working one does. "
            "A smoke test that crashes on it reports nothing, exactly when the report "
            "was the point"
        )
    if problem := _shape(result, service):
        return problem
    if problem := _probes(service):
        return problem
    assert isinstance(result, dict)

    first = service.calls[0]["elapsed_ms"]
    if result["cold_start_ms"] != first:
        return (
            f"{service.name}: cold_start_ms={result['cold_start_ms']}, and your first "
            f"call took {first} ms; hint: the cold start is the FIRST call, the one a "
            "user pays for while the process starts. Report what the service reported "
            "in elapsed_ms — a wall clock reads zero here, because nothing really slept"
        )

    rejected, healthy = _observed(service)
    if result["malformed_rejected"] != rejected:
        answered = "answered a malformed body with 200" if not rejected else "rejected it"
        return (
            f"{service.name}: it {answered}, and your report says "
            f"malformed_rejected={result['malformed_rejected']}; hint: read the status. "
            "A 200 for garbage is the worst outcome there is, and a smoke test that "
            "hides it is worse than none"
        )
    if result["healthy"] != healthy:
        return (
            f"{service.name}: healthy={result['healthy']}, and the deployment "
            f"{'is fine' if healthy else 'is not'}; hint: healthy is true only when "
            "'/health' answered 200, a good question came back 200 with all four "
            "answer fields, and a malformed body was refused. A smoke test that only "
            "passes tells you nothing"
        )
    if problem := _rollback(result["rollback"]):
        return f"{service.name}: {problem}"
    return None


@register("ch14-e3")
def _ch14_e3(smoke: Any) -> str | None:
    """The deployment smoke test: it measures, it reports bad news, it survives."""
    if not callable(smoke):
        return "pass the smoke function itself, not the result of calling it"
    for service in _deployments():
        if problem := _judge(smoke, service):
            return problem
    return None
