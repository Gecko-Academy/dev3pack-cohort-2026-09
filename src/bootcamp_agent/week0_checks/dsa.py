"""Checkers for Course C, unit 12: the data structures an agent loop is made of.

Every exercise here is checked by behaviour, on inputs the notebook does not
show. The timing exercise wants numbers that were measured, and refuses a pair
that a scan-versus-lookup measurement cannot produce. The dedupe function runs
on two citation lists whose first-seen orders differ, so `set()` cannot pass
both by luck. The tree walk runs on a tree that contains itself, under a
deadline, because a walk without a budget is the bug the exercise exists to
prevent. The topological sort runs on the fixture's edges in an order that
breaks insertion order, and on a cycle, where the only right answer is None.

The deadline helper is the one `fast_lane` wrote for the same reason: a learner
function that may never stop must not take the kernel down with it.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from bootcamp_agent.checks import register
from bootcamp_agent.week0_checks.fast_lane import _run_with_deadline

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = REPO_ROOT / "cookbook" / "fixtures" / "program-graph-example.json"

#: How many seconds a learner function gets before "it never stopped" is the verdict.
DEADLINE_SECONDS = 5.0


# ======================================== unit 12 · lesson 1: measure, then decide


@register("w12-e1")
def _w12_e1(timings: object) -> str | None:
    """A scan and a dict lookup, both timed, and the numbers must be a measurement."""
    if not isinstance(timings, dict) or set(timings) != {"linear_ms", "dict_ms", "label"}:
        return "expected a dict with exactly the keys 'linear_ms', 'dict_ms' and 'label'"
    if timings["label"] != "measured":
        return (
            f"label is {timings['label']!r}; it must be 'measured'. The number that tells "
            "you which world you are in is the one timeit printed, not the one you expected"
        )
    for key in ("linear_ms", "dict_ms"):
        value = timings[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"{key} must be a number of milliseconds, got {type(value).__name__}"
        if value <= 0:
            return (
                f"{key} is {value}; a timing of zero or less was not measured. Take "
                "min(timeit.repeat(...)), divide by number, and convert seconds to ms"
            )
    linear_ms = float(timings["linear_ms"])
    dict_ms = float(timings["dict_ms"])
    if dict_ms > linear_ms * 5:
        return (
            f"dict_ms ({dict_ms:.4f}) is more than five times linear_ms ({linear_ms:.4f}). A "
            "dict lookup that is slower than a scan means the wrong thing was timed: build "
            "the dict once, outside the timed statement, and time only index[target]"
        )
    if dict_ms * 10 > linear_ms:
        return (
            f"dict_ms ({dict_ms:.4f}) is not even ten times smaller than linear_ms "
            f"({linear_ms:.4f}). Over 60,000 ids a lookup is thousands of times faster than "
            "a scan, so the timed block did more than one lookup: build the index outside "
            "the statement, and scan the scaled list, not the six real documents"
        )
    return None


# ======================================== unit 12 · lesson 2: list, dict, set

#: Two citation lists whose first-seen orders differ. A set iterates in one
#: hash-determined order per process, so it can match at most one of them.
_CITATION_RUNS: tuple[list[str], ...] = (
    [
        "rag-basics",
        "agent-loops",
        "rag-basics",
        "mcp-overview",
        "agent-loops",
        "prompt-injection",
        "rag-basics",
        "structured-outputs",
        "evaluation-basics",
        "mcp-overview",
    ],
    [
        "structured-outputs",
        "evaluation-basics",
        "structured-outputs",
        "prompt-injection",
        "rag-basics",
        "prompt-injection",
        "mcp-overview",
        "agent-loops",
        "rag-basics",
    ],
)


@register("w12-e2")
def _w12_e2(dedupe: object) -> str | None:
    """Deduplicate citations and keep the order they were first seen in."""
    if not callable(dedupe):
        return "expected the dedupe(citations) function itself, not its result"
    for citations in _CITATION_RUNS:
        expected = list(dict.fromkeys(citations))
        result = dedupe(list(citations))
        if not isinstance(result, list):
            return f"return a list of doc ids, got {type(result).__name__}"
        if len(result) != len(set(result)):
            return "the result still has duplicates; every doc id must appear once"
        if set(result) != set(expected):
            lost = sorted(set(expected) - set(result))
            extra = sorted(set(result) - set(expected))
            if lost:
                return (
                    f"{lost[0]!r} was cited but is missing from the result; drop repeats, not ids"
                )
            return f"{extra[0]!r} is in the result but was never cited"
        if result == sorted(expected) and expected != sorted(expected):
            return (
                "the result is sorted alphabetically; order matters, and the order is the one "
                "the citations were first seen in. Sorting is a different question"
            )
        if result != expected:
            return (
                "the ids are right but the order is not first-seen. set() forgets the order "
                "it received; dict.fromkeys(citations) keeps it, and so does a seen-set "
                "beside a list"
            )
    return None


# ======================================== unit 12 · lesson 3: stack, queue, recursion


def _tree(name: str, *children: dict) -> dict:
    return {"name": name, "children": list(children)}


def _chain(length: int) -> tuple[dict, list[str]]:
    """A tree that is one long path, deeper than any budget the check hands out."""
    names = [f"call-{index}" for index in range(length)]
    node: dict = _tree(names[-1])
    for name in reversed(names[:-1]):
        node = _tree(name, node)
    return node, names


def _walk_under_deadline(
    walk: Callable[..., object], tree: dict, budget: int
) -> tuple[bool, dict[str, object]]:
    return _run_with_deadline(lambda root: walk(root, budget), tree, seconds=DEADLINE_SECONDS)


@register("w12-e3")
def _w12_e3(walk: object) -> str | None:
    """walk(node, budget) visits names and STOPS when the budget is spent."""
    if not callable(walk):
        return "expected the walk(node, budget) function itself, not its result"

    small = _tree("answer", _tree("search", _tree("get_document")), _tree("search again"))
    finished, outcome = _walk_under_deadline(walk, small, 10)
    if not finished:
        return "it never stopped on a four-node tree; every child must be visited once, then return"
    if "error" in outcome:
        return f"raised on a four-node tree: {outcome['error']}"
    visited = outcome.get("value")
    if not isinstance(visited, list) or not all(isinstance(name, str) for name in visited):
        return "return the list of visited names, in the order they were visited"
    if visited[:1] != ["answer"]:
        return "the root must be the first name visited"
    if sorted(visited) != ["answer", "get_document", "search", "search again"]:
        return f"visited {visited}; with a budget of 10 every one of the four nodes is visited once"

    deep, names = _chain(50)
    finished, outcome = _walk_under_deadline(walk, deep, 10)
    if not finished:
        return "it never stopped on a tree fifty nodes deep with a budget of 10"
    if "error" in outcome:
        return f"raised on a tree fifty nodes deep: {outcome['error']}"
    visited = outcome.get("value")
    if not isinstance(visited, list) or len(visited) > 10:
        count = len(visited) if isinstance(visited, list) else "no"
        return (
            f"returned {count} names with a budget of 10 on a tree fifty nodes deep. The budget "
            "is a ceiling on visits: check it before you descend, and return when it is spent"
        )
    if visited != names[:10]:
        return (
            f"returned {len(visited)} names with a budget of 10 on a tree fifty nodes deep; "
            "the budget is a ceiling, not a reason to stop early. Visit until it is spent"
        )

    loop = _tree("loop")
    loop["children"].append(loop)
    finished, outcome = _walk_under_deadline(walk, loop, 5)
    if not finished:
        return (
            "it never stopped on a node whose children contain itself. A tool-call tree can "
            "loop, and the budget is what ends it: check len(visited) against budget before "
            "the recursive call"
        )
    if "error" in outcome:
        return (
            f"raised on a node whose children contain itself: {outcome['error']}. The budget "
            "must stop the walk before the interpreter does; check it before you descend"
        )
    visited = outcome.get("value")
    if not isinstance(visited, list) or len(visited) != 5:
        count = len(visited) if isinstance(visited, list) else "no"
        return f"returned {count} names on a self-referencing node with a budget of 5; expected 5"
    return None


# ======================================== unit 12 · lesson 4: trees, graphs, order


def fixture_edges(path: Path = FIXTURE) -> list[tuple[str, str]]:
    """The "derive X before Y" edges of the teaching fixture, first-seen order.

    A quoted seed such as `'store'` is a constant; nothing derives it, so it is
    not a node. Everything else an account is derived from, or read from, is.
    """
    fixture = json.loads(path.read_text(encoding="utf-8"))
    edges: list[tuple[str, str]] = []
    for instruction in fixture["instructions"]:
        for account in instruction["accounts"]:
            for seed in account.get("seeds", []):
                if not seed.startswith("'"):
                    edges.append((seed, account["name"]))
            for source in account.get("derived_from", []):
                edges.append((source, account["name"]))
            if "read_from" in account:
                edges.append((account["read_from"], account["name"]))
    return list(dict.fromkeys(edges))


_CYCLE: list[tuple[str, str]] = [("store", "item"), ("item", "mint"), ("mint", "store")]


def _order_under_deadline(
    derive_order: Callable[..., object], edges: list[tuple[str, str]]
) -> tuple[bool, dict[str, object]]:
    return _run_with_deadline(derive_order, list(edges), seconds=DEADLINE_SECONDS)


@register("w12-e4")
def _w12_e4(derive_order: object) -> str | None:
    """derive_order(edges): every edge respected, and None when the edges form a cycle."""
    if not callable(derive_order):
        return "expected the derive_order(edges) function itself, not its result"

    # Reversed, so that the order the nodes are first seen in breaks three edges.
    edges = list(reversed(fixture_edges()))
    nodes = {node for edge in edges for node in edge}
    finished, outcome = _order_under_deadline(derive_order, edges)
    if not finished:
        return "it never stopped on the fixture's six edges, which have no cycle"
    if "error" in outcome:
        return f"raised on the fixture's edges: {outcome['error']}"
    order = outcome.get("value")
    if not isinstance(order, list):
        return (
            f"return a list of account names for edges without a cycle, got {type(order).__name__}"
        )
    if len(order) != len(set(order)):
        return "the order lists a name twice; every node appears exactly once"
    if set(order) != nodes:
        missing = sorted(nodes - set(order))
        if missing:
            return f"{missing[0]!r} is in the edges but not in the order; every node must be placed"
        return f"{sorted(set(order) - nodes)[0]!r} is in the order but in none of the edges"
    position = {node: index for index, node in enumerate(order)}
    for before, after in edges:
        if position[before] > position[after]:
            return (
                f"the order puts {after!r} before {before!r}, but the edge says derive "
                f"{before!r} first. Insertion order is not derive order: place a node only "
                "when everything it needs has been placed"
            )

    finished, outcome = _order_under_deadline(derive_order, _CYCLE)
    if not finished:
        return (
            "it never stopped on edges that form a cycle (store -> item -> mint -> store). "
            "When no node is ready and nodes remain, that is the cycle: return None"
        )
    if "error" in outcome:
        return (
            f"raised on edges that form a cycle: {outcome['error']}. A cycle is a gap, not an "
            "error to raise: return None"
        )
    if outcome.get("value") is not None:
        return (
            "returned an order for edges that form a cycle (store -> item -> mint -> store). "
            "No order respects every edge there; a cycle is a gap, not an order: return None"
        )
    return None
