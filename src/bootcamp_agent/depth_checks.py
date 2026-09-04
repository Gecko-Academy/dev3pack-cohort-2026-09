"""Checkers for the optional depth track, one module per fundamentals pillar.

Separate from `checks.py` on purpose. That file is the fifteen-session course
registry and is already long; this is optional material nobody needs in order to
finish the course. Both register into the same `CHECKS` dict, so `check()` and
`review()` work identically here, and `review("d2")` scores one depth module the
way `review("ch07")` scores a session.

Importing this module is what registers its checkers. Each depth notebook does
that in its preflight cell.

WHAT THESE JUDGE, AND WHY IT IS DIFFERENT FROM THE COURSE CHECKERS. The course
checks behaviour: it re-runs retrieval, counts model calls, calls the function
the participant wrote. Several of these check a DECISION instead, because that
is what the pillar teaches. A decision is checkable when it carries something
falsifiable:

  - an architecture decision must name the measurement that would reverse it,
    so "when it gets slow" fails and "p95 over 800 ms for 10 minutes" passes;
  - a retention policy must name something it refuses to remember;
  - a negative-test row must record what was OBSERVED, not what was intended;
  - a latency figure must say whether it was measured or is a target.

That is the line between a decision and an opinion, and it is the whole reason
this track can be self-paced with nobody reading the answers.
"""

from __future__ import annotations

import json
import re
import sqlite3

from bootcamp_agent.checks import register

_PLACEHOLDERS = ("", "...", "todo", "tbd", "n/a", "na", "none", "-", "?", "yes", "no")


def _unwritten(text: object, minimum: int = 20) -> bool:
    """True when a field is blank, a placeholder, or too short to be a thought."""
    if not isinstance(text, str):
        return True
    stripped = text.strip()
    return stripped.lower() in _PLACEHOLDERS or len(stripped) < minimum


def _keys_are(value: object, keys: tuple[str, ...]) -> str | None:
    if not isinstance(value, dict):
        return f"expected a dict with keys {keys}"
    if set(value) != set(keys):
        missing = sorted(set(keys) - set(value))
        extra = sorted(set(value) - set(keys))
        parts = []
        if missing:
            parts.append(f"missing {missing}")
        if extra:
            parts.append(f"unexpected {extra}")
        return "; ".join(parts)
    return None


# ============================================================ D1 · full stack


@register("d1-e1")
def _d1_e1(body: object) -> str | None:
    """The response contract. What a caller gets, and what it must never get."""
    required = ("answer", "citations", "confidence", "needs_human_review", "request_id")
    if not isinstance(body, dict):
        return "expected the response body as a dict"
    missing = sorted(set(required) - set(body))
    if missing:
        return f"the response body is missing {missing}"
    if not isinstance(body["citations"], list):
        return "'citations' must be a list, so a caller can iterate it without a type check"
    if not isinstance(body["needs_human_review"], bool):
        return "'needs_human_review' must be a bool; a refusal is a state, not a string"
    # The trace is useful, and it is also the prompt, the retrieved passages and
    # the tool arguments. It leaves only when a caller asks for it.
    if "trace" in body:
        return "the trace must not be in the default body; make it opt-in, it carries the prompt"
    for leak in ("prompt", "system", "api_key", "raw"):
        if leak in body:
            return f"'{leak}' must never cross the boundary"
    return None


@register("d1-e2")
def _d1_e2(error_for: object) -> str | None:
    """The error envelope: a 4xx names the field, a 5xx says nothing."""
    if not callable(error_for):
        return "expected the error_for(kind, detail) function itself"
    try:
        bad = error_for("invalid_request", "question must be a string")
        boom = error_for("internal", "KeyError: 'secret_token' at agent.py:88")
    except Exception as error:  # noqa: BLE001 - a crashing mapper is the failure
        return f"error_for raised {type(error).__name__}: {error}"

    for name, payload in (("invalid_request", bad), ("internal", boom)):
        problem = _keys_are(
            payload.get("error") if isinstance(payload, dict) else None,
            ("code", "message", "request_id"),
        )
        if problem:
            return f"{name}: expected {{'error': {{code, message, request_id}}}}; {problem}"

    if bad["error"]["code"] != "invalid_request":
        return "a bad request must carry code 'invalid_request'"
    if "question" not in bad["error"]["message"]:
        return "a 4xx should name the field that was wrong, so a caller can fix it"
    if "secret_token" in boom["error"]["message"] or "agent.py" in boom["error"]["message"]:
        return "a 5xx must not echo the exception; that is how tokens and paths leak"
    if _unwritten(boom["error"]["message"], minimum=10):
        return "a 5xx still needs a usable sentence, just not the internals"
    return None


@register("d1-e3")
def _d1_e3(states: object) -> str | None:
    """Client states. A refusal is a successful response, not an error."""
    if not isinstance(states, dict):
        return "expected a dict of state name -> what the user sees"
    lowered = {str(k).strip().lower() for k in states}
    for needed in ("refused", "error"):
        if needed not in lowered:
            return (
                f"missing the '{needed}' state; a refusal and an error are different things "
                "and the UI has to say so"
            )
    if len(lowered) < 4:
        return "at least four states: something before, something during, and both outcomes"
    for name, shown in states.items():
        if _unwritten(shown, minimum=12):
            return f"state {name!r} needs a sentence saying what the user actually sees"
    return None


# ========================================================== D2 · managing data


@register("d2-e1")
def _d2_e1(choice: object) -> str | None:
    """The storage decision, argued from an access pattern rather than a taste."""
    problem = _keys_are(choice, ("store", "access_pattern", "why", "what_it_costs"))
    if problem:
        return problem
    assert isinstance(choice, dict)
    if _unwritten(choice["store"], minimum=3):
        return "'store' names the thing you chose, for example 'sqlite, one table per version'"
    if _unwritten(choice["access_pattern"], minimum=25):
        return (
            "'access_pattern' is the actual argument: how the data is read and written, "
            "how often, and by whom. A store chosen without one is a guess"
        )
    if _unwritten(choice["why"], minimum=25):
        return "'why' connects the access pattern to the store"
    if _unwritten(choice["what_it_costs"], minimum=20):
        return (
            "'what_it_costs' names what this choice makes harder; "
            "every store makes something harder"
        )
    return None


@register("d2-e2")
def _d2_e2(ingest: object) -> str | None:
    """Ingestion is idempotent by content hash, and a change makes a new version."""
    if not callable(ingest):
        return "expected the ingest(conn, doc_id, text) function itself"
    conn = sqlite3.connect(":memory:")
    try:
        try:
            ingest(conn, "rag-basics", "chunking splits a document")
            ingest(conn, "rag-basics", "chunking splits a document")
        except Exception as error:  # noqa: BLE001
            return f"ingest raised on a repeat: {type(error).__name__}: {error}"
        rows = conn.execute(
            "select count(*) from documents where doc_id = ?", ("rag-basics",)
        ).fetchone()[0]
        if rows != 1:
            return (
                f"ingesting the same text twice produced {rows} rows; re-running an import "
                "must not duplicate. Key on a content hash"
            )
        ingest(conn, "rag-basics", "chunking splits a document into passages")
        rows = conn.execute(
            "select count(*) from documents where doc_id = ?", ("rag-basics",)
        ).fetchone()[0]
        if rows != 2:
            return (
                f"changed text produced {rows} row(s); a correction must be a new version, "
                "not an overwrite, or you cannot say what an old answer was grounded in"
            )
    except sqlite3.Error as error:
        return f"the table is not there yet, or its columns differ: {error}"
    finally:
        conn.close()
    return None


@register("d2-e3")
def _d2_e3(policy: object) -> str | None:
    """A retention policy is only real if something is refused."""
    problem = _keys_are(policy, ("keep", "keep_for", "delete_on_request", "never_store"))
    if problem:
        return problem
    assert isinstance(policy, dict)
    if not isinstance(policy["never_store"], list) or not policy["never_store"]:
        return (
            "'never_store' must list at least one thing you refuse to keep. A policy that "
            "stores everything and calls it a policy is the one that leaks"
        )
    for item in policy["never_store"]:
        if _unwritten(item, minimum=4):
            return "every 'never_store' entry names a real thing, for example 'the raw question'"
    if _unwritten(policy["keep_for"], minimum=6):
        return "'keep_for' needs a duration with a unit, not 'a while'"
    if not re.search(r"\d", str(policy["keep_for"])):
        return "'keep_for' needs a number: 30 days, 12 months, until the cohort ends"
    if _unwritten(policy["delete_on_request"], minimum=20):
        return "'delete_on_request' says what actually happens, and how you would prove it happened"
    return None


# ========================================================== D3 · architecture


_UNITS = (
    "ms",
    "millisecond",
    "s ",
    "second",
    "min",
    "minute",
    "hour",
    "day",
    "%",
    "percent",
    "req",
    "rps",
    "qps",
    "user",
    "row",
    "mb",
    "gb",
    "call",
)


@register("d3-e1")
def _d3_e1(adr: object) -> str | None:
    """A decision record. The reversal trigger is the part that makes it engineering."""
    problem = _keys_are(adr, ("decision", "context", "alternative", "why_not", "reverses_when"))
    if problem:
        return problem
    assert isinstance(adr, dict)
    for field, minimum in (("decision", 20), ("context", 30), ("alternative", 15), ("why_not", 25)):
        if _unwritten(adr[field], minimum=minimum):
            return f"'{field}' needs a real sentence"
    trigger = str(adr["reverses_when"])
    if _unwritten(trigger, minimum=20):
        return "'reverses_when' is the whole exercise; write the condition out"
    if not re.search(r"\d", trigger):
        return (
            "'reverses_when' has no number in it. 'When it gets slow' is an opinion; "
            "'when p95 stays over 800 ms for 10 minutes' is a trigger somebody can check"
        )
    if not any(unit in trigger.lower() for unit in _UNITS):
        return (
            "'reverses_when' has a number but no unit. A number without a unit cannot be "
            "compared against anything"
        )
    return None


@register("d3-e2")
def _d3_e2(verdicts: object) -> str | None:
    """Which imports cross a boundary that should not be crossed."""
    truth = {
        "api imports agent": False,
        "api imports retrieval": True,
        "agent imports storage": True,
        "storage imports agent": True,
        "cli imports agent": False,
    }
    if not isinstance(verdicts, dict) or set(verdicts) != set(truth):
        return f"expected a verdict for each of {sorted(truth)}"
    for edge, expected in truth.items():
        got = verdicts[edge]
        if not isinstance(got, bool):
            return f"{edge!r}: answer True (it breaks the boundary) or False (it is fine)"
        if got != expected:
            reason = {
                "api imports agent": "the API calling the domain seam is the point of having one",
                "api imports retrieval": "reaching past the seam duplicates the agent",
                "agent imports storage": "the domain should not know where anything is persisted",
                "storage imports agent": "storage calling the domain inverts the dependency",
                "cli imports agent": "a client calling the seam is exactly what a client does",
            }[edge]
            return f"{edge!r} should be {expected}: {reason}"
    return None


# ================================================= D4 · secure and reliable


@register("d4-e1")
def _d4_e1(matrix: object) -> str | None:
    """The negative matrix. 'Observed' is what separates it from a wish list."""
    if not isinstance(matrix, list) or len(matrix) < 4:
        return "expected at least four rows, each a dict"
    for row in matrix:
        problem = _keys_are(row, ("input", "expected", "observed"))
        if problem:
            return f"each row needs input, expected and observed; {problem}"
        assert isinstance(row, dict)
        if _unwritten(row["input"], minimum=8):
            return "'input' names the bad input you actually sent"
        if _unwritten(row["expected"], minimum=12):
            return "'expected' says what should happen"
        if _unwritten(row["observed"], minimum=12):
            return (
                "'observed' must record what happened when you ran it. An unfilled "
                "'observed' means the row was never tested, and an untested row is a hope"
            )
        if str(row["observed"]).strip().lower() in {
            "same",
            "as expected",
            "ok",
            "same as expected",
        }:
            return (
                "'observed' says 'as expected', which records nothing. Write what you saw: "
                "the error class, the status, the message"
            )
    return None


@register("d4-e2")
def _d4_e2(answer_within: object) -> str | None:
    """A timeout returns a flagged refusal. It does not crash and it does not lie."""
    if not callable(answer_within):
        return "expected the answer_within(client, question, seconds) function itself"

    class _Slow:
        def complete(self, system: str, user: str) -> str:  # noqa: ARG002
            raise TimeoutError("upstream took too long")

    class _Fine:
        def complete(self, system: str, user: str) -> str:  # noqa: ARG002
            return json.dumps(
                {
                    "answer": "Chunking splits a document into passages.",
                    "citations": ["rag-basics"],
                    "confidence": 0.8,
                    "needs_human_review": False,
                }
            )

    try:
        timed_out = answer_within(_Slow(), "what is chunking", 0.01)
    except TimeoutError:
        return "the timeout escaped; catch it and turn it into a refusal the caller can render"
    except Exception as error:  # noqa: BLE001
        return f"raised {type(error).__name__} instead of returning a refusal: {error}"

    if not isinstance(timed_out, dict) or "needs_human_review" not in timed_out:
        return "on timeout, return a dict shaped like an answer, with needs_human_review"
    if timed_out["needs_human_review"] is not True:
        return "a timed-out answer must be flagged for review; it is not a normal answer"
    if timed_out.get("citations"):
        return "a timeout cites nothing. Citing anything here invents grounding you never had"

    try:
        fine = answer_within(_Fine(), "what is chunking", 5)
    except Exception as error:  # noqa: BLE001
        return f"the healthy path raised {type(error).__name__}: {error}"
    if fine.get("needs_human_review") is not False:
        return "a healthy call must not be flagged; the guard has to be off in the normal case"
    return None


@register("d4-e3")
def _d4_e3(model: object) -> str | None:
    """A threat model that accepts nothing has not finished thinking."""
    problem = _keys_are(model, ("assets", "trust_boundary", "mitigated", "accepted"))
    if problem:
        return problem
    assert isinstance(model, dict)
    for field in ("assets", "mitigated"):
        if not isinstance(model[field], list) or not model[field]:
            return f"'{field}' is a non-empty list"
    if _unwritten(model["trust_boundary"], minimum=25):
        return "'trust_boundary' says where untrusted input stops being trusted"
    if _unwritten(model["accepted"], minimum=25):
        return (
            "'accepted' names one risk you decided to live with, and why. Every real system "
            "has one. A model with only mitigations is a list of intentions"
        )
    return None


# ==================================================== D5 · production signals


@register("d5-e1")
def _d5_e1(line: object) -> str | None:
    """One log line: correlatable, and safe to keep."""
    if isinstance(line, str):
        try:
            line = json.loads(line)
        except json.JSONDecodeError:
            return "the line must be JSON, so a machine can read it without a regex"
    if not isinstance(line, dict):
        return "expected one structured log line as a dict or a JSON string"
    for field in ("request_id", "event", "duration_ms"):
        if field not in line:
            return f"missing {field!r}; without a request id you cannot follow one call through"
    if not isinstance(line["duration_ms"], (int, float)):
        return "'duration_ms' is a number, and its unit is in the name"
    for leak in ("question", "answer", "prompt", "api_key", "token", "user_email"):
        if leak in line:
            return (
                f"'{leak}' must not be in the log. Logs are copied, shipped and kept far "
                "longer than anyone intends"
            )
    return None


@register("d5-e2")
def _d5_e2(measurement: object) -> str | None:
    """p50 and p95, measured on your own machine, and labelled as measured."""
    problem = _keys_are(measurement, ("p50_ms", "p95_ms", "runs", "source"))
    if problem:
        return problem
    assert isinstance(measurement, dict)
    for field in ("p50_ms", "p95_ms"):
        if not isinstance(measurement[field], (int, float)):
            return f"'{field}' is a number in milliseconds"
    if measurement["p95_ms"] < measurement["p50_ms"]:
        return "p95 cannot be below p50; check which is which"
    if not isinstance(measurement["runs"], int) or measurement["runs"] < 20:
        return "measure at least 20 runs; a percentile over five samples is not a percentile"
    source = str(measurement["source"]).strip().lower()
    if source not in {"measured", "target"}:
        return (
            "'source' must be exactly 'measured' or 'target'. Every latency number in a "
            "document is one or the other, and mixing them is how a goal becomes a claim"
        )
    if source == "target":
        return "run it and record the real numbers; the target belongs in the SLO, not here"
    return None


@register("d5-e3")
def _d5_e3(runbook: object) -> str | None:
    """A runbook nobody can follow under pressure is a document, not a runbook."""
    problem = _keys_are(runbook, ("symptom", "first_check", "rollback", "how_you_know"))
    if problem:
        return problem
    assert isinstance(runbook, dict)
    if _unwritten(runbook["symptom"], minimum=20):
        return "'symptom' is what someone notices first, in their words"
    if _unwritten(runbook["first_check"], minimum=20):
        return "'first_check' is the one command or dashboard to open first"
    if _unwritten(runbook["rollback"], minimum=20):
        return "'rollback' is the exact way back to the last good state"
    if _unwritten(runbook["how_you_know"], minimum=20):
        return (
            "'how_you_know' is the observation that says it worked. Without it you cannot "
            "tell recovery from a pause"
        )
    return None
