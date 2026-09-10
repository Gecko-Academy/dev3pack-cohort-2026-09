"""Session 5: the deterministic mini-agent.

`ch05-e1` lives in `checks.py` and judges the budget traces of
:func:`bootcamp_agent.agent.answer_question`. This module adds `ch05-e2`, which
judges the loop the learner writes: `run_loop(plan, tools, budget)`.

WHY A SCRIPTED PLAN. A real loop asks a model what to call next, so its exits
are only reachable when the model happens to choose them. `plan` is that
sequence written down, which makes every exit reachable on purpose and the
whole check deterministic and model-free. The learner's job is the part that is
theirs in production too: the budget, the repetition guard, and the refusal.

The four scenarios below are the four rows of the exit table:

  answered       a plan that ends in an `answer` step
  repeated_call  the same tool with the same arguments, back to back
  budget         a plan longer than the budget it was given
  tool_error     a tool that raises instead of returning

Tools are built fresh per scenario and record every call, so the check can tell
"the loop stopped" from "the loop kept going and reported otherwise".
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from bootcamp_agent.checks import register
from bootcamp_agent.tools import ToolError

#: The only four values `stopped_because` may take.
STOP_REASONS = ("answered", "budget", "repeated_call", "tool_error")

#: Every receipt carries all four keys, on every exit.
RECEIPT_KEYS = ("steps", "stopped_because", "answer", "refusal")

Call = tuple[str, dict[str, Any]]


def _tools(calls: list[Call]) -> dict[str, Callable[..., str]]:
    """A recording `lookup` and a `broken` that refuses. `calls` is the tape."""

    def lookup(**args: Any) -> str:
        calls.append(("lookup", dict(args)))
        return f"lookup says: {args.get('q')}"

    def broken(**args: Any) -> str:
        calls.append(("broken", dict(args)))
        raise ToolError("broken: the upstream service stopped answering")

    return {"lookup": lookup, "broken": broken}


def _shape(receipt: Any, scenario: str) -> str | None:
    """The receipt contract, checked before anything is read out of it."""
    if not isinstance(receipt, dict):
        return (
            f"{scenario}: run_loop returned {type(receipt).__name__}; "
            f"hint: return a receipt dict with the keys {RECEIPT_KEYS}"
        )
    missing = [key for key in RECEIPT_KEYS if key not in receipt]
    if missing:
        return (
            f"{scenario}: the receipt is missing {missing}; "
            "hint: build all four keys on every exit, not only the happy one"
        )
    if receipt["stopped_because"] not in STOP_REASONS:
        return (
            f"{scenario}: stopped_because={receipt['stopped_because']!r}; "
            f"hint: it must be one of {STOP_REASONS}"
        )
    steps = receipt["steps"]
    if not isinstance(steps, list):
        return f"{scenario}: 'steps' must be a list; hint: append one dict per executed tool call"
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or set(step) != {"tool", "args", "result"}:
            return (
                f"{scenario}: steps[{index}] is {step!r}; "
                "hint: each step is {'tool': ..., 'args': ..., 'result': ...}"
            )
    return None


def _refusal_problem(receipt: dict[str, Any], scenario: str) -> str | None:
    """Every exit that is not an answer owes the caller a readable reason."""
    if receipt["answer"] is not None:
        return (
            f"{scenario}: stopped_because={receipt['stopped_because']!r} but answer is "
            f"{receipt['answer']!r}; hint: only an 'answer' step sets answer"
        )
    refusal = receipt["refusal"]
    if not isinstance(refusal, str) or not refusal.strip():
        return (
            f"{scenario}: refusal is {refusal!r}; "
            "hint: write one sentence the caller can read, saying why the loop stopped"
        )
    return None


def _run(run_loop: Any, scenario: str, *args: Any, **kwargs: Any) -> Any:
    """Call the learner's loop; a raised exception is that scenario's failure."""
    try:
        return run_loop(*args, **kwargs)
    except Exception as error:  # noqa: BLE001 - an escaping error is the bug under test
        return f"{scenario}: run_loop raised {type(error).__name__}: {error}"


def _answered(run_loop: Any) -> str | None:
    scenario = "the answered plan"
    calls: list[Call] = []
    plan = [
        {"tool": "lookup", "args": {"q": "budgets"}},
        {"tool": "answer", "args": {"text": "A budget is the loop's hard stop."}},
    ]
    receipt = _run(run_loop, scenario, plan, _tools(calls))
    if isinstance(receipt, str):
        return receipt
    if problem := _shape(receipt, scenario):
        return problem
    if receipt["stopped_because"] != "answered":
        return (
            f"{scenario}: stopped_because={receipt['stopped_because']!r}; "
            "hint: an 'answer' step ends the loop with stopped_because='answered'"
        )
    if receipt["answer"] != "A budget is the loop's hard stop.":
        return (
            f"{scenario}: answer={receipt['answer']!r}; "
            "hint: the answer is the answer step's args['text'], copied through"
        )
    if receipt["refusal"] is not None:
        return f"{scenario}: refusal={receipt['refusal']!r}; hint: an answered run refuses nothing"
    steps = receipt["steps"]
    if len(steps) != 1 or steps[0]["tool"] != "lookup" or steps[0]["args"] != {"q": "budgets"}:
        return (
            f"{scenario}: steps={steps!r}; hint: record the tool calls only — "
            "the answer step is a decision, not a call"
        )
    if not isinstance(steps[0]["result"], str) or not steps[0]["result"]:
        return (
            f"{scenario}: steps[0]['result']={steps[0]['result']!r}; "
            "hint: store what the tool returned, not True or None"
        )
    if calls != [("lookup", {"q": "budgets"})]:
        return (
            f"{scenario}: the tools were called {calls!r}; "
            "hint: execute one planned call at a time, with tools[name](**args)"
        )
    return None


def _repeated(run_loop: Any) -> str | None:
    scenario = "the repeated plan"
    calls: list[Call] = []
    same = {"tool": "lookup", "args": {"q": "same question"}}
    receipt = _run(run_loop, scenario, [dict(same), dict(same), dict(same)], _tools(calls))
    if isinstance(receipt, str):
        return receipt
    if problem := _shape(receipt, scenario):
        return problem
    if receipt["stopped_because"] != "repeated_call":
        return (
            f"{scenario}: stopped_because={receipt['stopped_because']!r}; "
            "hint: compare each planned call with the one before it, and stop when "
            "the tool and the arguments both match"
        )
    if problem := _refusal_problem(receipt, scenario):
        return problem
    if not 1 <= len(receipt["steps"]) <= 2:
        return (
            f"{scenario}: {len(receipt['steps'])} steps recorded; "
            "hint: stop on the second identical call, so at most two are ever recorded"
        )
    if len(calls) != len(receipt["steps"]):
        return (
            f"{scenario}: {len(calls)} tool calls executed but {len(receipt['steps'])} recorded; "
            "hint: record every call you execute, and execute none you did not record"
        )
    return None


def _budget(run_loop: Any) -> str | None:
    scenario = "the over-budget plan"
    calls: list[Call] = []
    plan = [{"tool": "lookup", "args": {"q": f"step {n}"}} for n in range(4)]
    receipt = _run(run_loop, scenario, plan, _tools(calls), budget=2)
    if isinstance(receipt, str):
        return receipt
    if problem := _shape(receipt, scenario):
        return problem
    if receipt["stopped_because"] != "budget":
        return (
            f"{scenario}: a 4-step plan under budget=2 stopped_because="
            f"{receipt['stopped_because']!r}; hint: stop before the call that would "
            "exceed the budget"
        )
    if problem := _refusal_problem(receipt, scenario):
        return problem
    if len(receipt["steps"]) != 2:
        return (
            f"{scenario}: {len(receipt['steps'])} steps recorded under budget=2; "
            "hint: the budget is a count of executed calls, and it is exact"
        )
    if calls != [("lookup", {"q": "step 0"}), ("lookup", {"q": "step 1"})]:
        return (
            f"{scenario}: the tools were called {calls!r}; "
            "hint: the third call must never reach the tool"
        )
    return None


def _tool_error(run_loop: Any) -> str | None:
    scenario = "the failing-tool plan"
    calls: list[Call] = []
    plan = [
        {"tool": "broken", "args": {"q": "anything"}},
        {"tool": "lookup", "args": {"q": "never reached"}},
    ]
    receipt = _run(run_loop, scenario, plan, _tools(calls))
    if isinstance(receipt, str):
        return receipt
    if problem := _shape(receipt, scenario):
        return problem
    if receipt["stopped_because"] != "tool_error":
        return (
            f"{scenario}: stopped_because={receipt['stopped_because']!r}; "
            "hint: catch ToolError around the call and end the run with 'tool_error'"
        )
    if problem := _refusal_problem(receipt, scenario):
        return problem
    if "broken" not in receipt["refusal"]:
        return (
            f"{scenario}: refusal={receipt['refusal']!r}; "
            "hint: name the tool that failed, so the caller knows what to fix"
        )
    if len(receipt["steps"]) > 1:
        return (
            f"{scenario}: {len(receipt['steps'])} steps recorded; "
            "hint: a call that raised produced no result to record"
        )
    if any(name == "lookup" for name, _ in calls):
        return (
            f"{scenario}: the tools were called {calls!r}; "
            "hint: a failed tool ends the run — do not carry on to the next planned call"
        )
    return None


@register("ch05-e2")
def _ch05_e2(run_loop: Any) -> str | None:
    """The loop stops safely: answered, repeated_call, budget, tool_error."""
    if not callable(run_loop):
        return "pass the run_loop function itself, not the result of calling it"
    for scenario in (_answered, _repeated, _budget, _tool_error):
        if problem := scenario(run_loop):
            return problem
    return None
