"""The course as data: fifteen chapters, their dates, and where each one lives.

Before this module the schedule existed only as prose in `docs/curriculum.md`
and as directory names under `modules/`. Two sources drift, so this is the one:
the CLI reads it to find a notebook, and `scripts/course_index.py` renders
`docs/course-index.md` from it.

Exercise ids are NOT listed here. They come from the registry in
:mod:`bootcamp_agent.checks`, because that is where a check is actually defined
and a list of ids kept anywhere else would be a second source of the same fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Chapter:
    """One session. `manual_reason` is why CI cannot execute its notebook."""

    number: int
    title: str
    on: date
    module: int
    #: None when the notebook runs unattended in CI. A sentence when it does not,
    #: and the sentence is the reason, never a bare flag.
    manual_reason: str | None = None
    #: Chapter 15 is demo day: slides and a README, no notebook.
    has_notebook: bool = True

    @property
    def chapter_id(self) -> str:
        return f"ch{self.number:02d}"

    @property
    def directory(self) -> Path:
        return REPO_ROOT / "modules" / f"module-{self.module}" / f"chapter-{self.number:02d}"

    @property
    def notebook(self) -> Path | None:
        return self.directory / "notebook.ipynb" if self.has_notebook else None

    @property
    def solutions(self) -> Path | None:
        return self.directory / "solutions" / "notebook.ipynb" if self.has_notebook else None

    @property
    def runs_in_ci(self) -> bool:
        return self.has_notebook and self.manual_reason is None

    @property
    def weekday(self) -> str:
        return self.on.strftime("%a %d %b")


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(1, "Orientation: from LLM calls to agentic systems", date(2026, 9, 14), 1),
    Chapter(2, "Python for AI engineers", date(2026, 9, 15), 1),
    Chapter(3, "Prompts and structured outputs", date(2026, 9, 16), 1),
    Chapter(
        4,
        "Claude Code 101 and assistant configuration",
        date(2026, 9, 17),
        1,
        manual_reason="assistant-driven: it edits your editor and assistant configuration",
    ),
    Chapter(5, "Tools: controlled capabilities", date(2026, 9, 18), 1),
    Chapter(6, "RAG fundamentals", date(2026, 9, 21), 2),
    Chapter(7, "Retrieval quality and query optimization", date(2026, 9, 22), 2),
    Chapter(8, "Agentic design patterns", date(2026, 9, 23), 2),
    Chapter(9, "Reliability: tracing, evaluation, error analysis", date(2026, 9, 24), 2),
    Chapter(
        10,
        "Agent skills, MCP, and subagents",
        date(2026, 9, 25),
        2,
        manual_reason="assistant-driven: skill authoring plus before/after runs in your assistant",
    ),
    Chapter(11, "Memory and long-running agents", date(2026, 9, 28), 3),
    Chapter(12, "Capstone build sprint I", date(2026, 9, 29), 3),
    # Was instructor-gated until 2026-09-03. A read-only probe that day showed
    # the hosted surface is open: no credential, 16 tools, real mainnet data on
    # list_stores. The session now teaches from dated recordings and runs
    # unattended; the live surface and the fork rehearsal are both optional.
    Chapter(13, "Orquestra + Gecko: verified API interaction", date(2026, 9, 30), 3),
    Chapter(14, "Capstone build sprint II: hardening", date(2026, 10, 1), 3),
    Chapter(15, "Demo day", date(2026, 10, 2), 3, has_notebook=False),
)


@dataclass(frozen=True)
class Unit:
    """One week-0 unit.

    Deliberately NOT a Chapter. A Chapter has a date because a session happens
    on a day; week 0 is self-paced and giving it a date would be a lie the
    course-index would then print. The two live side by side rather than one
    pretending to be the other.
    """

    number: int
    slug: str
    title: str

    @property
    def prefix(self) -> str:
        """The exercise-id prefix, so `review("w01")` scores unit 1."""
        return f"w{self.number:02d}"

    @property
    def directory(self) -> Path:
        return REPO_ROOT / "modules" / "module-0" / self.slug

    @property
    def notebook(self) -> Path:
        return self.directory / "notebook.ipynb"


#: Week 0, the prerequisite. Order matters: unit 1 fixes the setup problem that
#: otherwise ruins unit 2.
WEEK0_UNITS: tuple[Unit, ...] = (
    Unit(1, "unit-01-environment", "The environment"),
    Unit(2, "unit-02-packages-and-docs", "Packages and documentation"),
    Unit(3, "unit-03-classes-and-contracts", "Classes and contracts"),
    Unit(4, "unit-04-real-apis", "Calling a real API"),
)


BY_ID: dict[str, Chapter] = {chapter.chapter_id: chapter for chapter in CHAPTERS}

WEEK_TITLES = {
    1: "Foundations and coding-assistant setup",
    2: "Retrieval, agents, reliability, skills",
    3: "Production thinking, Gecko, capstone",
}


class UnknownChapter(KeyError):
    """Raised for a chapter id the course does not have."""


def get_chapter(chapter_id: str) -> Chapter:
    """Look up a chapter by id, accepting `ch03`, `3` or `03`."""
    key = chapter_id.strip().lower()
    if not key.startswith("ch"):
        key = f"ch{key.zfill(2)}"
    if key not in BY_ID:
        raise UnknownChapter(f"no chapter {chapter_id!r}; known: {sorted(BY_ID)}")
    return BY_ID[key]


def exercise_ids(chapter_id: str) -> tuple[str, ...]:
    """The exercise ids registered for a chapter, read from the check registry."""
    from bootcamp_agent.checks import CHECKS

    prefix = f"{get_chapter(chapter_id).chapter_id}-"
    return tuple(sorted(key for key in CHECKS if key.startswith(prefix)))


def unit_exercise_ids(prefix: str) -> tuple[str, ...]:
    """The exercise ids for a week-0 unit, from the same registry."""
    import bootcamp_agent.week0_checks  # noqa: F401 - importing is what registers them
    from bootcamp_agent.checks import CHECKS

    return tuple(sorted(key for key in CHECKS if key.startswith(f"{prefix}-")))
