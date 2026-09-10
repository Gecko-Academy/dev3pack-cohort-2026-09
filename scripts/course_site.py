"""Generate the table of contents and the course index from the curriculum.

    uv run python scripts/course_site.py            # write them
    uv run python scripts/course_site.py --check    # CI: fail if anything is stale

ONE ORDERING SOURCE. The course is data in `bootcamp_agent.curriculum`, and this
renders it into the two files people navigate by:

    units/en/_toctree.yml   the table of contents, in the Hugging Face course
                            shape: one group per unit, `local` paths under
                            `units/en`, titles read from each page's heading
    docs/course-index.md    the human index: dates, checks, and what runs in CI

It also owns one managed block at the end of every unit's `introduction.mdx`,
between `navigation:start` and `navigation:end` markers, so every unit has a
Previous and a Next that cannot go stale. Everything outside the markers is the
author's.

IT ALSO REFUSES. A unit directory with no `introduction.mdx`, a notebook
without its solutions, a page nobody can reach from the table of contents, or
a directory the curriculum does not know: each is a problem `--check` reports,
because a page that exists and is unreachable is the failure this layout was
adopted to end.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bootcamp_agent.curriculum import (  # noqa: E402
    BONUS_DIRS,
    CAPSTONE,
    CHAPTERS,
    COURSE_RELEASE,
    TRACKS_ROOT,
    UNITS_ROOT,
    WEEK0_COURSES,
    WEEK0_UNITS,
    WEEK_TITLES,
    exercise_ids,
    unit_exercise_ids,
)
from bootcamp_agent.hints import FULL_MARKS  # noqa: E402

TOCTREE = UNITS_ROOT / "_toctree.yml"
INDEX = ROOT / "docs" / "course-index.md"
CURRICULUM = ROOT / "docs" / "curriculum.md"
#: Shipped INTO the public submissions repository, so its track renderer needs no
#: course checkout. It is the denominator and nothing else: ids, titles, whether
#: an item is scored, and how many marks it is out of. No answers, no checkers,
#: no exercise bodies — only what is needed to tell "not submitted" from
#: "handed in and never marked", which is the distinction the track exists for.
ITEMS = ROOT / "docs" / "instructor" / "submissions-repo" / "items.json"
NAV_START = "<!-- navigation:start -->"
NAV_END = "<!-- navigation:end -->"
PLAN_START = "<!-- plan:start -->"
PLAN_END = "<!-- plan:end -->"
MAP_START = "<!-- repo-map:start -->"
MAP_END = "<!-- repo-map:end -->"
RELEASE_START = "<!-- release-plan:start -->"
RELEASE_END = "<!-- release-plan:end -->"
README = ROOT / "README.md"

#: Every tracked top-level path, and one line on what it is for.
#:
#: THIS IS A CHECKED LIST, not documentation that drifts. `validate()` refuses a
#: top-level entry missing from here and an entry here that no longer exists, so
#: a directory cannot arrive in this repository undescribed — which is exactly
#: how the last map went stale. Whether a learner receives it is NOT written
#: here; it is read from the publisher, which is the only thing that decides.
REPO_MAP: tuple[tuple[str, str], ...] = (
    (
        "00-START-HERE.ipynb",
        "The map a learner opens first. Lists every notebook in order and ticks what is finished.",
    ),
    (
        "units/",
        "The course. `en/` holds week-0 units, the fifteen sessions, the capstone, and the bonus "
        "track, each a directory of pages plus a notebook.",
    ),
    (
        "src/bootcamp_agent/",
        "The finished shape of the capstone package, and the check registry every exercise is "
        "graded by.",
    ),
    (
        "tests/",
        "Behaviour contracts for the package — and the solved value of every exercise, which is "
        "why students never receive it.",
    ),
    ("data/", "The versioned corpus the retrieval sessions and the capstone answer from."),
    (
        "scripts/",
        "The course's own tooling: the site generator, the publisher, the submission collector.",
    ),
    ("docs/", "Curriculum, guides, the generated index, and the instructor material."),
    ("depth/", "Six optional software-engineering modules, about 45 minutes each. Never counted."),
    (
        "cookbook/",
        "Ten Gecko notebooks, from comprehending an OpenAPI spec to a verified loop on a fork. "
        "Optional.",
    ),
    ("workspaces/", "Four open projects to build in. Optional, unmarked, no checks."),
    ("integrations/", "Worked integrations the sessions link into rather than re-explain."),
    ("builder-kit/", "Templates a learner copies from when starting their own surface."),
    (
        "final_assignment/",
        "The final's harness and the offline practice grader. The private question set is not "
        "here and never will be.",
    ),
    (
        "modules/",
        "A pointer only. The tree lived here until 9 Sep 2026; the file says where it went.",
    ),
    (
        "AGENTS.md",
        "The policy a coding assistant reads before it edits. `CLAUDE.md` and the Cursor rules "
        "point at it rather than forking it.",
    ),
    ("README.md", "This file."),
    ("SETUP.md", "The half-hour path from a clone to a green doctor."),
    ("CLAUDE.md", "Points Claude Code at `AGENTS.md`."),
    ("LICENSE", "MIT."),
    ("pyproject.toml", "The package, its dependency groups, and the tool configuration."),
    ("uv.lock", "The resolved dependency set. CI installs from it frozen."),
    (".github/", "CI. It runs every notebook, the full test suite, and the generator's `--check`."),
    (".claude-plugin/", "The plugin manifest that ships the course's own slash commands."),
    (".cursor/", "Cursor rules, pointing at `AGENTS.md`."),
    (".env.example", "Every variable the course reads, with empty values."),
    (".gitignore", "What never enters git, including keys and a learner's own submissions."),
    (".python-version", "The interpreter `uv` picks."),
)

#: Pages that are not lessons: the welcome unit, in reading order.
UNIT0 = "unit0"
UNIT0_ORDER = (
    "introduction",
    "onboarding",
    "runtime-lanes",
    "how-to-submit",
    "week0",
    "week1",
    "week2",
    "week3",
)

#: One-page groups after the sessions, present only when the page exists.
TRAILING = (
    ("depth", "Depth track (optional)"),
    ("cookbook", "Cookbook"),
    ("workspaces", "Workspaces"),
    ("final-assignment", "Final assignment"),
)

HEADING = re.compile(r"^#\s+(.+?)\s*(?:\[\[[^\]]*\]\])?\s*$", re.M)


def page_title(path: Path) -> str:
    """The page's own first heading, without the `[[anchor]]` suffix."""
    match = HEADING.search(path.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else path.stem.replace("-", " ")


def _page_key(path: Path) -> tuple[int, int, str]:
    """introduction, then concepts in order, then anything else, quiz, conclusion."""
    stem = path.stem
    if stem == "introduction":
        return (0, 0, stem)
    if match := re.fullmatch(r"concepts-(\d+)", stem):
        return (1, int(match.group(1)), stem)
    if stem == "quiz":
        return (3, 0, stem)
    if stem == "conclusion":
        return (4, 0, stem)
    return (2, 0, stem)


def pages(directory: Path) -> list[Path]:
    """The lesson pages of one unit, in reading order.

    `loader-*` files are content carried in from a merged chapter and still to
    be folded into the unit's own pages; they are deliberately not listed.
    """
    return sorted(
        (path for path in directory.glob("*.mdx") if not path.name.startswith(("_", "loader-"))),
        key=_page_key,
    )


def _local(page: Path) -> str:
    """A toctree `local`: the page's path under `units/en`, without its suffix.

    NOT `directory.name`. Units nest by week now, so a session's page is
    `unit1/session-02-model-adapter/introduction`, and a name alone would
    collide the moment two weeks held the same leaf.
    """
    return page.relative_to(UNITS_ROOT).with_suffix("").as_posix()


def _sections(directory: Path, first_title: str | None = None) -> list[dict[str, str]]:
    sections = []
    for page in pages(directory):
        local = _local(page)
        title = first_title if (page.stem == "introduction" and first_title) else page_title(page)
        sections.append({"local": local, "title": title})
    return sections


def groups() -> list[dict[str, object]]:
    """The table of contents as data. Group order is the course order."""
    out: list[dict[str, object]] = []

    unit0 = UNITS_ROOT / UNIT0
    if unit0.is_dir():
        ordered = [
            unit0 / f"{stem}.mdx" for stem in UNIT0_ORDER if (unit0 / f"{stem}.mdx").is_file()
        ]
        out.append(
            {
                "title": "Unit 0. Welcome to the course",
                "sections": [
                    {"local": _local(page), "title": page_title(page)} for page in ordered
                ],
            }
        )

    for course in WEEK0_COURSES:
        sections: list[dict[str, str]] = []
        for unit in WEEK0_UNITS:
            if unit.course == course:
                sections += _sections(unit.directory, f"Unit {unit.number}. {unit.title}")
        out.append({"title": f"Week 0. {course}", "sections": sections})

    for chapter in CHAPTERS:
        out.append(
            {
                "title": f"Session {chapter.number}. {chapter.title} — {chapter.weekday}",
                "sections": _sections(chapter.directory, "Introduction"),
            }
        )
        # The capstone opens with a week, so it belongs after that week's last
        # session rather than after all fifteen.
        last_of_week = [c for c in CHAPTERS if c.module == chapter.module][-1]
        if chapter is last_of_week and chapter.module == CAPSTONE.opens_in_week:
            out.append(
                {
                    "title": CAPSTONE.title,
                    "sections": _sections(CAPSTONE.directory, "Introduction"),
                }
            )

    for name, title in TRAILING:
        directory = UNITS_ROOT / TRACKS_ROOT / name
        if directory.is_dir() and pages(directory):
            out.append({"title": title, "sections": _sections(directory)})

    for index, name in enumerate(BONUS_DIRS, start=1):
        directory = UNITS_ROOT / name
        if directory.is_dir() and pages(directory):
            out.append(
                {
                    "title": (
                        f"(Optional) Bonus {index}. {page_title(directory / 'introduction.mdx')}"
                    ),
                    "sections": _sections(directory),
                }
            )
    return out


def render_toctree() -> str:
    """Hand-rendered YAML: two nesting levels, quoted titles, no dependency."""
    lines = [
        "# generated by scripts/course_site.py — edit the curriculum or the pages, not this file"
    ]
    for group in groups():
        lines.append(f"- title: {json.dumps(group['title'], ensure_ascii=False)}")
        lines.append("  sections:")
        for section in group["sections"]:  # type: ignore[union-attr]
            lines.append(f"  - local: {section['local']}")
            lines.append(f"    title: {json.dumps(section['title'], ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def _link(directory: Path) -> str:
    """A link from docs/ to a unit directory; root-relative would break on GitHub."""
    return f"../{directory.relative_to(ROOT).as_posix()}/"


def render_index() -> str:
    lines = [
        "<!-- generated by scripts/course_site.py — edit the curriculum module, not this file -->",
        "",
        "# Course index",
        "",
        "Everything a learner opens lives under `units/en/`, one directory per unit,",
        "in the order `units/en/_toctree.yml` gives. Each unit holds an",
        "`introduction.mdx`, its concept pages, an exercise `notebook.ipynb` and a",
        "`solutions/notebook.ipynb`. Demo day has no notebook.",
        "",
        "**Checks** is how many exercises that unit's notebook scores. Run one with",
        "`uv run bootcamp check ch03`, or all of them with `uv run bootcamp progress`.",
        "",
        "## Week 0: the prerequisite",
        "",
        f"Self-paced, before Monday 14 September 2026. {len(WEEK0_UNITS)} units, all offline,",
        "handed in as a record of the work and never marked. No date: these are done",
        "when you do them. Short on time? The fast lane is the floor session 1 assumes;",
        "the courses beside it are the long form.",
        "",
    ]
    week0_checks = 0
    for course in WEEK0_COURSES:
        lines += [f"### {course}", "", "| # | Unit | Checks |", "|---|---|---|"]
        for unit in WEEK0_UNITS:
            if unit.course != course:
                continue
            count = len(unit_exercise_ids(unit.prefix))
            week0_checks += count
            lines.append(f"| {unit.number} | [{unit.title}]({_link(unit.directory)}) | {count} |")
        lines.append("")

    live_checks = 0
    for module in sorted(WEEK_TITLES):
        chapters = [chapter for chapter in CHAPTERS if chapter.module == module]
        first, last = chapters[0], chapters[-1]
        lines += [
            f"## Week {module}: {WEEK_TITLES[module]}",
            "",
            f"{first.weekday} to {last.weekday}",
            "",
            "| Day | # | Session | Checks | Runs unattended |",
            "|---|---|---|---|---|",
        ]
        for chapter in chapters:
            checks = len(exercise_ids(chapter.chapter_id))
            live_checks += checks
            if not chapter.has_notebook:
                unattended = "no notebook"
            elif chapter.manual_reason:
                unattended = f"no: {chapter.manual_reason}"
            else:
                unattended = "yes"
            lines.append(
                f"| {chapter.weekday} | {chapter.number} | "
                f"[{chapter.title}]({_link(chapter.directory)}) | "
                f"{checks or '—'} | {unattended} |"
            )
        lines.append("")

    capstone_checks = len(unit_exercise_ids(CAPSTONE.prefix))
    lines += [
        "## Capstone",
        "",
        f"[{CAPSTONE.title}]({_link(CAPSTONE.directory)}) opens with week",
        f"{CAPSTONE.opens_in_week} and is built between sessions. "
        f"{capstone_checks} checks, scored.",
        "",
    ]

    runnable = sum(1 for chapter in CHAPTERS if chapter.runs_in_ci)
    handed_in = [chapter for chapter in CHAPTERS if chapter.has_notebook and chapter.manual_reason]
    lines += [
        "## Totals",
        "",
        f"- {len(WEEK0_UNITS)} week-0 units with {week0_checks} checks, "
        "handed in and never marked.",
        f"- {len(CHAPTERS)} sessions, {runnable} of them running unattended in CI, "
        f"with {live_checks} scored checks; plus the capstone's {capstone_checks}.",
        f"- {week0_checks + live_checks + capstone_checks} checks across the course.",
        f"- {len(handed_in)} sessions are handed in rather than marked, because they are",
        "  assistant-driven and cannot be re-run; each says so in the table above.",
        "",
    ]
    return "\n".join(lines)


def outcome_of(directory: Path) -> str:
    """The unit's own statement of what a learner leaves with.

    Read from `introduction.mdx` rather than retyped, so the class-by-class plan
    says what each session's page says. Three shapes exist in the tree and all
    three are honest: an `## Outcome` heading, a `**Outcome:**` lead, or, for a
    page that predates either, the first real paragraph. A page still being
    authored says so rather than inventing something.
    """
    page = directory / "introduction.mdx"
    if not page.is_file():
        return "_Not yet authored._"
    lines = page.read_text(encoding="utf-8").splitlines()

    def paragraph_from(index: int) -> str:
        collected: list[str] = []
        for line in lines[index:]:
            stripped = line.strip()
            if stripped.startswith(("#", "|", "```", ">")):
                break
            if not stripped:
                if collected:
                    break
                continue
            collected.append(stripped)
        return " ".join(collected)

    for index, line in enumerate(lines):
        if line.strip().lower() == "## outcome":
            if found := paragraph_from(index + 1):
                return found
            break

    for index, line in enumerate(lines):
        if line.strip().startswith("**Outcome:**"):
            return paragraph_from(index).replace("**Outcome:** ", "").replace("**Outcome:**", "")

    # No stated outcome: the first paragraph that is prose rather than metadata.
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|", "```", ">", "-", "*")):
            continue
        if stripped.startswith("**") and stripped.endswith("**"):
            continue  # the dated subtitle line
        if found := paragraph_from(index):
            return found
    return "_No outcome stated yet._"


def render_plan() -> str:
    """The class-by-class plan: every unit, its outcome, its checks, its page."""
    lines = [
        PLAN_START,
        "",
        "<!-- generated by scripts/course_site.py — do not edit by hand -->",
        "",
    ]
    lines += [
        "## Week 0 — the prerequisite",
        "",
        "Self-paced, before Monday 14 September. Handed in as a record of the work",
        "and never marked.",
        "",
    ]
    for course in WEEK0_COURSES:
        lines += [f"### {course}", ""]
        for unit in WEEK0_UNITS:
            if unit.course != course:
                continue
            checks = unit_exercise_ids(unit.prefix)
            lines += [
                f"**Unit {unit.number} — {unit.title}** "
                f"([page](../{unit.directory.relative_to(ROOT).as_posix()}/introduction.mdx), "
                f"{len(checks)} checks)",
                "",
                outcome_of(unit.directory),
                "",
            ]
    for module in sorted(WEEK_TITLES):
        chapters = [chapter for chapter in CHAPTERS if chapter.module == module]
        lines += [
            f"## Week {module} — {WEEK_TITLES[module]} "
            f"({chapters[0].weekday} to {chapters[-1].weekday})",
            "",
        ]
        for chapter in chapters:
            checks = exercise_ids(chapter.chapter_id)
            marked = (
                "handed in, not marked"
                if chapter.manual_reason
                else ("no notebook" if not chapter.has_notebook else f"{len(checks)} checks")
            )
            lines += [
                f"### Session {chapter.number} — {chapter.title} ({chapter.weekday})",
                "",
                f"`{chapter.chapter_id}` · {marked} · "
                f"[page](../{chapter.directory.relative_to(ROOT).as_posix()}/introduction.mdx)",
                "",
                outcome_of(chapter.directory),
                "",
            ]
    capstone_checks = unit_exercise_ids(CAPSTONE.prefix)
    lines += [
        f"## {CAPSTONE.title}",
        "",
        f"`{CAPSTONE.prefix}` · {len(capstone_checks)} checks · opens with week "
        f"{CAPSTONE.opens_in_week} · "
        f"[page](../{CAPSTONE.directory.relative_to(ROOT).as_posix()}/introduction.mdx)",
        "",
        outcome_of(CAPSTONE.directory),
        "",
        PLAN_END,
    ]
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------- navigation


def _ordered_units() -> list[tuple[Path, str]]:
    """Every unit directory that gets a Previous/Next, in course order."""
    ordered: list[tuple[Path, str]] = [(unit.directory, unit.title) for unit in WEEK0_UNITS]
    for chapter in CHAPTERS:
        ordered.append((chapter.directory, chapter.title))
        # The capstone sits in the week it opens with, so Previous and Next
        # walk through it there rather than parking it after demo day.
        last_of_week = [c for c in CHAPTERS if c.module == chapter.module][-1]
        if chapter is last_of_week and chapter.module == CAPSTONE.opens_in_week:
            ordered.append((CAPSTONE.directory, CAPSTONE.title))
    return ordered


def _nav_block(
    here: Path,
    previous: tuple[Path, str] | None,
    following: tuple[Path, str] | None,
) -> str:
    """Previous and Next, as paths relative to the page they sit on.

    `../{name}/` only worked while every unit was a sibling. Units nest by week
    now, so the last session of week 1 links up and across into week 2, and the
    depth has to be computed rather than assumed.
    """

    def link(label: str, target: Path) -> str:
        rel = os.path.relpath(target / "introduction.mdx", here)
        return f"[{label}]({rel})"

    parts = []
    if previous:
        parts.append(link(f"Previous: {previous[1]}", previous[0]))
    if following:
        parts.append(link(f"Next: {following[1]}", following[0]))
    return f"{NAV_START}\n{' · '.join(parts)}\n{NAV_END}\n"


def with_navigation(text: str, block: str) -> str:
    """The page with its managed block replaced, or appended if absent."""
    start, end = text.find(NAV_START), text.find(NAV_END)
    if start != -1 and end != -1:
        return text[:start] + block + text[end + len(NAV_END) :].lstrip("\n")
    return text.rstrip("\n") + "\n\n" + block


def navigation_files() -> dict[Path, str]:
    """`introduction.mdx` content for every unit, nav block included."""
    ordered = _ordered_units()
    out: dict[Path, str] = {}
    for index, (directory, _title) in enumerate(ordered):
        page = directory / "introduction.mdx"
        if not page.is_file():
            continue  # reported by validate(), not silently created
        previous = ordered[index - 1] if index > 0 else None
        following = ordered[index + 1] if index + 1 < len(ordered) else None
        out[page] = with_navigation(
            page.read_text(encoding="utf-8"), _nav_block(directory, previous, following)
        )
    return out


# ------------------------------------------------------------------ validation


def validate() -> list[str]:
    """Everything wrong with the tree, each naming the path."""
    problems: list[str] = []
    known = {
        (UNITS_ROOT / UNIT0).resolve(),
        *((UNITS_ROOT / name).resolve() for name in BONUS_DIRS),
        *((UNITS_ROOT / TRACKS_ROOT / name).resolve() for name, _ in TRAILING),
    }
    for directory, _title in _ordered_units():
        known.add(directory.resolve())
        if not (directory / "introduction.mdx").is_file():
            problems.append(f"{directory.relative_to(ROOT)}: no introduction.mdx")
    for chapter in CHAPTERS:
        if chapter.has_notebook:
            for path in (chapter.notebook, chapter.solutions):
                if path is not None and not path.is_file():
                    problems.append(f"{path.relative_to(ROOT)}: missing")
    for unit in WEEK0_UNITS:
        for path in (unit.notebook, unit.directory / "solutions" / "notebook.ipynb"):
            if not path.is_file():
                problems.append(f"{path.relative_to(ROOT)}: missing")
    for path in (CAPSTONE.notebook, CAPSTONE.solutions):
        if not path.is_file():
            problems.append(f"{path.relative_to(ROOT)}: missing")
    # A unit directory is one holding pages. Walk to find them, because the
    # containers (`unit1/`, `bonus/`, `tracks/`) are not units themselves.
    for entry in sorted(UNITS_ROOT.rglob("*")):
        if not entry.is_dir() or entry.name == "solutions" or "solutions" in entry.parts:
            continue
        if not any(entry.glob("*.mdx")):
            continue
        if entry.resolve() not in known:
            problems.append(f"{entry.relative_to(ROOT)}: not a unit the curriculum knows")
    # A link that does not resolve is a 404 for a learner, and the whole reason
    # the tree moved was that every link in the old index was one. Code spans
    # are skipped: `tools[name](**args)` is not a link, however much it looks
    # like one to a regular expression.
    for page in sorted(UNITS_ROOT.rglob("*.mdx")):
        text = re.sub(r"`[^`]*`", "", page.read_text(encoding="utf-8"))
        for match in re.finditer(r"\[[^\]]*]\((?!https?:|#|mailto:)([^)]+)\)", text):
            target = match.group(1).split("#")[0].strip()
            if target and not (page.parent / target).exists():
                problems.append(f"{page.relative_to(ROOT)}: link does not resolve: {target}")

    # A top-level entry nobody described, or a description of something gone.
    described = {path.rstrip("/").split("/")[0] for path, _ in REPO_MAP}
    tracked = {
        line.split("/")[0]
        for line in subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.splitlines()
        if line
    }
    if tracked:
        for name in sorted(tracked - described):
            problems.append(f"{name}: tracked at the top level and not in REPO_MAP")
        for name in sorted(described - tracked):
            problems.append(f"{name}: described in REPO_MAP and not in the repository")

    reachable = {
        section["local"]
        for group in groups()
        for section in group["sections"]  # type: ignore[union-attr]
    }
    for page in sorted(UNITS_ROOT.rglob("*.mdx")):
        if page.name.startswith(("_", "loader-")) or "solutions" in page.parts:
            continue
        if _local(page) not in reachable:
            problems.append(f"{page.relative_to(ROOT)}: not reachable from _toctree.yml")
    return problems


def _publisher():
    """The publisher's own rules, imported rather than restated.

    Whether a learner receives a path is decided in exactly one place. Reading
    it here means the map cannot claim something the publisher does not do.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import publish_cohort

    return publish_cohort


def _audience(path: str, publisher) -> str:
    """What a learner gets of this entry, decided by what the publisher copies.

    NOT BY A LIST HERE. The publisher copies exactly the paths `released_paths`
    names, so anything absent from that list is absent from the student repo —
    and the honest default is therefore "never", not "day one". Saying otherwise
    is how a map starts promising files nobody ships.
    """
    entry = path.rstrip("/")
    if entry == "units":
        return "weekly"
    shipped = set(publisher.released_paths(max(publisher.WEEKS)))
    # Whole, when the publisher copies this path or a directory above it.
    if any(entry == name or entry.startswith(f"{name}/") for name in shipped):
        return "day one"
    # In part, when it copies something inside it: `docs/` sends its guides and
    # keeps the instructor material, and that difference is worth showing.
    if any(name.startswith(f"{entry}/") for name in shipped):
        return "in part"
    return "**never**"


def render_repo_map() -> str:
    """The top-level map, with who receives each entry read from the publisher."""
    publisher = _publisher()
    lines = [
        MAP_START,
        "",
        "| Path | What lives there | Students get it |",
        "|---|---|---|",
    ]
    for path, description in REPO_MAP:
        lines.append(f"| `{path}` | {description} | {_audience(path, publisher)} |")
    withheld = sorted(publisher.NEVER)
    named = ", ".join(f"`{name}`" for name in withheld)
    partial = sorted(
        path.rstrip("/") for path, _ in REPO_MAP if _audience(path, publisher) == "in part"
    )
    lines += [
        "",
        f"{len(withheld)} paths are withheld by name, whatever the week: {named}. "
        "Each is on that list for a stated reason — `tests/` alone holds the "
        "solved value of every exercise. The publisher audits the tree it built "
        "rather than trusting the copy, and refuses if one of them appears.",
        "",
        f"Sent in part: {', '.join(f'`{name}/`' for name in partial)}. "
        "Guides, the curriculum and the generated index ship; the instructor "
        "material, the specs and the plans do not.",
        "",
        MAP_END,
    ]
    return "\n".join(lines) + "\n"


def _release_label(name: str) -> str:
    """A released path under `units/en`, named the way a person would name it."""
    for chapter in CHAPTERS:
        if chapter.dirname == name:
            return f"Session {chapter.number}, {chapter.title}"
    if name == CAPSTONE.dirname:
        return CAPSTONE.title
    return name


def render_release_plan() -> str:
    """What lands in the student repository, week by week, and what is new.

    Generated from the publisher, so the table cannot promise a week the
    publisher would refuse to ship.
    """
    publisher = _publisher()
    lines = [RELEASE_START, "", "| Arrives | Date | What is added |", "|---|---|---|"]
    previous: set[str] = set()
    opens = {0: "now", 1: CHAPTERS[0].on, 2: CHAPTERS[5].on, 3: CHAPTERS[10].on}
    for week in publisher.WEEKS:
        current = set(publisher.released_paths(week))
        added = sorted(current - previous)
        if week == 0:
            what = (
                f"Everything above except the sessions: the twelve week-0 units, "
                f"the welcome pages, the bonus track and the whole toolchain "
                f"({len(added)} paths)."
            )
            when = "now"
        else:
            names = [_release_label(Path(path).name) for path in added]
            what = "; ".join(names) if names else "nothing new"
            date = opens[week]
            when = date.strftime("%a %d %b") if hasattr(date, "strftime") else str(date)
        label = "Week 0" if week == 0 else f"Week {week}"
        lines.append(f"| {label} | {when} | {what} |")
        previous = current
    lines += [
        "",
        "**Nothing is hidden behind a permission.** A week that has not opened is "
        "not in the repository yet, so `git pull` on the Monday is the whole "
        "ritual. Your table of contents lists what you actually have, and names "
        "what is still to come in a comment at the end — this table is the "
        "schedule, and you have it from day one.",
        "",
        "A correction is withdrawn as well as added: the publisher removes a file "
        "the current week no longer contains, so a fix actually reaches somebody "
        "who already pulled.",
        "",
        RELEASE_END,
    ]
    return "\n".join(lines) + "\n"


def readme_file() -> dict[Path, str]:
    """`README.md` with its two managed blocks replaced; the prose is the author's."""
    if not README.is_file():
        return {}
    text = README.read_text(encoding="utf-8")
    for start_marker, end_marker, render in (
        (MAP_START, MAP_END, render_repo_map),
        (RELEASE_START, RELEASE_END, render_release_plan),
    ):
        start, end = text.find(start_marker), text.find(end_marker)
        if start == -1 or end == -1:
            return {}
        text = text[:start] + render() + text[end + len(end_marker) :].lstrip("\n")
    return {README: text}


def render_items() -> str:
    """The answer-free item manifest the public submissions repository carries."""
    items = []
    for unit in WEEK0_UNITS:
        items.append(
            {
                "id": unit.prefix,
                "title": unit.title,
                "kind": "unit",
                "track": unit.course,
                "scored": False,
                "verifiable": True,
                "exercises": len(unit_exercise_ids(unit.prefix)),
                "max_score": None,
            }
        )
    for chapter in CHAPTERS:
        if not chapter.has_notebook:
            continue
        exercises = exercise_ids(chapter.chapter_id)
        scored = chapter.runs_in_ci
        items.append(
            {
                "id": chapter.chapter_id,
                "title": chapter.title,
                "kind": "session",
                "week": chapter.module,
                "date": chapter.on.isoformat(),
                "scored": scored,
                "verifiable": scored,
                "exercises": len(exercises),
                "max_score": len(exercises) * FULL_MARKS if scored else None,
            }
        )
    capstone = unit_exercise_ids(CAPSTONE.prefix)
    items.append(
        {
            "id": CAPSTONE.prefix,
            "title": CAPSTONE.title,
            "kind": "project",
            "opens_in_week": CAPSTONE.opens_in_week,
            "scored": True,
            "verifiable": True,
            "exercises": len(capstone),
            "max_score": len(capstone) * FULL_MARKS,
        }
    )
    return (
        json.dumps(
            {"schema": "dev3pack.items.v1", "release": COURSE_RELEASE, "items": items}, indent=2
        )
        + "\n"
    )


def curriculum_file() -> dict[Path, str]:
    """`docs/curriculum.md` with its plan block replaced; the prose is the author's."""
    if not CURRICULUM.is_file():
        return {}
    text = CURRICULUM.read_text(encoding="utf-8")
    start, end = text.find(PLAN_START), text.find(PLAN_END)
    if start == -1 or end == -1:
        return {}
    return {CURRICULUM: text[:start] + render_plan() + text[end + len(PLAN_END) :].lstrip("\n")}


def expected_files() -> dict[Path, str]:
    files = {TOCTREE: render_toctree(), INDEX: render_index(), ITEMS: render_items()}
    files.update(navigation_files())
    files.update(curriculum_file())
    files.update(readme_file())
    return files


def generate(check: bool = False) -> int:
    problems = validate()
    files = expected_files()
    stale = [
        path
        for path, text in files.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != text
    ]
    if check:
        for problem in problems:
            print(f"problem: {problem}")
        for path in stale:
            print(f"stale: {path.relative_to(ROOT)}")
        if problems or stale:
            print("re-run: uv run python scripts/course_site.py", file=sys.stderr)
            return 1
        print(f"course site current: {len(files)} generated files")
        return 0
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    written = f"{TOCTREE.relative_to(ROOT)}, {INDEX.relative_to(ROOT)}"
    print(f"wrote {written}, {len(files) - 2} navigation blocks")
    for problem in problems:
        print(f"problem: {problem}")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when anything is stale or wrong")
    args = parser.parse_args(argv)
    return generate(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
