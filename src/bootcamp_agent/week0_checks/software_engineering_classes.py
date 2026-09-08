"""Checkers for Course A, units 7 and 8: classes, documentation, tests, readability.

The learner hands over a class or a function and the checker USES it: it
instantiates, reads attributes, captures what `__init__` prints, runs the
docstring's own examples through doctest, and runs a test file through pytest
in a child process. Nothing here matches source text, because a class that
looks right and behaves wrong is exactly what these lessons exist to catch.
"""

from __future__ import annotations

import contextlib
import doctest
import inspect
import io
import os
import re
import subprocess
import sys
from pathlib import Path

from bootcamp_agent.checks import register


def _instantiate(cls: object, *args: object) -> tuple[object | None, str | None]:
    """`cls(*args)`, or the one-line reason it could not be built."""
    if not inspect.isclass(cls):
        return None, "expected the class itself, not an instance or a string"
    try:
        return cls(*args), None
    except Exception as error:  # noqa: BLE001 - the learner's code is the thing under test
        return (
            None,
            f"{cls.__name__}({', '.join(map(repr, args))}) raised {type(error).__name__}: {error}",
        )


# ======================================== unit 07 · classes in a package


@register("w07-e1")
def _w07_e1(cls: object) -> str | None:
    """A minimal class whose docstring promise, `attribute`, is kept by __init__."""
    instance, problem = _instantiate(cls, "class attribute value")
    if problem:
        return problem
    if "attribute" not in vars(instance):
        held = sorted(vars(instance))
        return (
            f"the instance has no attribute called 'attribute' (it has {held}); __init__ must "
            "store the value under the name the docstring promises"
        )
    if instance.attribute != "class attribute value":
        return "instance.attribute must hold exactly the value passed to __init__"
    return None


@register("w07-e2")
def _w07_e2(cls: object) -> str | None:
    """A child that keeps the parent's attributes because its __init__ calls the parent's."""
    if not inspect.isclass(cls) or len(cls.__mro__) < 3:
        return "expected a class that inherits from another class you wrote"
    parent = cls.__mro__[1]
    parent_instance, problem = _instantiate(parent)
    if problem:
        return f"the parent cannot be built on its own: {problem}"
    child_instance, problem = _instantiate(cls)
    if problem:
        return problem
    parent_state, child_state = vars(parent_instance), vars(child_instance)
    missing = sorted(set(parent_state) - set(child_state))
    if missing:
        return (
            f"the child instance lacks the parent's {missing}; a child __init__ replaces the "
            "parent's, so it must call it first: super().__init__()"
        )
    if not set(child_state) - set(parent_state):
        return "the child adds nothing; set one attribute of its own after calling the parent"
    return None


def _printed_by(cls: type) -> tuple[list[str] | None, str | None]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        _, problem = _instantiate(cls)
    if problem:
        return None, problem
    return [line for line in buffer.getvalue().splitlines() if line.strip()], None


@register("w07-e3")
def _w07_e3(cls: object) -> str | None:
    """Three generations, each __init__ printing after the one above it."""
    if not inspect.isclass(cls):
        return "expected the grandchild class itself"
    chain = [klass for klass in cls.__mro__ if klass is not object]
    if len(chain) < 3:
        return "expected three levels of inheritance: a parent, a child, a grandchild"
    printed, problem = _printed_by(cls)
    if problem:
        if "TypeError" in problem and "self" in problem:
            return f"{problem}; call the parent through super().__init__(), which passes self"
        return problem
    if len(printed) != len(chain):
        return (
            f"building {cls.__name__} printed {len(printed)} line(s) for {len(chain)} levels; "
            "every __init__ in the chain must run, so each one must call super().__init__()"
        )
    for ancestor in chain[1:]:
        above, problem = _printed_by(ancestor)
        if problem:
            return f"{ancestor.__name__} cannot be built on its own: {problem}"
        if printed[: len(above)] != above:
            return (
                f"the lines {ancestor.__name__} prints must come first, in the same order, "
                "when the grandchild is built; call super().__init__() before printing"
            )
    return None


@register("w07-e4")
def _w07_e4(cls: object) -> str | None:
    """Document: tokens computed in __init__ by a non-public _tokenize method."""
    instance, problem = _instantiate(cls, "test doc")
    if problem:
        return problem
    if "tokens" not in vars(instance):
        return "Document('test doc') has no `tokens` attribute; set self.tokens in __init__"
    if list(instance.tokens) != ["test", "doc"]:
        return f"Document('test doc').tokens is {instance.tokens!r}, expected ['test', 'doc']"
    empty, problem = _instantiate(cls, "")
    if problem:
        return problem
    if list(empty.tokens) != []:
        return "Document('').tokens must be an empty list"
    if not callable(getattr(cls, "_tokenize", None)):
        return "the tokenising method must be non-public: name it _tokenize, with the underscore"
    if callable(getattr(cls, "tokenize", None)):
        return "there is still a public `tokenize` method; the underscore version replaces it"
    return None


# ======================================== unit 08 · documentation, tests, readability


@register("w08-e1")
def _w08_e1(function: object) -> str | None:
    """A docstring with :param, :return and a >>> example that doctest accepts."""
    if not callable(function):
        return "expected the function itself"
    doc = inspect.getdoc(function) or ""
    for needle, meaning in ((":param", "the parameter"), (":return", "the return value")):
        if needle not in doc:
            return f"the docstring has no `{needle}` line describing {meaning}"
    if ">>>" not in doc:
        return "the docstring has no `>>>` example; doctest has nothing to run"
    name = getattr(function, "__name__", "f")
    # The example calls the function by name, so the name must resolve even when
    # the function was defined inside another function (a test, say).
    globs = {**getattr(function, "__globals__", {}), name: function}
    runner = doctest.DocTestRunner(verbose=False)
    tests = doctest.DocTestFinder().find(function, name=name, globs=globs)
    with contextlib.redirect_stdout(io.StringIO()):
        for test in tests:
            runner.run(test)
    if runner.failures:
        return (
            f"doctest reports {runner.failures} failing example(s); the body must do what "
            "the docstring shows, not the other way round"
        )
    try:
        if function(3) != 9 or function(-2) != 4:
            return "the function is named square, so square(3) must be 9 and square(-2) must be 4"
    except Exception as error:  # noqa: BLE001
        return f"calling the function raised {type(error).__name__}: {error}"
    return None


_SUMMARY = re.compile(r"(\d+) passed")
_FAILED = re.compile(r"(\d+) failed")


@register("w08-e2")
def _w08_e2(test_file: object) -> str | None:
    """pytest on the learner's test file, expecting exactly two passing tests."""
    if not isinstance(test_file, Path) or not test_file.is_file():
        return "expected the Path to the test file the cell wrote"
    if not test_file.name.startswith("test_"):
        return "pytest only collects files named test_*.py"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(test_file),
            "-q",
            "--color=no",
            "-p",
            "no:cacheprovider",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=test_file.parent,
        env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"},
    )
    summary = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    passed = _SUMMARY.search(result.stdout)
    failed = _FAILED.search(result.stdout)
    if failed and int(failed.group(1)):
        return f"pytest still reports a failure: {summary}; read the assertion it prints"
    if result.returncode != 0 or not passed:
        last = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else summary
        return f"pytest did not run cleanly: {last or 'no output'}"
    if int(passed.group(1)) != 2:
        return f"expected exactly 2 passing tests, pytest found {passed.group(1)}"
    return None


@register("w08-e3")
def _w08_e3(function: object) -> str | None:
    """Descriptive names for check(x, y=100), and the same behaviour."""
    if not callable(function):
        return "expected the function itself"
    name = getattr(function, "__name__", "")
    parameters = list(inspect.signature(function).parameters.values())
    if len(parameters) != 2:
        return "keep two parameters: the value to test and the threshold with its default"
    if parameters[1].default != 100:
        return "the second parameter must keep its default of 100"
    names = [name, parameters[0].name, parameters[1].name]
    vague = {"check", "chk", "x", "y", "a", "b", "f", "func", "value", "val", "n", "num"}
    for label, candidate in zip(
        ("function", "first parameter", "second parameter"), names, strict=True
    ):
        if candidate.lower() in vague or len(candidate) < 3:
            return f"the {label} is still called {candidate!r}; say what it is, not what type it is"
        if len(candidate) > 30:
            return (
                f"the {label} name is {len(candidate)} characters; that is the other failure mode"
            )
    try:
        checks = (function(100), function(99.9), function(30, 20), function(20, 30))
    except Exception as error:  # noqa: BLE001
        return f"calling the function raised {type(error).__name__}: {error}"
    if checks != (True, False, True, False):
        return "renaming must not change behaviour: the function still returns first >= second"
    return None
