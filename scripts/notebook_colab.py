"""Make every notebook openable in Google Colab, and say so at the top.

    uv run python scripts/notebook_colab.py            # write the badge + bootstrap
    uv run python scripts/notebook_colab.py --check     # CI: fail if any drifted

WHY. A learner with no GPU, or no laptop to hand, reaches the course through
Colab. Opened there, every notebook died on its first cell: the preflight walks
up from `Path.cwd()` looking for `pyproject.toml`, Colab starts in `/content`
with no course in it, the walk reaches `/`, and the import branch printed

    ❌ bootcamp_agent not importable -> in the repo root run: uv sync --group dev

which names a repo root that does not exist on that machine. A dead end, and
the one lane a beginner is most likely to try first.

GENERATED, BECAUSE FIFTY COPIES DRIFT. The preflight cell is hand-written per
notebook and already exists in six variants -- principled ones (week-0 units
have no corpus, two sessions carry a fixture helper, two are assistant-driven),
but six all the same. Only the shared parts are rewritten here, so those
differences survive; and the next change to the bootstrap is one edit rather
than fifty.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNITS = ROOT / "units" / "en"

#: The published repository a learner actually has. Colab opens from GitHub, and
#: the source repository is private, so this is the only URL that can work.
COHORT = "Gecko-Academy/dev3pack-cohort-2026-09"
COLAB = f"https://colab.research.google.com/github/{COHORT}/blob/main"

#: The dead end, byte-identical in all fifty notebooks.
OLD = (
    "except ImportError:\n"
    '    print("❌ bootcamp_agent not importable -> in the repo root run: uv sync --group dev")\n'
    '    print("   then pick the .venv kernel (or start Jupyter with: uv run jupyter lab)")'
)

#: What replaces it. Local behaviour is unchanged -- same message, same advice --
#: and Colab gets the one thing it was missing: the course itself.
NEW = """except ImportError:
    if "google.colab" in sys.modules:
        # Colab starts in /content with no course in it, so fetch one. A shallow
        # clone of the COHORT repository, which is the public one; the source
        # repository is private and would ask this learner for credentials.
        import subprocess

        target = Path("/content/dev3pack")
        if not (target / "pyproject.toml").exists():
            print("Colab detected — fetching the course (about 20 seconds)…")
            subprocess.run(
                ["git", "clone", "-q", "--depth", "1",
                 "https://github.com/COHORT_SLUG.git", str(target)],
                check=True,
            )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-e", str(target)], check=True
        )
        REPO_ROOT = target
        sys.path.insert(0, str(REPO_ROOT / "src"))
        import os

        os.chdir(REPO_ROOT)
        from bootcamp_agent.preflight import preflight

        print(f"ready — the course is at {REPO_ROOT}")
    else:
        print("❌ bootcamp_agent not importable -> in the repo root run: uv sync --group dev")
        print("   then pick the .venv kernel (or start Jupyter with: uv run jupyter lab)")"""
NEW = NEW.replace("COHORT_SLUG", COHORT)


#: A SECOND preflight, in four notebooks, and strictly worse. Its walk has no
#: `REPO_ROOT != REPO_ROOT.parent` guard, so where the canonical one gives up and
#: prints advice, this one loops on `/` forever: on Colab the notebook simply
#: hangs, which is harder to diagnose than any error message. It also imports
#: without a `try`, so a missing venv raises a traceback instead of the sentence
#: that says what to run. Both are replaced by the canonical form below.
UNGUARDED = (
    "# preflight\n"
    "from pathlib import Path\n"
    "import sys\n"
    "REPO_ROOT = Path.cwd()\n"
    "while not (REPO_ROOT / 'pyproject.toml').is_file():\n"
    "    REPO_ROOT = REPO_ROOT.parent\n"
    "sys.path.insert(0, str(REPO_ROOT / 'src'))\n"
    "from bootcamp_agent.checks import check, review\n"
)

CANONICAL = (
    "# Preflight: environment checks with a fix for anything missing. It never raises.\n"
    "import sys\n"
    "from pathlib import Path\n"
    "\n"
    "REPO_ROOT = Path.cwd()\n"
    'while not (REPO_ROOT / "pyproject.toml").exists() and REPO_ROOT != REPO_ROOT.parent:\n'
    "    REPO_ROOT = REPO_ROOT.parent\n"
    'sys.path.insert(0, str(REPO_ROOT / "src"))\n'
    "\n"
    "try:\n"
    "    from bootcamp_agent.preflight import preflight\n" + NEW + "\nelse:\n"
    "    preflight(REPO_ROOT)\n"
    "\n"
    "from bootcamp_agent.checks import check, review\n"
)

BADGE_MARK = "<!-- colab-badge -->"


def badge_for(notebook: Path) -> str:
    """The Open-in-Colab line for one notebook, pointing at the cohort repo."""
    relative = notebook.relative_to(ROOT).as_posix()
    return (
        f"{BADGE_MARK}\n"
        f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]"
        f"({COLAB}/{relative})\n"
    )


def notebooks() -> list[Path]:
    """Every notebook a learner opens, solutions included.

    Solutions are published one session at a time, and when one IS released a
    learner opens it the same way as any other page.

    Jupyter's own checkpoints are skipped, as `check_notebooks` and
    `notebook_index` already skip them. They are gitignored copies nobody opens,
    and without this the `--check` fails for anyone who has opened a notebook
    locally -- a red build caused entirely by the editor.
    """
    return sorted(path for path in UNITS.rglob("*.ipynb") if ".ipynb_checkpoints" not in path.parts)


def _lines(source: object) -> list[str]:
    return source if isinstance(source, list) else str(source).splitlines(keepends=True)


def retarget(notebook: Path) -> tuple[bool, str | None]:
    """Give one notebook the badge and the Colab bootstrap.

    Returns (changed, problem). A notebook with no preflight cell is a problem
    worth naming rather than skipping: it is the cell that makes the rest run.
    """
    document = json.loads(notebook.read_text(encoding="utf-8"))
    cells = document["cells"]
    changed = False

    preflight = next(
        (
            c
            for c in cells
            if "Preflight: environment checks" in "".join(_lines(c["source"]))
            # `.strip()`: one of the four lacks the trailing newline, and a
            # byte-exact match silently left that notebook hanging on Colab.
            or "".join(_lines(c["source"])).strip() == UNGUARDED.strip()
        ),
        None,
    )
    if preflight is None:
        return False, f"{notebook.relative_to(ROOT)}: no preflight cell"

    body = "".join(_lines(preflight["source"]))
    if body.strip() == UNGUARDED.strip():
        preflight["source"] = CANONICAL.splitlines(keepends=True)
        body = CANONICAL
        changed = True
    if OLD in body:
        preflight["source"] = (body.replace(OLD, NEW)).splitlines(keepends=True)
        changed = True
    elif NEW not in body:
        return False, f"{notebook.relative_to(ROOT)}: preflight has drifted; neither form found"

    wanted = badge_for(notebook)
    first = "".join(_lines(cells[0]["source"])) if cells else ""
    if cells and cells[0]["cell_type"] == "markdown" and BADGE_MARK in first:
        if first.strip() != wanted.strip():
            cells[0]["source"] = wanted.splitlines(keepends=True)
            changed = True
    else:
        cells.insert(
            0,
            {
                "cell_type": "markdown",
                # nbformat 4.5 requires an id on every cell. Without one, every
                # `bootcamp check`, `progress` and `submit` printed
                # `MissingIDFieldWarning: … will become a hard error`, which is
                # a frightening thing to show a learner for a badge.
                "id": "colab-badge",
                "metadata": {},
                "source": wanted.splitlines(keepends=True),
            },
        )
        changed = True

    if changed:
        notebook.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", "utf-8")
    return changed, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if anything would change")
    args = parser.parse_args(argv)

    found = notebooks()
    if not found:
        print("no notebooks under units/en", file=sys.stderr)
        return 1

    if args.check:
        stale, problems = [], []
        for notebook in found:
            document = json.loads(notebook.read_text(encoding="utf-8"))
            cells = document["cells"]
            body = "".join(
                "".join(_lines(c["source"]))
                for c in cells
                if "Preflight: environment checks" in "".join(_lines(c["source"]))
            )
            first = "".join(_lines(cells[0]["source"])) if cells else ""
            if not body:
                problems.append(f"{notebook.relative_to(ROOT)}: no preflight cell")
            elif NEW not in body or BADGE_MARK not in first:
                stale.append(str(notebook.relative_to(ROOT)))
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        for path in stale:
            print(f"  stale: {path}", file=sys.stderr)
        if stale or problems:
            print("\nre-run: uv run python scripts/notebook_colab.py", file=sys.stderr)
            return 1
        print(f"colab ready: {len(found)} notebooks")
        return 0

    touched, problems = 0, []
    for notebook in found:
        changed, problem = retarget(notebook)
        touched += int(changed)
        if problem:
            problems.append(problem)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    print(f"colab: {touched} of {len(found)} notebooks updated")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
