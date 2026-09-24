"""Project 04: trace the team you built yesterday, then grade it.

WHY THIS PROJECT EXISTS, AND WHY IT DOES NOT EDIT PROJECT 03. The analyst team
already carries a receipt: `calls`, `stopped_because`, `rejected`. A receipt is
not a trace. It says what happened in total and never says in what order, so it
cannot tell "the passage never arrived" from "it arrived and was ignored", which
is the one distinction session 9 spends an hour on.

The learner could add emitters inside `analyst_team.py`. They must not, and the
reason is worth more than the convenience: you rarely own the thing you need to
trace. A graph you did not write still streams its updates, and watching those
updates is a trace you can build from the outside. So project 04 wraps rather
than edits, and project 03's notebook keeps comparing its hand-built state to the
imported one, field for field, exactly as it does today.

THE FOUR DELIVERABLES ARE FOUR DIFFERENT SHAPES, on purpose. Project 03 shipped
with `e1` and `e3` both wanting a `TeamState`, so passing the wrong one still
went green and the mix-up stayed invisible until a founder hit it live in class.
Here: a list of events, a list of cases, a list of outcomes, a dict of counts.
Each check refuses the other three by message rather than by crashing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ..agent import FAILURE_BUCKETS, TRACE_KINDS
from ..bonus import register
from .analyst_team import companies
from .sec_filings import questions

#: A trace shorter than this is not a run, it is a print statement.
MIN_TRACE_EVENTS = 3

#: Fewer cases than this and one lucky answer moves the pass rate more than a fix.
MIN_CASES = 10


def _rows(value: Any) -> list[Mapping[str, Any]] | None:
    """A non-empty sequence of mappings, or None. The shape all three lists share."""
    if isinstance(value, Mapping) or isinstance(value, (str, bytes)):
        return None
    if not isinstance(value, Sequence):
        return None
    rows = list(value)
    if not rows or not all(isinstance(row, Mapping) for row in rows):
        return None
    return rows


def _has(rows: Sequence[Mapping[str, Any]], *keys: str) -> bool:
    """Every row carries every key. What tells one list-of-dicts from another."""
    return all(all(key in row for key in keys) for row in rows)


@register("project-04-e1")
def _trace(trace: Any) -> str | None:
    """Step 1: a trace of one run, built by watching a graph from the outside."""
    rows = _rows(trace)
    if rows is None:
        return (
            "pass the trace from step 1, a list of {'kind': ..., 'detail': ...} events: "
            "check_step('project-04-e1', trace)"
        )
    if not _has(rows, "kind", "detail"):
        missing = sorted({key for key in ("kind", "detail") for row in rows if key not in row})
        return f"every event needs 'kind' and 'detail'; {missing} is missing from at least one"
    if len(rows) < MIN_TRACE_EVENTS:
        return (
            f"{len(rows)} event(s); a run of this team touches retrieval and the model, "
            f"so a real trace has at least {MIN_TRACE_EVENTS}"
        )
    unknown = sorted({str(row["kind"]) for row in rows} - set(TRACE_KINDS))
    if unknown:
        return f"kind {unknown} is not one of {list(TRACE_KINDS)}; a new kind nobody reads is noise"
    kinds = {str(row["kind"]) for row in rows}
    if "llm_call" not in kinds:
        return (
            "no 'llm_call' event; the team calls a model, so a trace that misses it "
            "is the missing span from session 9"
        )
    if not any(str(row["detail"]).strip() for row in rows):
        return "every 'detail' is blank; the kind says what happened, the detail says which one"
    return None


@register("project-04-e2")
def _cases(cases: Any) -> str | None:
    """Step 2: the golden set, taken from the labelled questions rather than invented."""
    rows = _rows(cases)
    if rows is None:
        return (
            "pass the cases from step 2, a list of {'question': ..., 'expected_company': ...}: "
            "check_step('project-04-e2', cases)"
        )
    if not _has(rows, "question", "expected_company"):
        return (
            "every case needs 'question' and 'expected_company'; "
            "a case without a label cannot be graded"
        )
    if len(rows) < MIN_CASES:
        return (
            f"{len(rows)} case(s); use at least {MIN_CASES} so one lucky answer "
            "cannot move the rate"
        )
    known = set(companies().values())
    unknown = sorted({str(row["expected_company"]) for row in rows} - known)
    if unknown:
        return (
            f"expected_company {unknown} is in no source; the label has to name "
            "a company the corpus holds"
        )
    if len({str(row["question"]) for row in rows}) != len(rows):
        return "two cases share a question; a duplicate counts one answer twice"
    return None


@register("project-04-e3")
def _report(report: Any) -> str | None:
    """Step 3: one outcome per case, each carrying the reason it passed or failed."""
    rows = _rows(report)
    if rows is None:
        return (
            "pass the report from step 3, a list of "
            "{'question': ..., 'passed': ..., 'reason': ...}: "
            "check_step('project-04-e3', report)"
        )
    if not _has(rows, "question", "passed", "reason"):
        return (
            "every outcome needs 'question', 'passed' and 'reason'; "
            "a bare true or false is not a result you can act on"
        )
    if not all(isinstance(row["passed"], bool) for row in rows):
        return (
            "'passed' must be True or False, not a score; the pass condition is "
            "a decision you wrote down"
        )
    if len(rows) < MIN_CASES:
        return (
            f"{len(rows)} outcome(s) for at least {MIN_CASES} cases; grade every case, "
            "including the ones you expect to fail"
        )
    if all(row["passed"] for row in rows):
        return (
            "every case passed on the first run. Either the pass condition accepts anything, "
            "or the set is too easy to teach you where the fix goes. "
            "Check one by hand against its trace"
        )
    unexplained = [row for row in rows if not row["passed"] and not str(row["reason"]).strip()]
    if unexplained:
        return (
            f"{len(unexplained)} failure(s) carry no reason; a red case without "
            "a reason is an investigation, not a result"
        )
    return None


@register("project-04-e4")
def _buckets(buckets: Any) -> str | None:
    """Step 4: the failures sorted into named buckets, because the bucket is the work item."""
    if not isinstance(buckets, Mapping):
        return (
            "pass the buckets from step 4, a dict of bucket name -> how many failures: "
            "check_step('project-04-e4', buckets)"
        )
    if not buckets:
        return (
            "no buckets; if nothing failed, the set is too easy, and if something did, "
            "name where the fix goes"
        )
    unknown = sorted({str(name) for name in buckets} - set(FAILURE_BUCKETS))
    if unknown:
        return (
            f"bucket {unknown} is not one of {list(FAILURE_BUCKETS)}; "
            "an invented bucket hides which fix it needs"
        )
    if not all(
        isinstance(count, int) and not isinstance(count, bool) for count in buckets.values()
    ):
        return "every value must be a whole number of failures"
    if any(count < 0 for count in buckets.values()):
        return "a bucket cannot hold a negative number of failures"
    if sum(buckets.values()) < 1:
        return "the counts add to zero; every failure in the report belongs to exactly one bucket"
    return None


def labelled_questions() -> list[dict[str, str]]:
    """The 20 labelled questions as case rows, so the golden set is read, not typed.

    Project 03 already routes these and knows the right company for each. Reusing
    them means the golden set carries a label somebody checked, and it keeps the
    two projects grading the same corpus.
    """
    names = companies()
    rows = []
    for item in questions():
        ticker = str(item.get("company", "")).lower()
        company = names.get(ticker)
        if company:
            rows.append({"question": str(item["question"]), "expected_company": company})
    return rows
