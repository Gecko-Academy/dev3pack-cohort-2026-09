"""Publish one week of the course into the student repository.

    uv run python scripts/publish_cohort.py --week 1              # dry run
    uv run python scripts/publish_cohort.py --week 1 --commit     # write it

TWO REPOSITORIES, AND ONLY ONE OF THEM IS STAGED.

    source   this repo. Private, yours, everything, CI. Where you work.
    student  Gecko-Academy/dev3pack-cohort-2026-09. Read-only for the cohort.
             Contains only what has been released.

Nothing is hidden by a permission. Week 2 is simply not in the student repo
until you publish it, so there is nothing to leak and nothing to administer per
student. Access is granted once, at enrolment.

WHY A SCRIPT RATHER THAN A COPY BY HAND. Two exclusions are easy to forget and
expensive to get wrong:

  - `tests/test_checks.py` runs every checker against its SOLVED value. It is a
    literal answer key for all fifteen sessions.
  - an unreleased `units/en/session-NN-*/` is the staging itself.

So this refuses to publish rather than trusting anyone to remember. The refusal
is the product; the copying is incidental.

WHAT IT DOES NOT PROTECT AGAINST, stated plainly: the repository is MIT
licensed, and a student who has week 1 may redistribute it. This is a speed bump
against a cooperating cohort, not a control. It stops accidents, not people.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The student repository, named once. It also appears in SETUP.md, README.md
#: and the instructor runbook, and `tests/test_publish.py` asserts all four
#: agree — four files each hardcoding the same slug is how a rename half-lands,
#: which is exactly what happened when this said "Scoras-Academy".
STUDENT_REPO = "Gecko-Academy/dev3pack-cohort-2026-09"

sys.path.insert(0, str(ROOT / "src"))

from bootcamp_agent.curriculum import (  # noqa: E402
    BONUS_DIRS,
    CAPSTONE,
    CHAPTERS,
    TRACK_DIRS,
    get_chapter,
    unit_dir,
)

#: The weeks a publish can name. Week 0 is the prerequisite; 1-3 are the live weeks.
WEEKS = (0, 1, 2, 3)


UNITS = "units/en"


def week_of(relative: Path) -> int | None:
    """The week a path under `units/en` opens with, or None if it is never gated.

    Read from the curriculum: a session opens with its week, the capstone with
    the week its first exercise needs, and everything else (week-0 units, the
    welcome pages, the bonus track, the table of contents) ships on day one.
    """
    parts = relative.parts
    if parts[:2] != ("units", "en") or len(parts) < 3:
        return None
    # The week is the directory the material sits in: `unit0` is the
    # prerequisite, `unit1`-`unit3` are the teaching weeks. Reading it from the
    # path is why the nesting was worth doing — before it, this had to match
    # every session and the capstone by name.
    container = parts[2]
    if re.fullmatch(r"unit[0-9]+", container):
        return int(container[4:])
    # `bonus/` and `tracks/` are never gated; they ship on day one.
    return 0


#: Ships whole, on day one, whatever week it is. Every one of these is either
#: shared by all three weeks or reached across weeks (chapter 05 of week 1 links
#: into `cookbook/integrations/11`), so partitioning them breaks week 1.
ALWAYS = (
    # The map a learner opens first. It sorts to the top of a Jupyter file list
    # on purpose, and it reads the curriculum live, so a newly published week
    # appears in it without this file changing.
    "00-START-HERE.ipynb",
    # The pointer left where the old layout lived, so a student who pulled week 0
    # under `modules/` is told where it went rather than left with an empty dir.
    "modules/README.md",
    "src",
    "data",
    "cookbook",
    "workspaces",
    "scripts",
    "builder-kit",
    "integrations",
    "docs/guides",
    "docs/curriculum.md",
    "docs/course-index.md",
    "depth",
    "final_assignment",
    "README.md",
    "SETUP.md",
    "LICENSE",
    # The assistant policy, and the two files that point at it rather than
    # forking it. The README a student receives has a whole section telling them
    # to read AGENTS.md first, and session 1's outcome is a scoped instruction
    # set shaped like this one — so withholding them made the shipped README
    # promise a file that was not there.
    "AGENTS.md",
    "CLAUDE.md",
    ".cursor",
    ".claude-plugin",
    "pyproject.toml",
    "uv.lock",
    ".env.example",
    ".gitignore",
    ".python-version",
)

#: Never published, at any week. Each entry states why, because a bare deny-list
#: is the kind of thing somebody edits without knowing what it was protecting.
NEVER = {
    "tests": "test_checks.py holds the solved value of every exercise",
    ".github": "CI belongs to the source repo, and a partial tree fails it",
    "docs/specs": "internal design records",
    "docs/plans": "internal planning notes, superseded as often as they are written",
    "docs/instructor": "teaching notes, rubric, and the hosted-MCP checklist",
    "evals": "instructor evaluation harness",
    # `scripts/` ships, because a learner runs the doctor and the submit CLI
    # from it. This one file is the exception: its whole job is to write the
    # teaching plans and decks under `docs/instructor/`, which never travel.
    "scripts/instructor_pack.py": "it generates the teaching material",
}


#: Solutions are withheld and released one session at a time, so a learner meets
#: an exercise before its answer is a folder away — the whole point of the priced
#: hint tier. The set of released chapters is recorded in the student repo, so a
#: rebuild never silently un-releases one. Every tree under `units/` is gated,
#: week-0 units included: their worked answer is `hint(reveal=True)`, and a unit's
#: solutions can still be released by path (`--release-solutions
#: units/en/w01-environment`). The depth track keeps its own.
SOLUTIONS = "solutions"
RELEASED_SOLUTIONS_FILE = ".solutions-released"
#: Every file the last publish wrote, one path per line.
#:
#: WITHOUT IT, WITHDRAWAL IS ONLY AS FINE-GRAINED AS A DIRECTORY. `scripts/`
#: ships whole, so a script deleted from the course stayed in every student's
#: clone forever — `scripts/course_index.py` outlived its own replacement, and
#: `scripts/instructor_pack.py` travelled once before it was denied. Comparing
#: this list against what the current release writes says exactly which files to
#: remove, and touches nothing a student added themselves.
PUBLISHED_FILE = ".published"


class PublishError(Exception):
    """The publish was refused. Nothing was written."""


def solution_dir_for(token: str) -> str:
    """The solutions directory a release token names, relative to the repo.

    A chapter id (`ch03`, `3`) resolves through the curriculum, the single source
    of where a chapter lives, and so does the capstone (`cap01`). Anything else is
    taken as the path to a solutions parent directory (`units/en/w01-environment`),
    so week-0 units stay releasable without inventing a second id scheme.
    """
    stripped = token.strip()
    if stripped.lower() in {CAPSTONE.prefix, CAPSTONE.slug}:
        return f"{UNITS}/{CAPSTONE.unit}/{CAPSTONE.dirname}/{SOLUTIONS}"
    if re.fullmatch(r"(ch)?0*\d+", stripped.lower()):
        chapter = get_chapter(stripped)
        return f"{UNITS}/{chapter.unit}/{chapter.dirname}/{SOLUTIONS}"
    return f"{stripped.rstrip('/')}/{SOLUTIONS}"


def read_released_solutions(destination: Path) -> set[str]:
    """Which solution directories the student repo has already released."""
    marker = destination / RELEASED_SOLUTIONS_FILE
    if not marker.is_file():
        return set()
    return {line.strip() for line in marker.read_text().splitlines() if line.strip()}


def write_released_solutions(destination: Path, released: set[str]) -> None:
    (destination / RELEASED_SOLUTIONS_FILE).write_text(
        "".join(f"{entry}\n" for entry in sorted(released))
    )


def _is_module_solution(relative: Path) -> bool:
    """A solutions directory (or a file inside one) under a gated unit."""
    parts = relative.parts
    return len(parts) >= 2 and parts[0] == "units" and SOLUTIONS in parts


def _solution_owner(relative: Path) -> str:
    """The `<...>/solutions` path a module-solution file belongs to."""
    parts = relative.parts
    cut = parts.index(SOLUTIONS)
    return Path(*parts[: cut + 1]).as_posix()


def released_paths(week: int) -> list[str]:
    """Everything that should exist in the student repo at this week."""
    paths = list(ALWAYS)
    paths += [f"{UNITS}/_toctree.yml"]
    # `unit0` carries both the welcome pages and the twelve self-paced units.
    paths += [f"{UNITS}/{unit_dir(0)}"]
    # The one-page entries for the side tracks. Their material ships from the
    # repository root (`depth/`, `cookbook/`, ...), but the page that introduces
    # each one lives under `units/en` and was left behind once, so the contents
    # page named four groups a student did not have.
    paths += [f"{UNITS}/{name}" for name in TRACK_DIRS]
    paths += [f"{UNITS}/{name}" for name in BONUS_DIRS]
    # A whole week's directory, once that week has opened. The capstone lives
    # inside the week it opens with, so it needs no case of its own.
    paths += [f"{UNITS}/{unit_dir(open_week)}" for open_week in WEEKS if 1 <= open_week <= week]
    return paths


def _forbidden(
    relative: Path, week: int, released_solutions: frozenset[str] = frozenset()
) -> str | None:
    """Why this path must not be published, or None if it may be."""
    parts = relative.parts
    for denied, reason in NEVER.items():
        denied_parts = Path(denied).parts
        if parts[: len(denied_parts)] == denied_parts:
            return reason
    opens = week_of(relative)
    if opens is not None and opens > week:
        return f"week {opens} has not been released yet"
    if _is_module_solution(relative) and _solution_owner(relative) not in released_solutions:
        return "solutions are released per session; this chapter's has not been"
    return None


def audit(tree: Path, week: int) -> list[str]:
    """Every path in `tree` that must not be there at this week.

    Run AFTER building the tree, against what is actually on disk, rather than
    reasoning about what should have been copied. The check is only worth
    anything if it can catch a mistake in the copying itself.
    """
    problems: list[str] = []
    released = frozenset(read_released_solutions(tree))
    for path in sorted(tree.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(tree)
        if ".git" in relative.parts:
            continue  # the student repo's own checkout, not published content
        reason = _forbidden(relative, week, released)
        if reason:
            problems.append(f"{relative}: {reason}")
    return problems


#: Copied but never carried into a module chapter — solutions are added back
#: only for the released chapters, one at a time.
_COPY_IGNORE = (
    "__pycache__",
    "*.pyc",
    ".ipynb_checkpoints",
    ".venv",
    "*.egg-info",
    # gitignored, tens of thousands of files; copying it is what made a publish crawl
    "node_modules",
    ".git",
    # Deny-listed in NEVER, and `scripts/` copies as a tree, so the audit would
    # catch it only after it had been written. Skipped at the copy instead.
    "instructor_pack.py",
)


def tracked_files(source: Path) -> set[str] | None:
    """Every path git tracks in the course, or None when it is not a checkout.

    THE PUBLISH COPIES A WORKING TREE, and a working tree holds more than the
    course: build artifacts, a scratch `score_report.json`, and — the reason
    this exists — `integrations/sendai-txs/.keypair.json`, which is gitignored
    here and was copied into a student checkout anyway. Anything git does not
    track is not course material, and a secret is exactly the kind of thing that
    is gitignored.
    """
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=source,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return {entry for entry in result.stdout.split("\0") if entry}


def _untracked_filter(source: Path, tracked: set[str] | None, extra: tuple[str, ...]):
    """A `copytree` ignore callable that drops untracked files and the usual noise."""

    def ignore(directory: str, names: list[str]) -> set[str]:
        here = Path(directory)
        dropped = {name for name in names if any(fnmatch(name, pattern) for pattern in extra)}
        if tracked is None:
            return dropped
        for name in names:
            candidate = here / name
            if candidate.is_dir():
                continue
            if (candidate.relative_to(source)).as_posix() not in tracked:
                dropped.add(name)
        return dropped

    return ignore


def build(
    source: Path,
    destination: Path,
    week: int,
    released_solutions: frozenset[str] = frozenset(),
) -> tuple[list[str], list[str]]:
    """Copy the released set into `destination`. Returns (copied, skipped).

    Module solutions are withheld: the module trees copy without them, then each
    released chapter's solutions are copied back. Any module solution already in
    the student repo but not released is pruned, so tightening the policy reaches
    a student who pulled under the old one.
    """
    copied: list[str] = []
    skipped: list[str] = []
    tracked = tracked_files(source)
    for entry in released_paths(week):
        origin = source / entry
        if not origin.exists():
            skipped.append(entry)
            continue
        target = destination / entry
        target.parent.mkdir(parents=True, exist_ok=True)
        if origin.is_dir():
            # A module tree copies without any solutions; every other tree (depth,
            # workspaces) keeps its own.
            extra = _COPY_IGNORE + (SOLUTIONS,) if entry.startswith("units/") else _COPY_IGNORE
            shutil.copytree(
                origin,
                target,
                dirs_exist_ok=True,
                ignore=_untracked_filter(source, tracked, extra),
            )
        else:
            if tracked is not None and entry not in tracked:
                skipped.append(entry)
                continue
            shutil.copy2(origin, target)
        copied.append(entry)

    for owner in sorted(released_solutions):
        origin = source / owner
        if not origin.exists():
            skipped.append(owner)
            continue
        shutil.copytree(
            origin,
            destination / owner,
            dirs_exist_ok=True,
            ignore=_untracked_filter(source, tracked, _COPY_IGNORE),
        )
        copied.append(owner)

    _prune_unreleased_solutions(destination, released_solutions)
    trim_toctree(destination, week)
    annotate_missing_links(destination, week)
    return copied, skipped


def read_manifest(destination: Path) -> set[str] | None:
    """What the last publish wrote, or None if this repo predates the manifest."""
    marker = destination / PUBLISHED_FILE
    if not marker.is_file():
        return None
    return {line.strip() for line in marker.read_text().splitlines() if line.strip()}


def _ignored(relative: Path) -> bool:
    """Whether any part of this path is something a publish never copies."""
    return any(fnmatch(part, pattern) for part in relative.parts for pattern in _COPY_IGNORE)


def shipped_files(
    source: Path, week: int, released_solutions: frozenset[str] = frozenset()
) -> set[str]:
    """Exactly the files this release writes into a student repo.

    Computed from what git TRACKS, not from what sits on either disk. This is
    what makes withdrawal exact: a file the last release wrote and this one does
    not is a file the course removed, and a file a student created was never in
    it. It is also why an untracked artifact — a build output, a scratch report,
    a gitignored keypair — cannot appear in a manifest and cannot be shipped.
    """
    tracked = tracked_files(source)
    if tracked is None:
        return set()
    entries = released_paths(week)
    shipped = set()
    for name in tracked:
        relative = Path(name)
        if _ignored(relative):
            continue
        if not any(name == entry or name.startswith(f"{entry}/") for entry in entries):
            continue
        if _is_module_solution(relative) and _solution_owner(relative) not in released_solutions:
            continue
        if _forbidden(relative, week, released_solutions) is not None:
            continue
        shipped.add(name)
    return shipped


def write_manifest(destination: Path, files: set[str]) -> None:
    (destination / PUBLISHED_FILE).write_text("".join(f"{entry}\n" for entry in sorted(files)))


def trim_toctree(destination: Path, week: int) -> list[str]:
    """Drop table-of-contents groups whose pages this week does not ship.

    THE SHIPPED CONTENTS MUST MATCH THE SHIPPED TREE. The generated toctree
    names every page in the course, all 15 sessions included, and a student
    holding week 0 has a fraction of them. Left whole, their contents page lists
    entries that resolve to nothing, which reads as a broken repository rather
    than as a course that has not opened yet.

    So the groups go, and a comment says what is coming and when — the schedule
    itself lives in the README's release table, which every student has on day
    one. Returns the titles that were withheld.
    """
    toctree = destination / UNITS / "_toctree.yml"
    if not toctree.is_file():
        return []

    lines = toctree.read_text(encoding="utf-8").splitlines()
    groups: list[list[str]] = []
    header: list[str] = []
    for line in lines:
        if line.startswith("- title:"):
            groups.append([line])
        elif groups:
            groups[-1].append(line)
        else:
            header.append(line)

    kept: list[list[str]] = []
    withheld: list[str] = []
    for group in groups:
        locals_ = [
            line.split("local:", 1)[1].strip()
            for line in group
            if line.strip().startswith("- local:")
        ]
        present = [local for local in locals_ if (destination / UNITS / f"{local}.mdx").is_file()]
        if locals_ and not present:
            withheld.append(group[0].split("title:", 1)[1].strip().strip('"'))
            continue
        if len(present) < len(locals_):
            # A partly-shipped group keeps only the pages that are actually here.
            trimmed = [group[0], "  sections:"]
            keep = False
            for line in group[1:]:
                if line.strip().startswith("- local:"):
                    keep = line.split("local:", 1)[1].strip() in present
                elif not line.strip().startswith("title:"):
                    keep = False
                if keep:
                    trimmed.append(line)
            group = trimmed
        kept.append(group)

    out = list(header)
    for group in kept:
        out.extend(group)
    if withheld:
        out.append("")
        out.append("# Not in this repository yet. Each arrives on its Monday and")
        out.append("# `git pull` brings it; the dates are in the README.")
        for title in withheld:
            out.append(f"#   {title}")
    toctree.write_text("\n".join(out) + "\n", encoding="utf-8")
    return withheld


#: EVERY published markdown document, found rather than listed.
#:
#: A hand-list is the wrong shape here and was wrong twice: `AGENTS.md` shipped
#: linking to the deny-listed `tests/`, and `docs/curriculum.md` shipped linking
#: into fifteen sessions a week-0 student does not have. Any document written
#: against the full tree has this problem, so the rule is the whole set.
#:
#: `.mdx` pages are NOT in it. Those move with their unit, so their relative
#: links stay correct, and the site generator already refuses a broken one.
ANNOTATED_SUFFIX = ".md"


def _absent_note(target: str, destination: Path) -> str | None:
    """Why this link's target is not in the student's copy, or None if it is.

    Three answers, and the difference matters to whoever reads it: it opens on a
    date, it is withheld from every week, or it is simply not there.
    """
    relative = target.rstrip("/").lstrip("./")
    while relative.startswith("../"):
        relative = relative[3:]
    if (destination / relative).exists():
        return None
    # EVERY segment, not just the last. A link to a page INSIDE an unreleased
    # session ends in `introduction.mdx`, and matching only the tail lost the
    # date and said the uselessly vague "not released yet" instead.
    segments = relative.split("/")
    for chapter in CHAPTERS:
        if chapter.dirname in segments:
            return f" — opens {chapter.weekday}"
    if CAPSTONE.dirname in segments:
        return f" — opens with week {CAPSTONE.opens_in_week}"
    for denied in NEVER:
        if relative == denied or relative.startswith(f"{denied}/"):
            return " — not in your copy"
    return " — not released yet"


def annotate_missing_links(destination: Path, week: int) -> int:
    """Unwrap links whose target this week does not ship, saying why.

    THE SAME FAILURE IN EVERY DOCUMENT A STUDENT OPENS. `README.md` links to all
    fifteen sessions and `docs/course-index.md` names each one; in week 0 those
    are eighteen links to nothing, which reads as a broken clone rather than as
    a course that has not opened. The row is worth keeping — it is where a
    learner sees the whole shape — so the link is unwrapped, not deleted, and
    the reason replaces it. Returns how many were rewritten.
    """
    changed = 0

    def unwrap(match: re.Match[str]) -> str:
        nonlocal changed
        title, target = match.group(1), match.group(2)
        note = _absent_note(target, destination)
        if note is None:
            return match.group(0)
        changed += 1
        return f"{title}{note}"

    documents = sorted(
        path
        for path in destination.rglob(f"*{ANNOTATED_SUFFIX}")
        if path.is_file()
        and ".git" not in path.parts
        and not _ignored(path.relative_to(destination))
    )
    for document in documents:
        text = document.read_text(encoding="utf-8")
        # Line by line, so a row that already carries the date is not told it
        # twice: both documents put sessions in a table with a date column.
        lines = []
        for line in text.split("\n"):
            # Skip code spans: `tools[name](**args)` is not a link, however much
            # it looks like one to a regular expression.
            rewritten_line = re.sub(
                r"(?<!`)\[([^\]]+)]\((?!https?:|#|mailto:)([^)]+)\)",
                unwrap,
                line,
            )
            for chapter in CHAPTERS:
                stamp = f" — opens {chapter.weekday}"
                if stamp in rewritten_line and rewritten_line.count(chapter.weekday) > 1:
                    rewritten_line = rewritten_line.replace(stamp, " — not yet")
            lines.append(rewritten_line)
        rewritten = "\n".join(lines)
        if rewritten != text:
            document.write_text(rewritten, encoding="utf-8")
    return changed


def _prune_unreleased_solutions(destination: Path, released_solutions: frozenset[str]) -> None:
    """Remove any unit solutions directory the release set does not name."""
    modules = destination / "units"
    if not modules.is_dir():
        return
    for candidate in modules.rglob(SOLUTIONS):
        if not candidate.is_dir():
            continue
        owner = candidate.relative_to(destination).as_posix()
        if owner not in released_solutions:
            shutil.rmtree(candidate)


def _prune_empty_dirs(destination: Path) -> None:
    """Drop directories a withdrawal emptied, so a withheld week leaves no husk."""
    for path in sorted(destination.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and ".git" not in path.parts and not any(path.iterdir()):
            path.rmdir()


def _stale(
    destination: Path,
    week: int,
    source: Path = ROOT,
    released_solutions: frozenset[str] = frozenset(),
) -> list[Path]:
    """Files in the student repo that this week's release no longer includes.

    A publish that only adds would leave a withdrawn file behind forever, so a
    correction to the course would never reach a student who already pulled.
    """
    allowed = {Path(entry) for entry in released_paths(week)}
    previous = read_manifest(destination) or set()
    now = shipped_files(source, week, released_solutions)
    stale: list[Path] = []
    for path in destination.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(destination)
        if relative.as_posix() in {RELEASED_SOLUTIONS_FILE, PUBLISHED_FILE}:
            continue  # our own ledgers, generated here, not course content
        outside = not any(relative == entry or entry in relative.parents for entry in allowed)
        # Shipped by a previous publish and not written by this one. That is a
        # file the course deleted, and it is the only case where a file INSIDE a
        # released directory may be removed — a student's own work never appears
        # in the manifest, so it is never touched.
        withdrawn = relative.as_posix() in previous and relative.as_posix() not in now
        # A deny-listed file already in the destination. Refusing to publish is
        # not enough on its own: the audit would then refuse every publish
        # forever, and the file would sit there while it did.
        denied = _forbidden(relative, week) is not None
        if outside or withdrawn or denied:
            stale.append(relative)
    return stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", type=int, required=True, choices=WEEKS)
    parser.add_argument(
        "--into",
        type=Path,
        help="checkout of the student repo (default: ../dev3pack-cohort-2026-09)",
    )
    parser.add_argument(
        "--release-solutions",
        nargs="+",
        default=[],
        metavar="CHAPTER",
        help="also release these chapters' solutions (e.g. ch03), added to any already released",
    )
    parser.add_argument(
        "--commit", action="store_true", help="actually write and commit; otherwise dry run"
    )
    args = parser.parse_args(argv)

    destination = args.into or ROOT.parent / "dev3pack-cohort-2026-09"

    # Resolve the requested solutions and refuse any whose week is not open — a
    # solution cannot ship before the exercise it answers.
    newly = {solution_dir_for(token) for token in args.release_solutions}
    for owner in sorted(newly):
        number = week_of(Path(owner)) or 0
        if number > args.week:
            raise PublishError(
                f"{owner}: its week ({number}) is not released yet, so its solutions cannot be"
            )
    already = read_released_solutions(destination) if destination.exists() else set()
    released_solutions = frozenset(already | newly)

    print(f"publishing week {args.week} -> {destination}")
    opened = [chapter.dirname for chapter in CHAPTERS if chapter.module <= args.week]
    withheld = [chapter.dirname for chapter in CHAPTERS if chapter.module > args.week]
    if args.week >= CAPSTONE.opens_in_week:
        opened.append(CAPSTONE.dirname)
    else:
        withheld.append(CAPSTONE.dirname)
    print(f"  released: week 0, unit 0, bonus, {', '.join(opened) or 'no sessions'}")
    print(f"  withheld: {', '.join(withheld) or 'nothing'}")
    print(f"  excluded always: {', '.join(sorted(NEVER))}")
    print(
        "  solutions released: "
        + (", ".join(sorted(released_solutions)) if released_solutions else "none")
    )

    if not args.commit:
        print("\nDry run. Nothing written. Re-run with --commit to publish.")
        return 0

    if not (destination / ".git").is_dir():
        raise PublishError(
            f"{destination} is not a git checkout. Clone the student repo there first:\n"
            f"  git clone git@github.com:{STUDENT_REPO}.git {destination}"
        )

    write_released_solutions(destination, set(released_solutions))
    copied, missing = build(ROOT, destination, args.week, released_solutions)
    if missing:
        print(f"\n  not present in source, skipped: {', '.join(missing)}")

    # Withdraw first, audit second. A previous publish may have left a now-
    # withheld week on disk (going from week 1 back to week 0), and the audit
    # must judge what this release leaves behind, not what the last one did.
    first_manifest = read_manifest(destination) is None
    withdrawn = _stale(destination, args.week, ROOT, released_solutions)
    for relative in withdrawn:
        (destination / relative).unlink()
    _prune_empty_dirs(destination)
    if withdrawn:
        print(f"\n  withdrew {len(withdrawn)} file(s) no longer in the release")

    write_manifest(destination, shipped_files(ROOT, args.week, released_solutions))
    if first_manifest:
        # Before the manifest existed, a file the course deleted could only be
        # withdrawn if its whole directory was withheld. Anything that slipped
        # through is named here once, for a human to decide on.
        expected = shipped_files(ROOT, args.week, released_solutions)
        ledgers = {PUBLISHED_FILE, RELEASED_SOLUTIONS_FILE}
        orphans = sorted(
            path.relative_to(destination).as_posix()
            for path in destination.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and not _ignored(path.relative_to(destination))
            and path.relative_to(destination).as_posix() not in expected | ledgers
        )
        if orphans:
            print("\n  in the student repo and not in the course — check each:")
            for entry in orphans:
                print(f"    {entry}")

    problems = audit(destination, args.week)
    if problems:
        raise PublishError(
            "REFUSED. These would have been published and must not be:\n  "
            + "\n  ".join(problems[:20])
            + (f"\n  ... and {len(problems) - 20} more" if len(problems) > 20 else "")
        )

    print(f"\n  {len(copied)} top-level entries copied, audit clean")
    subprocess.run(["git", "add", "-A"], cwd=destination, check=True)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=destination,
        capture_output=True,
        text=True,
        check=True,
    )
    if not status.stdout.strip():
        print("  nothing changed; the student repo is already at this week")
        return 0
    message = f"week {args.week}"
    if newly:
        message += f" + solutions: {', '.join(sorted(newly))}"
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=destination,
        check=True,
    )
    print(f"\nCommitted. Push it when you are ready:\n  git -C {destination} push")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublishError as error:
        print(f"\n{error}", file=sys.stderr)
        raise SystemExit(1) from error
