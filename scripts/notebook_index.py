"""Generate docs/notebook-index.md: what every notebook is, and where it starts.

    uv run python scripts/notebook_index.py
    uv run python scripts/notebook_index.py --check   # CI: fail if it is stale

TRANSPORT ONLY. Everything here is READ OUT OF THE NOTEBOOKS. The goal line, the
exercise ids and the opening code example are extracted, never retyped, because
a hand-written index of forty notebooks is stale the first time somebody edits
one and nobody notices for a month.

WHAT EACH ENTRY CARRIES, and why those three things:

    guidance     the notebook's own Goal line, so a learner can tell from the
                 index whether this is the one they want
    explanation  what it teaches and what it costs them, in the notebook's own
                 words rather than a summary of them
    a start      the first real code cell, so the index answers "what does this
                 actually look like" without opening anything

The preflight and the import cell are skipped when choosing that example: every
notebook opens with the same four lines, and printing them forty times would
tell a reader nothing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

OUTPUT = ROOT / "docs" / "notebook-index.md"


def collections() -> tuple[tuple[tuple[str, ...], str, str], ...]:
    """Where notebooks live, and what each collection is for.

    Read from the curriculum rather than typed, because the layout is one
    directory per unit and the grouping (week 0, week 1, ...) is a fact the
    curriculum already holds.
    """
    from bootcamp_agent.curriculum import CAPSTONE, CHAPTERS, WEEK0_UNITS, WEEK_TITLES

    groups: list[tuple[tuple[str, ...], str, str]] = [
        (
            tuple(f"units/en/{unit.dirname}" for unit in WEEK0_UNITS),
            "Week 0 — the prerequisite",
            "Self-paced, before session 1.",
        )
    ]
    for week, title in sorted(WEEK_TITLES.items()):
        chapters = [chapter for chapter in CHAPTERS if chapter.module == week]
        groups.append(
            (
                tuple(f"units/en/{chapter.dirname}" for chapter in chapters),
                f"Week {week} — {title}",
                f"Sessions {chapters[0].number} to {chapters[-1].number}.",
            )
        )
    groups += [
        ((f"units/en/{CAPSTONE.dirname}",), "Capstone", "Built between sessions, from week 2."),
        (("depth",), "Depth track — optional", "Software engineering fundamentals. Ungraded."),
        (("cookbook",), "Cookbook", "Gecko reference notebooks, not part of any week."),
        (("workspaces",), "Workspaces", "Open-ended labs, one per week."),
    ]
    return tuple(groups)


GOAL = re.compile(r"\*\*Goal:\*\*\s*(.+?)(?:\n\n|\Z)", re.S)
TITLE = re.compile(r"^#\s+(.+)$", re.M)
CHECK = re.compile(r'check\(\s*["\']([\w-]+)["\']')
#: Cells every notebook opens with. Skipped when picking the example.
BOILERPLATE = ("preflight", "REPO_ROOT = Path.cwd()", "from bootcamp_agent.checks import")


def _cells(notebook: Path) -> list[tuple[str, str]]:
    data = json.loads(notebook.read_text(encoding="utf-8"))
    out = []
    for cell in data.get("cells", []):
        source = "".join(cell.get("source", []))
        out.append((cell.get("cell_type", ""), source))
    return out


def describe(notebook: Path) -> dict[str, object]:
    """Everything the index says about one notebook, read from the notebook."""
    cells = _cells(notebook)
    markdown = [text for kind, text in cells if kind == "markdown"]
    code = [text for kind, text in cells if kind == "code"]

    header = markdown[0] if markdown else ""
    title_match = TITLE.search(header)
    goal_match = GOAL.search(header)

    example = ""
    for text in code:
        if any(marker in text for marker in BOILERPLATE):
            continue
        if text.strip().startswith("check(") or text.strip().startswith("review("):
            continue
        example = text.strip()
        break

    return {
        "path": notebook.relative_to(ROOT).as_posix(),
        "title": title_match.group(1).strip() if title_match else notebook.parent.name,
        "goal": " ".join((goal_match.group(1) if goal_match else "").split()),
        "exercises": sorted({found for text in code for found in CHECK.findall(text)}),
        "example": example,
    }


def notebooks_under(directory: Path) -> list[Path]:
    """Exercise notebooks only. A `solutions/` copy is the same entry, answered."""
    return sorted(
        path
        for path in directory.rglob("notebook.ipynb")
        if "solutions" not in path.parts and ".ipynb_checkpoints" not in path.parts
    ) + sorted(
        path
        for path in directory.rglob("*.ipynb")
        if path.name != "notebook.ipynb"
        and "solutions" not in path.parts
        and ".ipynb_checkpoints" not in path.parts
    )


def render() -> str:
    lines = [
        "<!-- generated by scripts/notebook_index.py — edit the notebooks, not this file -->",
        "",
        "# Notebook index",
        "",
        "Every notebook in the course: what it is for, what it checks, and the first",
        "real cell so you can see what it looks like before opening it.",
        "",
        "Each entry's goal and opening example are read out of the notebook itself, so",
        "this file cannot drift from what it describes. Every notebook with exercises has",
        "a `solutions/notebook.ipynb` beside it.",
        "",
        '**Stuck on an exercise?** `check(...)` names the fix for free, `hint("id")` costs',
        '30 marks, and `hint("id", reveal=True)` shows the answer. Nothing is ever locked.',
        "",
    ]

    total = 0
    for relatives, heading, blurb in collections():
        found = [
            notebook
            for relative in relatives
            if (ROOT / relative).is_dir()
            for notebook in notebooks_under(ROOT / relative)
        ]
        if not found:
            continue
        lines += [f"## {heading}", "", blurb, ""]
        for notebook in found:
            entry = describe(notebook)
            total += 1
            lines += [f"### {entry['title']}", ""]
            lines.append(f"`{entry['path']}`")
            lines.append("")
            if entry["goal"]:
                lines += [str(entry["goal"]), ""]
            exercises = entry["exercises"]
            if exercises:
                lines += [
                    f"**Checks {len(exercises)}:** " + ", ".join(f"`{e}`" for e in exercises),
                    "",
                ]
            else:
                lines += ["**No checked exercises.** Reference material.", ""]
            if entry["example"]:
                lines += ["Starts with:", "", "```python", str(entry["example"]), "```", ""]
    lines += ["---", "", f"{total} notebooks.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit non-zero if stale")
    args = parser.parse_args(argv)

    rendered = render()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if current != rendered:
            print(f"{OUTPUT.relative_to(ROOT)} is stale; regenerate it:", file=sys.stderr)
            print("  uv run python scripts/notebook_index.py", file=sys.stderr)
            return 1
        print(f"{OUTPUT.relative_to(ROOT)} is current")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
