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
  - an unreleased `modules/module-N/` is the staging itself.

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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The student repository, named once. It also appears in SETUP.md, README.md
#: and the instructor runbook, and `tests/test_publish.py` asserts all four
#: agree — four files each hardcoding the same slug is how a rename half-lands,
#: which is exactly what happened when this said "Scoras-Academy".
STUDENT_REPO = "Gecko-Academy/dev3pack-cohort-2026-09"

#: Weeks, and the chapter directories each one opens.
WEEK_MODULES = {
    0: "modules/module-0",
    1: "modules/module-1",
    2: "modules/module-2",
    3: "modules/module-3",
}

#: Ships whole, on day one, whatever week it is. Every one of these is either
#: shared by all three weeks or reached across weeks (chapter 05 of week 1 links
#: into `cookbook/integrations/11`), so partitioning them breaks week 1.
ALWAYS = (
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
}


#: Solutions are withheld and released one session at a time, so a learner meets
#: an exercise before its answer is a folder away — the whole point of the priced
#: hint tier. The set of released chapters is recorded in the student repo, so a
#: rebuild never silently un-releases one. Every tree under `modules/` is gated,
#: week-0 units included: their worked answer is `hint(reveal=True)`, and a unit's
#: solutions can still be released by path (`--release-solutions
#: modules/module-0/unit-01-environment`). The depth track keeps its own.
SOLUTIONS = "solutions"
RELEASED_SOLUTIONS_FILE = ".solutions-released"


class PublishError(Exception):
    """The publish was refused. Nothing was written."""


def solution_dir_for(token: str) -> str:
    """The solutions directory a release token names, relative to the repo.

    A chapter id (`ch03`, `3`) resolves through the curriculum, the single source
    of where a chapter lives. Anything else is taken as the path to a solutions
    parent directory (`modules/module-0/unit-01-environment`), so week-0 units
    stay releasable without inventing a second id scheme.
    """
    stripped = token.strip()
    if re.fullmatch(r"(ch)?0*\d+", stripped.lower()):
        from bootcamp_agent.curriculum import get_chapter

        chapter = get_chapter(stripped)
        return f"modules/module-{chapter.module}/chapter-{chapter.number:02d}/{SOLUTIONS}"
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
    """A solutions directory (or a file inside one) under a module chapter."""
    parts = relative.parts
    return len(parts) >= 2 and parts[0] == "modules" and SOLUTIONS in parts


def _solution_owner(relative: Path) -> str:
    """The `<...>/solutions` path a module-solution file belongs to."""
    parts = relative.parts
    cut = parts.index(SOLUTIONS)
    return Path(*parts[: cut + 1]).as_posix()


def released_paths(week: int) -> list[str]:
    """Everything that should exist in the student repo at this week."""
    paths = list(ALWAYS)
    for number, directory in sorted(WEEK_MODULES.items()):
        if number <= week:
            paths.append(directory)
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
    for number, directory in WEEK_MODULES.items():
        if number > week and parts[: len(Path(directory).parts)] == Path(directory).parts:
            return f"week {number} has not been released yet"
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
)


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
            ignore = _COPY_IGNORE + (SOLUTIONS,) if entry.startswith("modules/") else _COPY_IGNORE
            shutil.copytree(
                origin,
                target,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(*ignore),
            )
        else:
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
            ignore=shutil.ignore_patterns(*_COPY_IGNORE),
        )
        copied.append(owner)

    _prune_unreleased_solutions(destination, released_solutions)
    return copied, skipped


def _prune_unreleased_solutions(destination: Path, released_solutions: frozenset[str]) -> None:
    """Remove any module solutions directory the release set does not name."""
    modules = destination / "modules"
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


def _stale(destination: Path, week: int) -> list[Path]:
    """Files in the student repo that this week's release no longer includes.

    A publish that only adds would leave a withdrawn file behind forever, so a
    correction to the course would never reach a student who already pulled.
    """
    allowed = {Path(entry) for entry in released_paths(week)}
    stale: list[Path] = []
    for path in destination.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(destination)
        if relative == Path(RELEASED_SOLUTIONS_FILE):
            continue  # the release ledger, generated here, not course content
        if not any(relative == entry or entry in relative.parents for entry in allowed):
            stale.append(relative)
    return stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", type=int, required=True, choices=sorted(WEEK_MODULES))
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
        module = Path(owner).parts[1]  # module-N
        number = int(module.split("-")[1])
        if number > args.week:
            raise PublishError(
                f"{owner}: its week ({number}) is not released yet, so its solutions cannot be"
            )
    already = read_released_solutions(destination) if destination.exists() else set()
    released_solutions = frozenset(already | newly)

    print(f"publishing week {args.week} -> {destination}")
    print(
        f"  released: {', '.join(WEEK_MODULES[n] for n in sorted(WEEK_MODULES) if n <= args.week)}"
    )
    withheld = [WEEK_MODULES[n] for n in sorted(WEEK_MODULES) if n > args.week]
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
    withdrawn = _stale(destination, args.week)
    for relative in withdrawn:
        (destination / relative).unlink()
    _prune_empty_dirs(destination)
    if withdrawn:
        print(f"\n  withdrew {len(withdrawn)} file(s) no longer in the release")

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
