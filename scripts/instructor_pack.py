"""Generate the instructor pack: one teaching plan and one deck per session.

    uv run python scripts/instructor_pack.py            # write them
    uv run python scripts/instructor_pack.py --check    # CI: fail if stale

FOR US, NEVER FOR STUDENTS. Everything here lands under `docs/instructor/`,
which is on the publisher's deny list, so none of it can reach a cohort repo.
The quiz answers alone make that non-negotiable.

TWO KINDS OF CONTENT IN ONE FILE, and the split is the whole design. Between
`generated:start` and `generated:end` is what the session already says about
itself: its outcome, its concept pages, its exercises, its quiz answers, its
file paths. That block is derived on every run, so a plan cannot drift from the
material it teaches. Everything outside the markers — the run of show, the demo,
the traps, what to cut when you are behind — is yours, and no run touches it.

The deck is the same arrangement: a generated spine of slides that follows the
concept pages, and your own slides wherever you add them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bootcamp_agent.curriculum import (  # noqa: E402
    CAPSTONE,
    CHAPTERS,
    WEEK_TITLES,
    exercise_ids,
)
from bootcamp_agent.hints import FULL_MARKS  # noqa: E402

PACK = ROOT / "docs" / "instructor" / "sessions"
START = "<!-- generated:start -->"
END = "<!-- generated:end -->"

HEADING = re.compile(r"^#\s+(.+?)\s*(?:\[\[[^\]]*\]\])?\s*$", re.M)
SUBHEADING = re.compile(r"^##\s+(.+?)\s*$", re.M)
QUESTION = re.compile(r"^###\s+(Q\d+):\s*(.+?)\s*$", re.M)
CORRECT = re.compile(r'\{\s*text:\s*"((?:[^"\\]|\\.)*)".*?correct:\s*true', re.S)


#: The per-session watchpoint, re-keyed to the sessions as they now stand.
#:
#: These were written against the OLD chapter numbers and moved with their
#: content on 2026-09-09 (`docs/instructor/id-migration.md` has the mapping).
#: Two did not move with content and are placed by the calendar instead, because
#: that is what they are about: the first class is where environments are not
#: ready, and the last is where demos overrun. Sessions with no entry never had
#: one — they are the two sessions that did not exist before the re-sequence.
WATCHPOINTS: dict[str, tuple[str, str]] = {
    "ch01": (
        "Environments not ready despite SETUP.md, and assistants differ "
        "(Claude Code / Cursor / Codex).",
        "First 10 minutes: doctor screenshots on screen; helpers fix stragglers "
        "during the lab, never during the lecture. Teach the policy file, demo "
        "in ONE assistant, let pairs translate. Do not demo all three.",
    ),
    "ch02": (
        "The Python level spread is widest here.",
        "The diagnostic sorts the pairs. Strong learners get the extension: add "
        "a third failure-mode test.",
    ),
    "ch03": (
        "Learners equate JSON mode with correctness.",
        "Show a valid-JSON-wrong-answer case explicitly. That is why citations "
        "get verified two sessions later.",
    ),
    "ch04": (
        '"Why not give it write tools?"',
        "Answer with blast radius, show the read-only registry, and point "
        "forward at session 13's fork story.",
    ),
    "ch06": (
        "Learners want embeddings on day one.",
        "Hold the line: the lexical baseline first, embeddings only after "
        "session 7 measures what they would buy.",
    ),
    "ch07": (
        "Metric soup.",
        'Only hit rate and "fewer, better passages". Precision and recall stay conceptual today.',
    ),
    "ch08": (
        "Reflection-mania.",
        "The eval decides. One revision cap, measure it, and most will see "
        "marginal gains — that IS the lesson.",
    ),
    "ch09": (
        "Evaluator false positives go unnoticed.",
        "Plant one: a case that passes for the wrong reason. Finding it is part of the lab.",
    ),
    "ch10": (
        "Skills become prompt dumps.",
        "Enforce the SKILL.md sections — when to use, failure rules. "
        "Before-and-after evidence is required.",
    ),
    "ch11": (
        "Memory scope creep.",
        "The whole lab is ONE preference, ONE episode, and a reset. Refuse more.",
    ),
    "ch13": (
        "The hosted MCP surface.",
        "Read `../chapter-13-hosted-mcp-checklist.md` TWICE, days before. It "
        "carries the fallback ladder.",
    ),
    "ch14": (
        "Learners fix all four clinic failures superficially.",
        "One failure fixed WITH a rerun eval beats four patched blind. Grade the rerun.",
    ),
    "ch15": (
        "Demos overrun.",
        "A visible timer, a hard 6 minutes, no exceptions — rehearsed in session 14's homework.",
    ),
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _section(text: str, name: str) -> str:
    """One `## name` section's body, stopping at the next heading of any level."""
    match = re.search(rf"^##\s+{re.escape(name)}\s*$", text, re.M)
    if not match:
        return ""
    rest = text[match.end() :]
    following = re.search(r"^#{1,3}\s+", rest, re.M)
    return (rest[: following.start()] if following else rest).strip()


def _beat(body: str) -> tuple[str, str | None]:
    """A section's opening paragraph and its first code block, if it has one.

    This is what makes the deck a deck rather than a list of headings: the
    sentence the page leads with is already the sentence to say out loud, and
    the first code block is already the thing to put on screen.
    """
    code = re.search(r"^```[a-z]*\n.*?^```", body, re.S | re.M)
    prose = body[: code.start()] if code else body
    paragraphs = [block.strip() for block in prose.split("\n\n") if block.strip()]
    lead = next((block for block in paragraphs if not block.startswith(("|", ">", "-"))), "")
    return lead, code.group(0) if code else None


def concept_pages(directory: Path) -> list[tuple[Path, str, list[tuple[str, str, str | None]]]]:
    """Each concept page: its path, its title, and the beats inside it.

    A beat is one `##` section: its heading, the paragraph it opens with, and
    its first code block. Enough to be a slide without inventing anything.
    """
    pages = []
    for path in sorted(directory.glob("concepts-*.mdx")):
        text = _read(path)
        title = HEADING.search(text)
        beats = []
        headings = list(SUBHEADING.finditer(text))
        for index, match in enumerate(headings):
            stop = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            lead, code = _beat(text[match.end() : stop])
            beats.append((match.group(1), lead, code))
        pages.append((path, title.group(1) if title else path.stem, beats))
    return pages


def notebook_sections(path: Path | None) -> list[str]:
    """The `##` headings a learner walks through in the exercise notebook."""
    if path is None or not path.is_file():
        return []
    notebook = json.loads(path.read_text(encoding="utf-8"))
    found = []
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        for line in cell.get("source", []):
            if line.startswith("## "):
                found.append(line[3:].strip())
    return found


def quiz(directory: Path) -> list[tuple[str, str, str]]:
    """Each question, and the choice marked correct — the reason this is private."""
    text = _read(directory / "quiz.mdx")
    out = []
    positions = [(m.start(), m.group(1), m.group(2)) for m in QUESTION.finditer(text)]
    for index, (start, label, question) in enumerate(positions):
        stop = positions[index + 1][0] if index + 1 < len(positions) else len(text)
        answer = CORRECT.search(text[start:stop])
        out.append((label, question, answer.group(1) if answer else "—"))
    return out


def exercises(chapter_id: str) -> list[tuple[str, str]]:
    """Each exercise id with the one-line description its checker carries."""
    import bootcamp_agent.session_checks  # noqa: F401 - importing registers them
    from bootcamp_agent.checks import CHECKS

    out = []
    for key in exercise_ids(chapter_id):
        doc = (CHECKS[key].__doc__ or "").strip().splitlines()
        out.append((key, doc[0] if doc else "—"))
    return out


# ------------------------------------------------------------------- rendering


def _ci_note(chapter) -> str:
    """Whether CI executes this notebook, and the reason when it does not."""
    if chapter.runs_in_ci:
        return "yes"
    return f"no — {chapter.manual_reason or 'no notebook'}"


def render_plan_facts(chapter) -> str:
    """The generated half of a teaching plan: what the session says about itself."""
    directory = chapter.directory
    introduction = _read(directory / "introduction.mdx")
    outcome = _section(introduction, "Outcome")
    contract = _section(introduction, "Contract and threat boundary")
    pages = concept_pages(directory)
    items = exercises(chapter.chapter_id)
    questions = quiz(directory)
    sections = notebook_sections(chapter.notebook)

    marks = len(items) * FULL_MARKS if chapter.runs_in_ci else None
    scoring = (
        f"{len(items)} exercises, {marks} marks"
        if marks
        else f"{len(items)} exercise(s), handed in and never marked"
    )

    lines = [
        START,
        "",
        "## At a glance",
        "",
        "| | |",
        "|---|---|",
        f"| Date | {chapter.on.strftime('%A %d %B %Y')} |",
        f"| Week | {chapter.module} — {WEEK_TITLES[chapter.module]} |",
        f"| Directory | `{directory.relative_to(ROOT)}` |",
        f"| Scoring | {scoring} |",
        f"| Runs in CI | {_ci_note(chapter)} |",
        "",
    ]

    if outcome:
        lines += ["## The goal, in the session's own words", "", outcome, ""]
    if contract:
        lines += ["## Contract and threat boundary", "", contract, ""]

    lines += ["## What is covered", ""]
    if pages:
        for path, title, beats in pages:
            lines.append(f"**{title}** — `{path.name}`")
            lines.append("")
            for heading, _lead, _code in beats:
                lines.append(f"- {heading}")
            lines.append("")
    else:
        lines += ["No concept pages; this session is the notebook and the rubric.", ""]

    if sections:
        lines += ["## The notebook, in order", ""]
        lines += [f"{index}. {name}" for index, name in enumerate(sections, start=1)]
        lines.append("")

    if items:
        lines += ["## Exercises", "", "| Id | What the checker judges |", "|---|---|"]
        lines += [f"| `{key}` | {what} |" for key, what in items]
        lines.append("")

    if questions:
        lines += [
            "## Quiz, with the answers",
            "",
            "**Never paste this section into a channel a student can read.**",
            "",
        ]
        for label, question, answer in questions:
            lines += [f"**{label}.** {question}", "", f"→ {answer}", ""]

    watchpoint = WATCHPOINTS.get(chapter.chapter_id)
    if watchpoint:
        trap, mitigation = watchpoint
        lines += ["## Watchpoint", "", f"**{trap}**", "", mitigation, ""]

    lines += ["## Files", ""]
    for path in sorted(directory.glob("*.mdx")):
        lines.append(f"- `{path.relative_to(ROOT)}`")
    if chapter.notebook is not None:
        lines.append(f"- `{chapter.notebook.relative_to(ROOT)}`")
        solutions = chapter.solutions.relative_to(ROOT)
        lines.append(f"- `{solutions}` — withheld until after the class")
    lines.append(f"- `{(PACK / chapter.dirname / 'slides.mdx').relative_to(ROOT)}` — the deck")
    lines += ["", END]
    return "\n".join(lines) + "\n"


#: The shape of a two-hour class, as the default a plan starts from. It is a
#: seed, not a rule: the numbers are the founder's to change per session, and no
#: run overwrites them once the file exists.
DEFAULT_RUN_OF_SHOW = """## Run of show

| Minutes | What |
|---|---|
| 0–10 | Warm-up: one question from last session, answered out loud. |
| 10–35 | Concepts, live. Show the failure before the fix, every time. |
| 35–45 | The demo below, run for real. Let it break where it breaks. |
| 45–105 | The lab. Checkpoints at 60, 80 and 100 minutes. |
| 105–120 | Share, debug one failure together, exit ticket. |

**The lab is the class.** When the concepts run long, cut the second example,
never the lab.

## The demo

_What you run on screen, and the moment it is meant to produce._

## Traps

_What goes wrong in this room, and what you say when it does._

## What to cut when behind

_Named in advance, so the decision is not made at minute 90._

## After the class

Release this session's solutions, then collect what came in:

```bash
uv run python scripts/publish_cohort.py --week N \\
  --release-solutions {chapter_id} --commit
uv run python scripts/collect_submissions.py --merge
```
"""


def render_slides(chapter) -> str:
    """A deck spine that follows the concept pages, in Marp-compatible MDX."""
    pages = concept_pages(chapter.directory)
    items = exercises(chapter.chapter_id)
    # The marker opens the file. Everything the generator owns — the front
    # matter included — has to sit inside it, or a merge writes the header a
    # second time on every run. Your own slides go after the closing marker.
    lines = [
        START,
        "---",
        "marp: true",
        "paginate: true",
        f'title: "Session {chapter.number} — {chapter.title}"',
        "---",
        "",
        f"# Session {chapter.number}",
        f"## {chapter.title}",
        "",
        f"{chapter.on.strftime('%A %d %B %Y')} · 2 hours",
        "",
    ]
    for _path, title, beats in pages:
        lines += ["---", "", f"# {title}", ""]
        for heading, lead, code in beats:
            lines += ["---", "", f"## {heading}", ""]
            if lead:
                lines += [lead, ""]
            if code:
                lines += [code, ""]
    if items:
        lines += ["---", "", "# The lab", ""]
        for key, what in items:
            lines.append(f"- **{key}** — {what}")
        lines.append("")
    lines += [
        "---",
        "",
        "# Exit ticket",
        "",
        "- What works now that did not this morning?",
        "- What is still unclear?",
        "- What is your next action?",
        "",
        END,
        "",
    ]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ assembling


def _merge(existing: str, generated: str) -> str:
    """Replace the generated block, keeping everything the author wrote."""
    start, end = existing.find(START), existing.find(END)
    if start == -1 or end == -1:
        return existing.rstrip("\n") + "\n\n" + generated
    return existing[:start] + generated + existing[end + len(END) :].lstrip("\n")


def plan_file(chapter) -> tuple[Path, str]:
    path = PACK / chapter.dirname / "plan.md"
    facts = render_plan_facts(chapter)
    if path.is_file():
        return path, _merge(path.read_text(encoding="utf-8"), facts)
    header = (
        f"# Session {chapter.number} — {chapter.title}\n\n"
        f"Teaching plan. Everything above the `generated` markers is read from the\n"
        f"session itself; everything below them is yours to write and no run of\n"
        f"`scripts/instructor_pack.py` will touch it.\n\n"
    )
    seed = DEFAULT_RUN_OF_SHOW.replace("{chapter_id}", chapter.chapter_id).replace(
        "--week N", f"--week {chapter.module}"
    )
    return path, header + facts + "\n" + seed


def slides_file(chapter) -> tuple[Path, str]:
    path = PACK / chapter.dirname / "slides.mdx"
    deck = render_slides(chapter)
    if path.is_file() and path.read_text(encoding="utf-8").startswith(START):
        return path, _merge(path.read_text(encoding="utf-8"), deck)
    # No marker at the top means nothing here is yours yet, or the file predates
    # the marker moving. Either way the spine is rewritten whole.
    return path, deck


def render_index() -> str:
    """The one page that says what exists and where, in teaching order."""
    lines = [
        "<!-- generated by scripts/instructor_pack.py — run it, do not edit this file -->",
        "",
        "# Instructor packs, by session",
        "",
        "One directory per session: `plan.md` is what you teach from, `slides.mdx`",
        "is the deck. Both carry a generated block read from the session's own",
        "pages, and your own writing outside it.",
        "",
        "**None of this is published.** `docs/instructor/` is on the publisher's",
        "deny list, and the plans carry the quiz answers.",
        "",
        "```bash",
        "uv run python scripts/instructor_pack.py           # refresh the generated blocks",
        "uv run python scripts/instructor_pack.py --check   # CI: fail when one is stale",
        "```",
        "",
        "| # | Date | Session | Exercises | Plan |",
        "|---|---|---|---|---|",
    ]
    for chapter in CHAPTERS:
        count = len(exercise_ids(chapter.chapter_id)) if chapter.has_notebook else 0
        scoring = f"{count}" if chapter.runs_in_ci else (f"{count}, unmarked" if count else "—")
        lines.append(
            f"| {chapter.number} | {chapter.weekday} | {chapter.title} | {scoring} "
            f"| [plan]({chapter.dirname}/plan.md) · [slides]({chapter.dirname}/slides.mdx) |"
        )
    lines += [
        "",
        f"The capstone is not a class. Its brief is `{CAPSTONE.directory.relative_to(ROOT)}`,",
        "and it is worked in the hours between sessions from week 2.",
        "",
        "Timing traps that apply to every session, and the two hard dependencies,",
        "are in [`../teaching-notes.md`](../teaching-notes.md).",
        "",
    ]
    return "\n".join(lines) + "\n"


def expected_files() -> dict[Path, str]:
    files = {PACK / "README.md": render_index()}
    for chapter in CHAPTERS:
        for path, text in (plan_file(chapter), slides_file(chapter)):
            files[path] = text
    return files


def generate(check: bool = False) -> int:
    files = expected_files()
    stale = [
        path
        for path, text in files.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != text
    ]
    if check:
        for path in stale:
            print(f"stale: {path.relative_to(ROOT)}")
        if stale:
            print("re-run: uv run python scripts/instructor_pack.py", file=sys.stderr)
            return 1
        print(f"instructor pack current: {len(files)} files")
        return 0
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"wrote {len(files)} files under {PACK.relative_to(ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when anything is stale")
    args = parser.parse_args(argv)
    return generate(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
