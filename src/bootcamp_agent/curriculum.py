"""The course as data: fifteen sessions, twelve week-0 units, one capstone, and
where each one lives.

Before this module the schedule existed only as prose in `docs/curriculum.md`
and as directory names. Two sources drift, so this is the one: the CLI reads it
to find a notebook, `scripts/course_site.py` renders the table of contents and
the course index from it, and the publisher gates weeks by it.

LAYOUT. Every learner-facing page lives under `units/en/`, in the shape of the
Hugging Face courses: one directory per unit, its pages beside its notebook, and
one generated `_toctree.yml` that is the only place ordering is written down.
`en` is a real directory level so a second language is a mirror of this one.

Exercise ids are NOT listed here. They come from the registry in
:mod:`bootcamp_agent.checks`, because that is where a check is actually defined
and a list of ids kept anywhere else would be a second source of the same fact.

IDS WERE RENAMED ONCE, on 2026-09-09, when the sessions were re-sequenced and no
live-session submission existed yet. `docs/instructor/id-migration.md` records
the map. After that date an id is never renamed or reused.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The course release. Stamped into a final report so a score can be tied to the
#: exact course it was earned against; bumped when the cohort's content changes
#: in a way that would make an older report incomparable.
COURSE_RELEASE = "2026.09.1"

#: Where every learner-facing page lives. The language is a directory on purpose.
UNITS_ROOT = REPO_ROOT / "units" / "en"


@dataclass(frozen=True)
class Chapter:
    """One live session. `manual_reason` is why CI cannot execute its notebook."""

    number: int
    slug: str
    title: str
    on: date
    module: int
    #: None when the notebook runs unattended in CI. A sentence when it does not,
    #: and the sentence is the reason, never a bare flag.
    manual_reason: str | None = None
    #: Session 15 is demo day: pages and a rubric, no notebook.
    has_notebook: bool = True

    @property
    def chapter_id(self) -> str:
        return f"ch{self.number:02d}"

    @property
    def dirname(self) -> str:
        return f"session-{self.number:02d}-{self.slug}"

    @property
    def directory(self) -> Path:
        return UNITS_ROOT / self.dirname

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


#: The fifteen sessions, re-sequenced 2026-09-09 so that every session opens
#: with a contract and closes with a failure the learner has to handle.
CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        1,
        "assistant-configuration",
        "Configure the assistant and the repository instructions",
        date(2026, 9, 14),
        1,
        manual_reason="assistant-driven: it edits your editor and assistant configuration",
    ),
    Chapter(2, "model-adapter", "Call a model through the adapter", date(2026, 9, 15), 1),
    Chapter(3, "structured-outputs", "Structured outputs", date(2026, 9, 16), 1),
    Chapter(4, "bounded-tools", "Bounded tools", date(2026, 9, 17), 1),
    Chapter(5, "deterministic-mini-agent", "A deterministic mini-agent", date(2026, 9, 18), 1),
    Chapter(6, "retrieval-baseline", "A retrieval baseline", date(2026, 9, 21), 2),
    Chapter(7, "grounding-metrics", "Retrieval and grounding metrics", date(2026, 9, 22), 2),
    Chapter(8, "loops-and-graphs", "Loops and graphs", date(2026, 9, 23), 2),
    Chapter(9, "trace-and-evaluate", "Trace and evaluate an agent", date(2026, 9, 24), 2),
    Chapter(
        10,
        "skills-and-adr",
        "Skills and an architecture decision record",
        date(2026, 9, 25),
        2,
        manual_reason="assistant-driven: skill authoring plus before/after runs in your assistant",
    ),
    Chapter(11, "state-and-memory", "State and memory", date(2026, 9, 28), 3),
    Chapter(12, "mcp-architecture", "MCP architecture and primitives", date(2026, 9, 29), 3),
    # The applied case is Orquestra + Gecko. A read-only probe on 2026-09-03
    # showed the hosted surface is open: no credential, 16 tools, real mainnet
    # data on list_stores. The session teaches from dated recordings and runs
    # unattended; the live surface and the fork rehearsal are both optional.
    Chapter(13, "secure-mcp-server", "Build and secure an MCP server", date(2026, 9, 30), 3),
    Chapter(14, "deploy-and-operate", "Deploy and operate the capstone", date(2026, 10, 1), 3),
    Chapter(
        15, "defend-the-capstone", "Defend the capstone", date(2026, 10, 2), 3, has_notebook=False
    ),
)


@dataclass(frozen=True)
class Unit:
    """One week-0 unit.

    Deliberately NOT a Chapter. A Chapter has a date because a session happens
    on a day; week 0 is self-paced and giving it a date would be a lie the
    course index would then print. The two live side by side rather than one
    pretending to be the other.
    """

    number: int
    slug: str
    title: str
    #: The course a unit belongs to. Units 1-4 are the fast lane; the three
    #: courses beside them are the long form, in the DataCamp lesson shape.
    course: str = "The fast lane"

    @property
    def prefix(self) -> str:
        """The exercise-id prefix, so `review("w01")` scores unit 1."""
        return f"w{self.number:02d}"

    @property
    def dirname(self) -> str:
        return f"{self.prefix}-{self.slug}"

    @property
    def directory(self) -> Path:
        return UNITS_ROOT / self.dirname

    @property
    def notebook(self) -> Path:
        return self.directory / "notebook.ipynb"


#: Week 0, the prerequisite. Order matters: unit 1 fixes the setup problem that
#: otherwise ruins unit 2.
WEEK0_UNITS: tuple[Unit, ...] = (
    Unit(1, "environment", "The environment"),
    Unit(2, "packages-and-docs", "Packages and documentation"),
    Unit(3, "classes-and-contracts", "Classes and contracts"),
    Unit(4, "real-apis", "Calling a real API"),
    Unit(
        5,
        "packages-and-pep8",
        "Packages, PyPI and PEP 8",
        course="Course A — Software engineering foundations",
    ),
    Unit(
        6,
        "portable-packages",
        "A portable package",
        course="Course A — Software engineering foundations",
    ),
    Unit(
        7,
        "classes-in-packages",
        "Classes in a package",
        course="Course A — Software engineering foundations",
    ),
    Unit(
        8,
        "docs-tests-readability",
        "Documentation, tests and readability",
        course="Course A — Software engineering foundations",
    ),
    Unit(
        9,
        "mcp-first-server",
        "Your first MCP server",
        course="Course B — MCP: AI apps as easy as 1, 2, 3",
    ),
    Unit(
        10,
        "mcp-resources-prompts-llms",
        "Resources, prompts, and the LLM",
        course="Course B — MCP: AI apps as easy as 1, 2, 3",
    ),
    Unit(
        11,
        "mcp-data-apis-third-party",
        "Databases, APIs, and third-party servers",
        course="Course B — MCP: AI apps as easy as 1, 2, 3",
    ),
    Unit(
        12,
        "dsa-for-agents",
        "Data structures for agents",
        course="Course C — Data structures for agents",
    ),
)

#: Course order for the index: the fast lane first, then the long form.
WEEK0_COURSES: tuple[str, ...] = tuple(dict.fromkeys(unit.course for unit in WEEK0_UNITS))


@dataclass(frozen=True)
class Project:
    """The capstone: built across weeks 2 and 3 in the hours between sessions.

    Neither a Chapter nor a Unit. It has no single date, it is scored, and it
    opens with week 2 because its first exercise needs the retrieval baseline.
    """

    prefix: str = "cap01"
    slug: str = "capstone"
    title: str = "Capstone: the source-grounded research assistant"
    opens_in_week: int = 2

    @property
    def dirname(self) -> str:
        return self.slug

    @property
    def directory(self) -> Path:
        return UNITS_ROOT / self.dirname

    @property
    def notebook(self) -> Path:
        return self.directory / "notebook.ipynb"

    @property
    def solutions(self) -> Path:
        return self.directory / "solutions" / "notebook.ipynb"


CAPSTONE = Project()

#: Optional bonus units: pages only, never counted, never submitted. The
#: directory name is the id, and the title carries the optionality in words,
#: the way the Hugging Face course marks its bonus units.
BONUS_DIRS: tuple[str, ...] = (
    "bonus-b01-graph-rag",
    "bonus-b02-multimodal-ingestion",
    "bonus-b03-multi-agent-orchestration",
    "bonus-b04-memory-consent-deletion",
    "bonus-b05-deploy-evaluate-teardown",
)

BY_ID: dict[str, Chapter] = {chapter.chapter_id: chapter for chapter in CHAPTERS}

WEEK_TITLES = {
    1: "Contracts, adapters, tools, and a first agent",
    2: "Retrieval, graphs, evaluation, skills",
    3: "State, MCP, deployment, defense",
}


class UnknownChapter(KeyError):
    """Raised for a chapter id the course does not have."""


def get_chapter(chapter_id: str) -> Chapter:
    """Look up a session by id, accepting `ch03`, `3` or `03`."""
    key = chapter_id.strip().lower()
    if not key.startswith("ch"):
        key = f"ch{key.zfill(2)}"
    if key not in BY_ID:
        raise UnknownChapter(f"no chapter {chapter_id!r}; known: {sorted(BY_ID)}")
    return BY_ID[key]


def exercise_ids(chapter_id: str) -> tuple[str, ...]:
    """The exercise ids registered for a session, read from the check registry."""
    import bootcamp_agent.session_checks  # noqa: F401 - importing is what registers them
    from bootcamp_agent.checks import CHECKS

    prefix = f"{get_chapter(chapter_id).chapter_id}-"
    return tuple(sorted(key for key in CHECKS if key.startswith(prefix)))


def unit_exercise_ids(prefix: str) -> tuple[str, ...]:
    """The exercise ids for a week-0 unit or the capstone, from the same registry."""
    import bootcamp_agent.week0_checks  # noqa: F401 - importing is what registers them
    from bootcamp_agent.checks import CHECKS

    return tuple(sorted(key for key in CHECKS if key.startswith(f"{prefix}-")))
