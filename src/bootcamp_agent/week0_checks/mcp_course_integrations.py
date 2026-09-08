"""Checkers for Course B, unit 11: a database, an API, and somebody else's server.

Two of the three exercises hand over the path to a server file, and the checks
read it twice. First with `ast`, because the two mistakes this unit exists to
prevent are both invisible at runtime on a well-behaved input: an f-string
query answers correctly right up to the day somebody sends a quote, and a key
in a tool's parameter list works perfectly while leaking the credential to
every client. Then over the wire, with the same `probe` unit 9 uses, because a
server that parses is not a server that answers.

The third exercise is prose, and it is checked as prose: the placeholders have
to be gone, the sentences have to be sentences, and the surface-area answer has
to carry the number it claims to be about.

NOTHING HERE GOES ON THE NETWORK. The hosted surface is a recorded tool list in
`fixtures/orquestra-tools.json`, read from disk. Session 13 connects to the real
one.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from bootcamp_agent.checks import register
from bootcamp_agent.week0_checks.fast_lane import _unwritten
from bootcamp_agent.week0_checks.mcp_course import (
    NEW_YORK_TO_TOKYO,
    _function,
    _is_decorator,
    _server_file,
    expected_conversion,
    probe,
    zone_list,
)

UNIT_11 = (
    Path(__file__).resolve().parents[3]
    / "modules"
    / "module-0"
    / "unit-11-mcp-data-apis-third-party"
)
ORQUESTRA_TOOLS = UNIT_11 / "fixtures" / "orquestra-tools.json"

#: The value that turns the starter's f-string query into two queries. It is a
#: teaching payload: it reads the table it was already allowed to read, and adds
#: a row that was never in it.
INJECTION = "' UNION SELECT 'pwned' --"

#: The environment variable the deck's API tool reads its credential from.
KEY_VARIABLE = "TIMEZONE_API_KEY"

_SELECT = re.compile(r"\bselect\b", re.IGNORECASE)

#: A string literal that looks like a credential. Deliberately narrow: it is
#: only ever applied inside a tool's body, where a filesystem path does not live.
_KEY_LITERAL = re.compile(
    r"(?:sk|pk|api[_-]?key|apikey|token|secret|bearer)[-_][A-Za-z0-9]{8,}"
    r"|\b(?=[A-Za-z0-9_]*\d)[A-Za-z0-9_]{24,}\b",
    re.IGNORECASE,
)
_KEYISH_NAME = re.compile(r"(?i)(key|token|secret|credential|password)")


def hosted_tools() -> list[str]:
    """The tool names recorded from the hosted surface. Read from disk, never fetched."""
    return list(json.loads(ORQUESTRA_TOOLS.read_text(encoding="utf-8"))["tools"])


def _parse(path: Path) -> ast.AST | str:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as error:
        return f"the server file does not parse: line {error.lineno}: {error.msg}"


def _tool(tree: ast.AST, name: str) -> ast.FunctionDef | str:
    function = _function(tree, name)
    if function is None:
        return f"the file defines no function called {name}"
    if not any(_is_decorator(item, "tool") for item in function.decorator_list):
        return f"{name} is not decorated with @mcp.tool(), so the server has no such tool"
    return function


# ======================================== unit 11 · lesson 1: the database


def _literal_strings(node: ast.AST) -> list[str]:
    return [
        inner.value
        for inner in ast.walk(node)
        if isinstance(inner, ast.Constant) and isinstance(inner.value, str)
    ]


def _looks_like_sql(node: ast.AST) -> bool:
    """True when any literal part of this node reads like a query."""
    return any(_SELECT.search(text) for text in _literal_strings(node))


def _interpolated_sql(function: ast.FunctionDef) -> str | None:
    """The complaint about SQL built by interpolation, or None if there is none."""
    advice = (
        "Send the value beside the query instead of inside it: "
        'conn.execute("... LIKE ? LIMIT 50", (f"%{prefix}%",))'
    )
    for node in ast.walk(function):
        if isinstance(node, ast.JoinedStr) and _looks_like_sql(node):
            return (
                "the query is an f-string, so whatever the caller sent is part of the SQL. "
                "The tool answers correctly for 'Europe' and answers something else entirely "
                f"for {INJECTION!r}. {advice}"
            )
        if isinstance(node, ast.BinOp) and _looks_like_sql(node):
            if isinstance(node.op, ast.Mod):
                return f"the query is built with %, which puts the caller's text in it. {advice}"
            if isinstance(node.op, ast.Add):
                return (
                    "the query is built by concatenation, which puts the caller's text in it. "
                    f"{advice}"
                )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "format"
            and _looks_like_sql(node.func.value)
        ):
            return f"the query is built with .format(), which is interpolation too. {advice}"
    return None


def _execute_calls(function: ast.FunctionDef) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("execute", "executemany")
    ]


@register("w11-e1")
def _w11_e1(path: object) -> str | None:
    """A lookup tool whose query is parameterised, and which still answers correctly."""
    problem = _server_file(path)
    if problem:
        return problem
    assert isinstance(path, Path)
    tree = _parse(path)
    if isinstance(tree, str):
        return tree
    function = _tool(tree, "lookup_locations")
    if isinstance(function, str):
        return function
    params = [item.arg for item in function.args.args]
    if params != ["prefix"]:
        return f"the tool takes one argument, prefix; got {params}"

    interpolated = _interpolated_sql(function)
    if interpolated:
        return interpolated
    queries = [text for text in _literal_strings(function) if _SELECT.search(text)]
    if not queries:
        return "the tool runs no SELECT; it has to ask the locations table something"
    if not any("?" in text for text in queries):
        return (
            "the query has no ? in it. A parameterised query names a placeholder and hands "
            "the value over separately, so the database never parses it as SQL"
        )
    calls = _execute_calls(function)
    if not calls:
        return "nothing in the tool calls execute(), so no query runs"
    if not any(len(call.args) >= 2 or call.keywords for call in calls):
        return (
            "execute() was handed the query and nothing else. The values go in a second "
            'argument, as a tuple: conn.execute(sql, (f"%{prefix}%",))'
        )

    report = probe(path, {"tool": "lookup_locations", "arguments": {"prefix": "Europe"}})
    if isinstance(report, str):
        return report
    if report.get("is_error"):
        return f"the tool answered with an error: {str(report.get('text', ''))[:160]}"
    found = [line.strip() for line in str(report.get("text", "")).splitlines() if line.strip()]
    expected = [zone for zone in zone_list() if zone.startswith("Europe/")]
    if found != expected:
        return f"prefix='Europe' should answer exactly {expected}; got {found}"

    attack = probe(path, {"tool": "lookup_locations", "arguments": {"prefix": INJECTION}})
    if isinstance(attack, str):
        return attack
    if "pwned" in str(attack.get("text", "")):
        return (
            f"the tool still answers 'pwned' for prefix={INJECTION!r}, so the value is part of "
            "the SQL somewhere. A parameterised query matches it as text, and matches nothing"
        )
    return None


# ======================================== unit 11 · lesson 2: the API key


def _reads_environ(node: ast.AST) -> bool:
    """True when this expression reads a process environment variable."""
    for inner in ast.walk(node):
        if isinstance(inner, ast.Attribute) and inner.attr == "environ":
            return True
        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
            if inner.func.attr == "getenv":
                return True
    return False


def _env_bound_names(function: ast.FunctionDef) -> set[str]:
    """The local names assigned from an environment read."""
    names: set[str] = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and _reads_environ(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def _names_in(node: ast.AST) -> set[str]:
    return {inner.id for inner in ast.walk(node) if isinstance(inner, ast.Name)}


def _hardcoded_key(tree: ast.AST, function: ast.FunctionDef) -> str | None:
    """A credential written into the source, either in the tool or in a module constant."""
    for text in _literal_strings(function):
        if _KEY_LITERAL.search(text):
            return (
                f"{text[:24]!r} in the tool body reads like a credential. A key in the source "
                "is a key in the repository, and `.env` is gitignored for exactly this reason"
            )
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
            continue
        if not isinstance(node.value.value, str) or len(node.value.value) < 8:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and _KEYISH_NAME.search(target.id):
                return (
                    f"{target.id} is a hardcoded credential. Read it from the environment at "
                    f"call time: os.environ.get({KEY_VARIABLE!r})"
                )
    return None


@register("w11-e2")
def _w11_e2(path: object) -> str | None:
    """A tool whose credential comes from the environment and reaches nobody else."""
    problem = _server_file(path)
    if problem:
        return problem
    assert isinstance(path, Path)
    tree = _parse(path)
    if isinstance(tree, str):
        return tree
    function = _tool(tree, "convert_timezone")
    if isinstance(function, str):
        return function

    params = [item.arg for item in function.args.args]
    leaked = [name for name in params if _KEYISH_NAME.search(name)]
    if leaked:
        return (
            f"{leaked[0]!r} is a tool parameter, so it is in the tool's input schema, which "
            "means every client can see that it must supply a credential, and does. The "
            "client never sends, receives or holds the key: the server reads it itself"
        )
    wanted = ["date_time", "from_timezone", "to_timezone"]
    if params != wanted:
        return f"the tool takes {wanted}; got {params}"

    hardcoded = _hardcoded_key(tree, function)
    if hardcoded:
        return hardcoded

    if not _reads_environ(function):
        return (
            "nothing in the tool reads the environment. The key lives outside the code, in "
            f"the process environment or a .env file: os.environ.get({KEY_VARIABLE!r})"
        )

    secrets = _env_bound_names(function) | {name for name in params if _KEYISH_NAME.search(name)}
    for node in ast.walk(function):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        exposed = sorted(secrets & _names_in(node.value))
        if exposed:
            return (
                f"the tool returns {exposed[0]!r} to the caller. A tool result goes to the "
                "client and into the model's context, so a key in a result is a key published"
            )

    report = probe(path, {"tool": "convert_timezone", "arguments": NEW_YORK_TO_TOKYO})
    if isinstance(report, str):
        return report
    if report.get("is_error"):
        return (
            "the tool answered with an error rather than a conversion: "
            f"{str(report.get('text', ''))[:160]}"
        )
    text = str(report.get("text", ""))
    converted = expected_conversion(**NEW_YORK_TO_TOKYO)
    if converted not in text:
        # A stdio child gets a filtered environment, so the key is absent here on
        # purpose: the tool has to work unauthenticated rather than crash.
        return (
            f"the conversion should read {converted}; got {text[:120]!r}. With no key in the "
            "environment the tool still converts: a missing credential is a header you leave "
            "off, not an exception"
        )
    return None


# ======================================== unit 11 · lesson 3: somebody else's server

_QUESTIONS = {
    "trust": (
        "who wrote it, who runs it, and what it calls when you are not watching. The deck's "
        "own question: the server runs code and may reach external APIs, so check the source"
    ),
    "security": (
        "what private data and which credentials the surface would be able to reach through "
        "you, and what it never needs"
    ),
    "surface_area": (
        "how many tools it exposes, because more tools is more the model can choose to do. "
        "Name the number the recorded fixture lists"
    ),
}


@register("w11-e3")
def _w11_e3(answers: object) -> str | None:
    """The deck's three questions, applied to a surface you did not write."""
    if not isinstance(answers, dict):
        return f"expected a dict with the keys {sorted(_QUESTIONS)}"
    missing = sorted(set(_QUESTIONS) - set(answers))
    if missing:
        return f"missing {missing}; the three questions are {sorted(_QUESTIONS)}"
    extra = sorted(set(answers) - set(_QUESTIONS))
    if extra:
        return f"{extra} is not one of the three questions {sorted(_QUESTIONS)}"
    for question, about in _QUESTIONS.items():
        answer = answers[question]
        if not isinstance(answer, str):
            return f"{question!r} needs a sentence, as a string"
        if _unwritten(answer, minimum=40):
            return f"{question!r} is still a placeholder. Write one sentence about {about}"
        if len(answer) > 400:
            return (
                f"{question!r} is {len(answer)} characters. One sentence you would say out "
                "loud, not a paragraph: if it does not fit, you have not decided yet"
            )
        if answer.strip()[-1] not in ".!?":
            return f"{question!r} is not a finished sentence; it needs an end"
    count = str(len(hosted_tools()))
    if count not in answers["surface_area"]:
        return (
            f"'surface_area' does not say how large the surface is. The recorded list holds "
            f"{count} tools; name that number, and say what it means that a model can pick "
            "any of them"
        )
    return None
