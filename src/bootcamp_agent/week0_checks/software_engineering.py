"""Checkers for Course A, units 5 and 6: packages, PyPI, PEP 8, and portability.

Every exercise here builds something real and the checker exercises it, never
its text: the PEP 8 file is re-linted by ruff and then RUN, the package the
learner writes is imported in a fresh interpreter, the dependency table is
parsed the way an installer would parse it. A learner who reads the checker
finds no string to paste.

Subprocesses are the honest way to test a package on disk. Importing the
learner's `my_package` into the kernel would cache the first attempt in
`sys.modules` and every later attempt would look like the first one. A child
interpreter starts empty every time and leaves nothing behind when it exits.
"""

from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

from bootcamp_agent.checks import register

#: The exact ruff invocation the notebook uses, so learner and checker agree.
#: `--isolated` ignores whatever pyproject sits above the temp file, `--preview`
#: turns on the pycodestyle E1/E2/E3 rules that a PEP 8 lesson is about.
RUFF_ARGS = ("--isolated", "--no-cache", "--preview", "--select", "E,W,F")

_PLACEHOLDERS = ("", "...", "todo", "tbd", "n/a", "none", "-", "?")


def _child(
    args: list[str], cwd: Path | None = None, timeout: float = 60
) -> subprocess.CompletedProcess:
    """Run a child interpreter that writes no bytecode and cannot outlive the check."""
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"},
    )


def ruff_violations(path: Path) -> list[dict]:
    """Every violation ruff finds in `path`, as dicts with `code`, `row`, `message`."""
    result = _child(
        [sys.executable, "-m", "ruff", "check", *RUFF_ARGS, "--output-format", "json", str(path)]
    )
    if not result.stdout.strip():
        return []
    return [
        {
            "code": item["code"],
            "row": item["location"]["row"],
            "column": item["location"]["column"],
            "message": item["message"],
        }
        for item in json.loads(result.stdout)
    ]


# ======================================== unit 05 · packages, PyPI and PEP 8


@register("w05-e1")
def _w05_e1(answer: object) -> str | None:
    """Read the signature that help() printed, not the one you remember."""
    if not isinstance(answer, tuple) or len(answer) != 2:
        return "expected a tuple of two strings: (function_name, first_parameter_name)"
    name, first = answer
    if not isinstance(name, str) or not isinstance(first, str):
        return "both items must be strings; the names as help() printed them"
    function = getattr(textwrap, name, None)
    if function is None or not callable(function) or name.startswith("_"):
        return f"textwrap has no public function called {name!r}; read the first line of help()"
    parameters = list(inspect.signature(function).parameters)
    if not parameters:
        return f"textwrap.{name} takes no parameters; pick one that does"
    if first != parameters[0]:
        return (
            f"the first parameter of textwrap.{name} is not {first!r}; the signature line "
            "help() prints lists the parameters in order, and the first one is the one"
        )
    return None


@register("w05-e2")
def _w05_e2(path: object) -> str | None:
    """PEP 8 until ruff is silent, and the script still prints what it printed."""
    if not isinstance(path, Path) or not path.is_file():
        return "expected the Path to the .py file the cell wrote"
    violations = ruff_violations(path)
    if violations:
        codes = sorted({item["code"] for item in violations})
        first = violations[0]
        return (
            f"ruff still reports {len(violations)} violation(s) ({', '.join(codes)}); the first "
            f"is line {first['row']}: {first['code']} {first['message']}"
        )
    run = _child([sys.executable, str(path)], timeout=10)
    if run.returncode != 0:
        last = (
            run.stderr.strip().splitlines()[-1] if run.stderr.strip() else f"exit {run.returncode}"
        )
        return f"the file no longer runs: {last}"
    if run.stdout.split() != ["[10,", "3,", "4,", "7]", "6"]:
        return (
            "the file lints clean but prints something different; style changes must not "
            "change behaviour, keep the data and both prints as they were"
        )
    return None


@register("w05-e3")
def _w05_e3(labels: object) -> str | None:
    """Package, class or method: the three shapes modular Python comes in."""
    truth = {
        "import collections": "package",
        "collections.Counter(words)": "class",
        "counts.most_common(2)": "method",
        "' '.join(words)": "method",
    }
    if not isinstance(labels, dict) or set(labels) != set(truth):
        return f"expected one label for each of the four snippets: {sorted(truth)}"
    allowed = {"package", "class", "method"}
    for snippet, expected in truth.items():
        got = str(labels[snippet]).strip().lower()
        if got not in allowed:
            return f"{snippet!r} is labelled {got!r}; use one of {sorted(allowed)}"
        if got != expected:
            reasons = {
                "package": "an import statement brings in a package, whatever it is called",
                "class": "a capitalised name called with arguments builds an instance of a class",
                "method": "a dot on an existing object, then a call, is a method of that object",
            }
            return f"{snippet!r} is not a {got}: {reasons[expected]}"
    return None


# ======================================== unit 06 · a portable package

_REQUIREMENT_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _requirement_name(requirement: str) -> str:
    match = _REQUIREMENT_NAME.match(requirement)
    return match.group(1).lower() if match else ""


@register("w06-e1")
def _w06_e1(table: object) -> str | None:
    """Which requirement pins an exact version, and which one floats."""
    if not isinstance(table, dict) or set(table) != {"requires", "exact", "floating"}:
        return "expected a dict with exactly the keys 'requires', 'exact' and 'floating'"
    requires = table["requires"]
    if not isinstance(requires, list) or len(requires) < 2:
        return "'requires' must be a list of at least two requirement strings"
    if any(not isinstance(item, str) or not _requirement_name(item) for item in requires):
        return "every entry in 'requires' must be a requirement string such as 'numpy==1.15.4'"
    exact = {_requirement_name(item) for item in requires if "==" in item}
    floating = {_requirement_name(item) for item in requires if "==" not in item}
    if not exact or not floating:
        return "'requires' needs at least one exact pin (==) and at least one entry without one"
    for key, truth in (("exact", exact), ("floating", floating)):
        given = table[key]
        if not isinstance(given, (list, tuple, set)):
            return f"'{key}' must be a list of package names"
        names = {str(item).strip().lower() for item in given}
        if names != truth:
            other = "floating" if key == "exact" else "exact"
            wrong = sorted(names - truth)
            missing = sorted(truth - names)
            if wrong:
                return (
                    f"{wrong[0]!r} is listed under '{key}' but its requirement is {other}: only "
                    "'==' pins an exact version; '>=' is a floor and a bare name is anything"
                )
            return f"{missing[0]!r} belongs under '{key}'; read its requirement string again"
    return None


_PROBE_PACKAGE = textwrap.dedent(
    """
    import contextlib, importlib, io, json
    report = {}
    try:
        import my_package
    except Exception as error:
        report["import_error"] = f"{type(error).__name__}: {error}"
    else:
        try:
            utils = importlib.import_module("my_package.utils")
            report["utils_has_it"] = callable(getattr(utils, "we_need_to_talk", None))
        except Exception as error:
            report["utils_error"] = f"{type(error).__name__}: {error}"
            utils = None
        top = getattr(my_package, "we_need_to_talk", None)
        report["top_has_it"] = callable(top)
        report["same_object"] = utils is not None and top is getattr(utils, "we_need_to_talk", 0)
        report["doc"] = my_package.__doc__
        outputs = []
        for flag in (True, False):
            buffer = io.StringIO()
            if callable(top):
                with contextlib.redirect_stdout(buffer):
                    top(break_up=flag)
            outputs.append(buffer.getvalue().strip())
        report["outputs"] = outputs
        import pydoc
        report["rendered"] = pydoc.render_doc(my_package, renderer=pydoc.plaintext)
    print(json.dumps(report))
    """
)


def _probe_package(work_dir: object) -> dict | str:
    """Import the learner's `my_package` from `work_dir` in a fresh interpreter."""
    if not isinstance(work_dir, Path) or not (work_dir / "my_package").is_dir():
        return "expected the Path of the directory that contains my_package/"
    result = _child([sys.executable, "-c", _PROBE_PACKAGE], cwd=work_dir, timeout=30)
    if result.returncode != 0 or not result.stdout.strip():
        last = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "no output"
        return f"importing my_package crashed: {last}"
    report = json.loads(result.stdout)
    if "import_error" in report:
        return f"`import my_package` fails: {report['import_error']}"
    return report


@register("w06-e2")
def _w06_e2(work_dir: object) -> str | None:
    """`import my_package; my_package.we_need_to_talk(...)` in a fresh interpreter."""
    report = _probe_package(work_dir)
    if isinstance(report, str):
        return report
    if "utils_error" in report:
        return f"my_package/utils.py does not import: {report['utils_error']}"
    if not report["utils_has_it"]:
        return "my_package/utils.py must define we_need_to_talk; keep the function there"
    if not report["top_has_it"]:
        return (
            "`my_package.we_need_to_talk` does not exist; __init__.py must import it from "
            ".utils so the package exposes it"
        )
    if not report["same_object"]:
        return (
            "my_package.we_need_to_talk is a different object from my_package.utils."
            "we_need_to_talk; import the function in __init__.py rather than copying it"
        )
    breaking, staying = report["outputs"]
    if not breaking or not staying or breaking == staying:
        return "we_need_to_talk(break_up=True) and (break_up=False) must print two different lines"
    return None


@register("w06-e3")
def _w06_e3(work_dir: object) -> str | None:
    """help(my_package) shows the docstring only when __init__.py opens with one."""
    report = _probe_package(work_dir)
    if isinstance(report, str):
        return report
    doc = report["doc"]
    if not isinstance(doc, str) or doc.strip().lower() in _PLACEHOLDERS or len(doc.strip()) < 20:
        return (
            "my_package.__doc__ is empty; the first statement in __init__.py must be a "
            "docstring of at least one full sentence"
        )
    if doc.strip().splitlines()[0] not in report["rendered"]:
        return "help(my_package) does not show the docstring; it must open __init__.py"
    if not report["top_has_it"]:
        return "the docstring is there but my_package.we_need_to_talk is gone; keep the import"
    return None
