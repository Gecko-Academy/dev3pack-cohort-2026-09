"""Run a chapter's notebook and report what its own checks said.

The notebook is the arbiter, here as in the notebook itself: this module does
not re-implement any check. It executes the notebook and reads back the lines
`check()` and `review()` printed, so the terminal shows exactly what the
participant would see in Jupyter.

Strict mode stays OFF for a participant's notebook. An unfilled `TODO(you)`
prints ❌ and the notebook keeps going, which is the whole point: the scorecard
is meant to be read while the work is unfinished.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from bootcamp_agent.checks import STRICT_ENV
from bootcamp_agent.curriculum import Chapter, exercise_ids

#: What `check()` prints. Anchored, because a notebook may legitimately print
#: a tick inside prose and that is not a verdict.
_PASS = re.compile(r"^✅ (ch\d\d-e\d+) passed\s*$")
_FAIL = re.compile(r"^❌ (ch\d\d-e\d+): (.+)$")


class CourseworkError(Exception):
    """The notebook could not be run at all. Distinct from a failed check."""


@dataclass
class Scorecard:
    """One chapter's verdicts, in the notebook's own words."""

    chapter_id: str
    passed: tuple[str, ...] = ()
    failed: tuple[tuple[str, str], ...] = ()
    #: Registered for this chapter but never reached: the cell was not run, or
    #: an earlier cell raised. Not a failure, and never reported as one.
    not_reached: tuple[str, ...] = ()
    lines: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed) + len(self.not_reached)

    @property
    def headline(self) -> str:
        return f"{self.chapter_id}: {len(self.passed)}/{self.total} passed"


def outputs_of(notebook: object) -> list[str]:
    """Every text line a notebook's cells printed, in order."""
    lines: list[str] = []
    for cell in getattr(notebook, "cells", []):
        for output in cell.get("outputs", []) or []:
            text = output.get("text") or ""
            if not text and "data" in output:
                text = output["data"].get("text/plain", "")
            if isinstance(text, list):
                text = "".join(text)
            lines.extend(str(text).splitlines())
    return lines


def read_scorecard(chapter: Chapter, lines: list[str]) -> Scorecard:
    """Turn printed output into a scorecard. Nothing is judged here, only read."""
    passed: list[str] = []
    # Keyed by exercise id, because one exercise reports twice in a normal run:
    # `check()` prints when its cell executes, and `review()` prints the same
    # failure again in the closing scorecard. Counting both turned chapter 1's
    # honest 0/3 into 0/6, which is a tally no participant could act on. First
    # reason wins, since that is the one `check()` gave at the point of failure.
    failures: dict[str, str] = {}
    for line in lines:
        if match := _PASS.match(line.strip()):
            passed.append(match.group(1))
        elif match := _FAIL.match(line.strip()):
            failures.setdefault(match.group(1), match.group(2))
    failed = tuple(failures.items())
    seen = {*passed, *failures}
    not_reached = tuple(
        exercise for exercise in exercise_ids(chapter.chapter_id) if exercise not in seen
    )
    return Scorecard(
        chapter_id=chapter.chapter_id,
        passed=tuple(dict.fromkeys(passed)),
        failed=failed,
        not_reached=not_reached,
        lines=lines,
    )


def run_chapter(chapter: Chapter, timeout: int = 180) -> Scorecard:
    """Execute a chapter's notebook with checks non-strict, and read its verdicts.

    :raises CourseworkError: when there is no notebook, when nbclient is absent,
        or when the notebook raised before its checks could report.
    """
    notebook_path = chapter.notebook
    if notebook_path is None:
        raise CourseworkError(f"{chapter.chapter_id} has no notebook (it is demo day)")
    if not notebook_path.is_file():
        raise CourseworkError(f"not found: {notebook_path}")
    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError as error:  # pragma: no cover - dev group is installed in CI
        raise CourseworkError(
            f"{error.name} is missing; install the dev group: uv sync --group dev"
        ) from error

    notebook = nbformat.read(notebook_path, as_version=4)
    previous = os.environ.get(STRICT_ENV)
    os.environ[STRICT_ENV] = "0"
    try:
        NotebookClient(
            notebook,
            timeout=timeout,
            kernel_name="python3",
            resources={"metadata": {"path": str(notebook_path.parent)}},
        ).execute()
    except Exception as error:  # noqa: BLE001 - any failure is one report line
        raise CourseworkError(f"{type(error).__name__}: {str(error)[:200]}") from error
    finally:
        if previous is None:
            os.environ.pop(STRICT_ENV, None)
        else:
            os.environ[STRICT_ENV] = previous
    return read_scorecard(chapter, outputs_of(notebook))


def render(card: Scorecard) -> str:
    """The scorecard as the terminal shows it: the score, then the work."""
    out = [card.headline]
    for exercise, reason in card.failed:
        out.append(f"❌ {exercise}: {reason}")
    for exercise in card.not_reached:
        out.append(f"   {exercise}: not checked yet; run its check cell")
    return "\n".join(out)
