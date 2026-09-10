"""Checkers for Week 0, the prerequisite track.

Week 0 is self-paced and runs before session 1. Its job is a common floor: the
environment the course assumes, enough Python to read the typed contracts the
course uses, and one honest encounter with a real API.

Registered into the same `CHECKS` dict as everything else, so `check()` and
`review()` work unchanged — the pattern `depth_checks.py` already proved. Ids are
`w0N-eN`, so `review("w04")` scores unit 4.

UNIT 4 IS THE ONE WORTH EXPLAINING. It uses two live public APIs, both keyless:

  Frankfurter   api.frankfurter.dev, exchange rates. No key, no signup, and the
                docs and the endpoint agree with each other.
  Jupiter       api.jup.ag/tokens/v2, Solana token data. Its published OpenAPI
                declares `ApiKeyAuth` on all four paths, and all four answered
                200 with no key at all on 2026-09-04.

That second one is not a defect and the checker refuses to let a learner call it
one. A public read API being keyless is a product choice, and keys plausibly
gate rate tiers rather than access. The lesson is narrower and more useful: a
spec's security block records what somebody documented, not what the endpoint
enforces. An agent that reads only the spec asks for a key it does not need.

Every exercise runs against dated fixtures under the unit's `fixtures/`, so the
notebook executes offline and in CI. The live calls are an opt-in cell.
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bootcamp_agent.checks import register
from bootcamp_agent.curriculum import unit_by_prefix

REPO_ROOT = Path(__file__).resolve().parents[3]
UNIT_04 = unit_by_prefix("w04").directory / "fixtures"

_PLACEHOLDERS = ("", "...", "todo", "tbd", "n/a", "na", "none", "-", "?", "yes", "no")


def _unwritten(text: object, minimum: int = 20) -> bool:
    if not isinstance(text, str):
        return True
    stripped = text.strip()
    return stripped.lower() in _PLACEHOLDERS or len(stripped) < minimum


def _fixture(name: str) -> dict:
    return json.loads((UNIT_04 / f"{name}.json").read_text())


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


# ======================================== unit 04 · calling a real API


@register("w04-e1")
def _w04_e1(url: object) -> str | None:
    """Build the call from the documentation, and get it right the first time."""
    if not isinstance(url, str) or not url.strip():
        return "expected the full URL as a string"
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        return "https, not http. A rate you cannot trust in transit is not a rate"
    if parsed.netloc != "api.frankfurter.dev":
        return f"host should be api.frankfurter.dev, got {parsed.netloc!r}"
    if parsed.path.rstrip("/") != "/v1/latest":
        return (
            f"path should be /v1/latest, got {parsed.path!r}. /v1/latest is today's rate; "
            "a date in the path is the historical endpoint"
        )
    query = parse_qs(parsed.query)
    base = (query.get("base") or [""])[0].upper()
    if base != "USD":
        return f"the question asks what one US dollar buys, so base=USD, not {base or 'unset'!r}"
    symbols = {s.strip().upper() for s in (query.get("symbols") or [""])[0].split(",") if s.strip()}
    if "BRL" not in symbols:
        return "symbols must include BRL; without it you get every currency and pay for the noise"
    return None


@register("w04-e2")
def _w04_e2(reading: object) -> str | None:
    """Read the response, including the two things people skip: the date, and the direction."""
    problem = _keys_are(reading, ("usd_to_brl", "as_of", "one_brl_in_usd"))
    if problem:
        return problem
    assert isinstance(reading, dict)
    recorded = _fixture("frankfurter-latest")["response"]
    expected_rate = recorded["rates"]["BRL"]
    expected_date = recorded["date"]

    for field in ("usd_to_brl", "one_brl_in_usd"):
        if not isinstance(reading[field], (int, float)):
            return f"{field!r} is a number"
    if abs(reading["usd_to_brl"] - expected_rate) > 1e-6:
        return f"'usd_to_brl' should be {expected_rate}, read from the recorded response"
    if str(reading["as_of"]).strip() != expected_date:
        return (
            f"'as_of' should be {expected_date!r}. The response carries its own date, and a rate "
            "without one is a number you cannot defend later"
        )
    inverse = 1 / expected_rate
    if abs(reading["one_brl_in_usd"] - inverse) > 1e-4:
        # Fires for any wrong value, so it must not assert WHY it is wrong. It
        # names the commonest cause and gives the number.
        return f"'one_brl_in_usd' is wrong. A rate has a direction, so invert it: {inverse:.6f}"
    return None


@register("w04-e3")
def _w04_e3(verdict: object) -> str | None:
    """The spec said one thing and the endpoint did another. What follows from that?"""
    problem = _keys_are(
        verdict, ("is_it_a_vulnerability", "what_a_spec_only_agent_does", "what_to_do_instead")
    )
    if problem:
        return problem
    assert isinstance(verdict, dict)

    if verdict["is_it_a_vulnerability"] is not False:
        return (
            "No. A public read API answering without a key is a product choice, and keys "
            "plausibly gate rate tiers rather than access. Calling this a vulnerability is the "
            "mistake this exercise exists to prevent"
        )
    if _unwritten(verdict["what_a_spec_only_agent_does"], minimum=30):
        return (
            "'what_a_spec_only_agent_does': the spec declares ApiKeyAuth on every path, so an "
            "agent that reads only the spec concludes it needs something. Say what that costs"
        )
    plan = str(verdict["what_to_do_instead"])
    if _unwritten(plan, minimum=30):
        return "'what_to_do_instead' needs a real sentence"
    # Stems, not whole words: "probing" does not contain "probe", which the
    # reference solution discovered the hard way.
    finding_out = ("prob", "verif", "test", "try", "call", "check", "request", "measur")
    if not any(word in plan.lower() for word in finding_out):
        return (
            "'what_to_do_instead' should describe finding out rather than assuming. One request "
            "settled this in less time than reading the security section did"
        )
    return None


@register("w04-e4")
def _w04_e4(rows: object) -> str | None:
    """The declared-versus-actual table, read from the evidence rather than recalled."""
    recorded = _fixture("jupiter-declared-vs-actual")["paths"]
    if not isinstance(rows, list):
        return "expected a list of the paths where the spec and the endpoint disagree"
    named = {str(row).strip() for row in rows}
    expected = {row["path"] for row in recorded if row["keyless_status"] == 200}
    if named != expected:
        missing = sorted(expected - named)
        extra = sorted(named - expected)
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if extra:
            detail.append(f"{extra} is not in the evidence")
        return "; ".join(detail) + ". Read the fixture, do not recall it"
    return None


# ======================================== unit 01 · the environment


def _run_with_deadline(
    function, argument: object, seconds: float
) -> tuple[bool, dict[str, object]]:
    """Call `function(argument)` with a deadline; (finished, {"value" | "error"}).

    A forked child is used where fork exists, because a loop that never stops
    can be terminated there and leaves nothing behind. A thread cannot be
    stopped: the first version of this checker left a runaway loop spinning at
    100% CPU inside the learner's kernel for the rest of the session. The thread
    is kept only as the fallback on platforms without fork.
    """
    import multiprocessing

    if "fork" in multiprocessing.get_all_start_methods():
        context = multiprocessing.get_context("fork")
        receiver, sender = context.Pipe(duplex=False)

        def _child() -> None:
            try:
                sender.send({"value": function(argument)})
            except Exception as error:  # noqa: BLE001
                sender.send({"error": f"{type(error).__name__}: {error}"})

        child = context.Process(target=_child, daemon=True)
        child.start()
        sender.close()
        child.join(timeout=seconds)
        if child.is_alive():
            child.terminate()
            child.join(timeout=1)
            return False, {}
        return True, (receiver.recv() if receiver.poll() else {})

    outcome: dict[str, object] = {}

    def _attempt() -> None:
        try:
            outcome["value"] = function(argument)
        except Exception as error:  # noqa: BLE001
            outcome["error"] = f"{type(error).__name__}: {error}"

    worker = threading.Thread(target=_attempt, daemon=True)
    worker.start()
    worker.join(timeout=seconds)
    return (not worker.is_alive()), outcome


@register("w01-e1")
def _w01_e1(reading: object) -> str | None:
    """Which Python is running, and where do its packages come from.

    Self-verifying: every expected value is read from the live interpreter, so
    the check cannot drift and cannot be satisfied by copying somebody else's
    answer from a different machine.
    """
    problem = _keys_are(reading, ("python_version", "in_repo_venv", "why_it_matters"))
    if problem:
        return problem
    assert isinstance(reading, dict)

    running = f"{sys.version_info.major}.{sys.version_info.minor}"
    if str(reading["python_version"]).strip() != running:
        return (
            f"'python_version' should be {running!r}, which is what is running this cell. "
            "Read it from sys.version_info rather than from what you installed"
        )
    inside = Path(sys.prefix).resolve() == (REPO_ROOT / ".venv").resolve()
    if reading["in_repo_venv"] is not inside:
        hint = (
            "the kernel IS the repo's .venv"
            if inside
            else "the kernel is NOT the repo's .venv, which is the commonest setup failure"
        )
        return f"'in_repo_venv' is wrong: {hint}. Compare sys.prefix with the repo's .venv"
    if _unwritten(reading["why_it_matters"], minimum=30):
        return (
            "'why_it_matters': say what breaks when the kernel is a different Python from "
            "the one uv installed into. You have probably already seen it"
        )
    return None


@register("w01-e2")
def _w01_e2(locate: object) -> str | None:
    """Find the repo root from anywhere, the way every notebook here does."""
    if not callable(locate):
        return "expected the locate_repo_root(start) function itself"
    try:
        found = locate(unit_by_prefix("w01").directory)
    except Exception as error:  # noqa: BLE001
        return f"raised {type(error).__name__}: {error}"
    if not isinstance(found, Path):
        return f"return a Path, got {type(found).__name__}"
    if found.resolve() != REPO_ROOT.resolve():
        return (
            f"walked to {found}, expected the repo root. Climb until you find pyproject.toml, "
            "and stop at the filesystem root so a wrong start cannot loop forever"
        )
    # It must TERMINATE on a path with no pyproject above it. The obvious
    # implementation is a `while` that never stops, and calling it directly
    # would hang this checker along with the learner's kernel — which is what
    # happened the first time this shipped. So the call runs with a deadline,
    # and an attempt still running after it IS the finding.
    finished, outcome = _run_with_deadline(locate, Path(tempfile.gettempdir()), seconds=5)
    if not finished:
        return (
            "it never stopped. Given a directory with no pyproject.toml above it, the loop "
            "climbs past the filesystem root forever, because the parent of '/' is '/'. "
            "Compare `here` with `here.parent` and stop when they are equal"
        )
    if "error" in outcome:
        return f"raised on a directory with no pyproject above it: {outcome['error']}"

    outside = outcome.get("value")
    if isinstance(outside, Path) and not (outside / "pyproject.toml").exists():
        if outside != Path(outside.anchor):
            return (
                f"returned {outside} for a directory with no pyproject above it. Either return "
                "None or stop at the filesystem root; do not return a directory that has none"
            )
    return None


@register("w01-e3")
def _w01_e3(groups: object) -> str | None:
    """Runtime dependency or dev tool. Getting this wrong ships a test runner."""
    truth = {"pytest": "dev", "ruff": "dev", "nbformat": "dev", "python-dotenv": "main"}
    if not isinstance(groups, dict) or set(groups) != set(truth):
        return f"expected one answer for each of {sorted(truth)}"
    for package, expected in truth.items():
        got = str(groups[package]).strip().lower()
        if got not in {"main", "dev"}:
            return f"{package!r}: answer 'main' or 'dev'"
        if got != expected:
            why = (
                "a user of the package needs it at run time"
                if expected == "main"
                else "only somebody working ON the package needs it, so it does not ship"
            )
            return f"{package!r} belongs in {expected!r}: {why}"
    return None


# ======================================== unit 02 · packages and documentation


@register("w02-e1")
def _w02_e1(names: object) -> str | None:
    """What a package actually exposes, read rather than guessed."""
    if not isinstance(names, list):
        return "expected a list of module names importable from bootcamp_agent"
    expected = {"agent", "checks", "documents", "evals", "llm", "retrieval", "schema", "tools"}
    got = {str(n).strip() for n in names}
    missing = sorted(expected - got)
    if missing:
        return f"missing {missing}. List the .py files in src/bootcamp_agent rather than recalling"
    invented = sorted(got - {p.stem for p in (REPO_ROOT / "src" / "bootcamp_agent").glob("*.py")})
    if invented:
        return f"{invented} is not in the package. Read the directory"
    return None


@register("w02-e2")
def _w02_e2(docstring: object) -> str | None:
    """A docstring that answers the two questions a caller actually has."""
    if not isinstance(docstring, str) or _unwritten(docstring, minimum=40):
        return "expected a docstring of at least 40 characters"
    lowered = docstring.lower()
    if "return" not in lowered:
        return "say what it RETURNS. A caller cannot use a function without knowing that"
    if "raise" not in lowered and "error" not in lowered:
        return (
            "say what it RAISES. An undocumented exception is the one nobody handles, and "
            "this package raises typed errors on purpose"
        )
    first = docstring.strip().splitlines()[0]
    if not first.endswith("."):
        return "the summary line is one sentence and ends with a full stop"
    return None


@register("w02-e3")
def _w02_e3(fixed: object) -> str | None:
    """The broken import, repaired. The stub ships wrong on purpose."""
    if not callable(fixed):
        return "expected the load_the_corpus() function itself"
    try:
        documents = fixed()
    except ModuleNotFoundError as error:
        return (
            f"still ModuleNotFoundError: {error}. `bootcamp_agent.documents` is the module; "
            "`documents` alone is not on the path"
        )
    except Exception as error:  # noqa: BLE001
        return f"raised {type(error).__name__}: {error}"
    if not isinstance(documents, list) or len(documents) != 6:
        got = len(documents) if isinstance(documents, list) else type(documents).__name__
        return f"expected the 6 corpus documents, got {got}"
    return None


# ======================================== unit 03 · classes and contracts


@register("w03-e1")
def _w03_e1(add_tag: object) -> str | None:
    """The mutable default argument. Two calls must not share one list.

    A function default, not a dataclass field: `tags: list = []` on a dataclass
    raises at class-definition time, so the stub could not run at all, and a
    stub that cannot run teaches nothing. The function version RUNS and returns
    the wrong answer on the second call, which is the whole point.
    """
    if not callable(add_tag):
        return "expected the add_tag function itself, not the result of calling it"
    try:
        first = add_tag("alpha")
        second = add_tag("beta")
    except Exception as error:  # noqa: BLE001
        return f"raised {type(error).__name__}: {error}"
    if not isinstance(first, list) or not isinstance(second, list):
        return "add_tag should return a list"
    if len(second) != 1 or second[0] != "beta":
        return (
            f"the second call returned {second}, so both calls shared one list. A default "
            "argument is evaluated ONCE, when the function is defined, not per call. Default "
            "to None and build the list inside"
        )
    if first != ["alpha"]:
        return f"the first call should return ['alpha'], got {first}"
    return None


@register("w03-e2")
def _w03_e2(frozen: object) -> str | None:
    """Frozen means the value cannot change under a caller who kept a reference."""
    if not callable(frozen):
        return "expected the class itself"
    try:
        instance = frozen(name="search", description="find things")
    except Exception as error:  # noqa: BLE001
        return f"could not build one with name= and description=: {type(error).__name__}: {error}"
    if getattr(instance, "name", None) != "search":
        return "the instance should carry the name it was built with"
    try:
        instance.name = "something else"
    except Exception:
        return None
    return (
        "the instance let its name be reassigned. Freeze it, so a tool definition cannot be "
        "edited by whoever holds a reference to it"
    )


@register("w03-e3")
def _w03_e3(verdict: object) -> str | None:
    """Why the answer type fails closed, read from the real schema."""
    problem = _keys_are(verdict, ("rejects_unknown_fields", "why_fail_closed"))
    if problem:
        return problem
    assert isinstance(verdict, dict)
    if verdict["rejects_unknown_fields"] is not True:
        return (
            "It does. parse_research_answer refuses a payload carrying a field the schema "
            "does not declare. Try it before answering"
        )
    if _unwritten(verdict["why_fail_closed"], minimum=40):
        return (
            "'why_fail_closed': say what would happen if an unknown field were accepted "
            "silently. Think about a model that invents a 'confidence_override'"
        )
    return None
