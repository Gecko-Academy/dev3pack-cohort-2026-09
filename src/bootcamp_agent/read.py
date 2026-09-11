"""What a course page is, and how it renders.

The pages are MDX carrying `<Question>` blocks -- the Hugging Face course
format. Nothing that merely reads the file renders that: GitHub's preview shows
the headings and then prints `<Question choices={[{ text: ...` as a paragraph,
on Hugging Face's own repository as much as on ours. The `explain` strings are
the teaching, and they are exactly what is lost.

So a page is parsed here, in the package, and the three surfaces that show one
are transport:

  * `bootcamp_agent.read.page("session-01/quiz")` -- inline in Jupyter, which is
    where a learner already is, beside the exercise the page is about.
  * `scripts/course_html.py` -- the whole course as a static site.
  * anything later, including a hosted site, because the parse is here.

WHY THE QUIZ IS `<details>` AND NOT JAVASCRIPT. `display(HTML(...))` inserts
through `innerHTML`, and a `<script>` inserted that way never executes -- in any
browser, not as a Jupyter policy. A quiz built on a click handler is therefore
dead inside a notebook. `<details>` needs no script at all, so one rendering
works in Jupyter, in the site with JavaScript off, and in GitHub's own markdown.
The site layers a little JavaScript on top for polish; nothing depends on it.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path

from bootcamp_agent.curriculum import UNITS_ROOT

TOCTREE = UNITS_ROOT / "_toctree.yml"

#: Anything that is not a letter or digit, for building heading anchors.
_NOT_SLUG = re.compile(r"[^a-z0-9]+")

_KEY = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*")
_LITERAL = re.compile(r"(true|false|null|-?\d+(?:\.\d+)?)")
_HEADING = re.compile(r"^(#{1,4})\s+(.*)$")


class ReadError(Exception):
    """A page cannot be read as it stands."""


# --------------------------------------------------------------------------
# The `<Question>` component
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Choice:
    """One answer, with the sentence that explains why it is or is not right."""

    text: str
    explain: str
    correct: bool = False


@dataclass(frozen=True)
class Question:
    """A `<Question>` block: the choices, in the order they were authored."""

    choices: tuple[Choice, ...]


def _scan_string(source: str, start: int) -> tuple[str, int]:
    """Read one quoted string beginning at `start`, honouring backslash escapes.

    A regex cannot do this. The authored explanations contain escaped quotes --
    `"\\"When the retriever starts to feel slow\\""` is a real choice in unit 2 --
    and a non-greedy match stops at the first one, silently truncating the
    sentence a learner is meant to read.
    """
    quote = source[start]
    if quote not in "\"'`":
        raise ReadError(f"expected a quoted string at offset {start}")
    out: list[str] = []
    index = start + 1
    while index < len(source):
        character = source[index]
        if character == "\\" and index + 1 < len(source):
            out.append(source[index + 1])
            index += 2
            continue
        if character == quote:
            return "".join(out), index + 1
        out.append(character)
        index += 1
    raise ReadError("a choice's string is never closed")


def _scan_object(source: str, start: int) -> tuple[dict[str, object], int]:
    """Read one `{ text: "...", explain: "...", correct: true }` literal."""
    if source[start] != "{":
        raise ReadError(f"expected a choice at offset {start}")
    fields: dict[str, object] = {}
    index = start + 1
    while index < len(source):
        character = source[index]
        if character.isspace() or character == ",":
            index += 1
            continue
        if character == "}":
            return fields, index + 1
        key_match = _KEY.match(source, index)
        if key_match is None:
            raise ReadError(f"could not read a choice's field at offset {index}")
        key = key_match.group(1)
        index = key_match.end()
        if source[index] in "\"'`":
            value, index = _scan_string(source, index)
            fields[key] = value
            continue
        literal = _LITERAL.match(source, index)
        if literal is None:
            raise ReadError(f"could not read the value of {key!r} at offset {index}")
        fields[key] = {"true": True, "false": False, "null": None}.get(
            literal.group(1), literal.group(1)
        )
        index = literal.end()
    raise ReadError("a choice is never closed")


def parse_question(block: str) -> Question:
    """Turn one `<Question ... />` block into its choices.

    The attribute is a JavaScript array literal, not JSON: the keys are
    unquoted, the last entry may carry a trailing comma, and `correct: true` is
    a bare keyword. `json.loads` refuses all three, so this walks it.
    """
    opening = block.find("choices=")
    if opening == -1:
        raise ReadError("a <Question> with no choices")
    bracket = block.find("[", opening)
    if bracket == -1:
        raise ReadError("a <Question> whose choices are not a list")
    choices: list[Choice] = []
    index = bracket + 1
    while index < len(block):
        character = block[index]
        if character.isspace() or character == ",":
            index += 1
            continue
        if character == "]":
            break
        if character != "{":
            raise ReadError(f"unexpected {character!r} among the choices")
        fields, index = _scan_object(block, index)
        text = fields.get("text")
        if not isinstance(text, str):
            raise ReadError("a choice with no text")
        explain = fields.get("explain")
        choices.append(
            Choice(
                text=text,
                explain=explain if isinstance(explain, str) else "",
                correct=bool(fields.get("correct", False)),
            )
        )
    if not choices:
        raise ReadError("a <Question> with no choices")
    return Question(choices=tuple(choices))


def _close_of(text: str, start: int) -> int:
    """The offset just past the `/>` that closes the tag opening at `start`.

    Scans through strings, because a choice's prose may contain `/>` -- and a
    naive search for it cuts the block in half wherever it does.
    """
    index = start
    while index < len(text):
        character = text[index]
        if character in "\"'`":
            _, index = _scan_string(text, index)
            continue
        if character == "/" and text.startswith("/>", index):
            return index + 2
        index += 1
    raise ReadError("a <Question> tag is never closed")


#: A paragraph the markdown pass leaves alone, swapped for the rendered question.
PLACEHOLDER = "QUESTIONPLACEHOLDER"


def extract_questions(text: str) -> tuple[str, list[Question]]:
    """Replace every `<Question>` with a placeholder, and return them in order."""
    questions: list[Question] = []
    out: list[str] = []
    index = 0
    while True:
        opening = text.find("<Question", index)
        if opening == -1:
            out.append(text[index:])
            return "".join(out), questions
        closing = _close_of(text, opening)
        out.append(text[index:opening])
        out.append(f"\n\n{PLACEHOLDER}{len(questions)}\n\n")
        questions.append(parse_question(text[opening:closing]))
        index = closing


def inline(text: str) -> str:
    """Render one short string: backticks become code, everything else escapes."""
    parts = text.split("`")
    out = []
    for position, part in enumerate(parts):
        escaped = html.escape(part, quote=True)
        out.append(f"<code>{escaped}</code>" if position % 2 else escaped)
    return "".join(out)


def render_question(question: Question) -> str:
    """One question as HTML that needs no JavaScript to work.

    Each choice opens to its own explanation, and the tick appears only inside
    an opened one -- never in the summary, which would answer the question
    before it was asked, and never behind `opacity:0`, which still reads the
    answer out to a screen reader.
    """
    rows = []
    for choice in question.choices:
        tick = '<span class="tick">✓ </span>' if choice.correct else ""
        rows.append(
            '<li class="choice"><details><summary>'
            f"{inline(choice.text)}</summary>"
            f'<p class="explain">{tick}{inline(choice.explain)}</p>'
            "</details></li>"
        )
    return f'<div class="question"><ul class="choices">{"".join(rows)}</ul></div>'


# --------------------------------------------------------------------------
# A page
# --------------------------------------------------------------------------


def anchor_of(heading: str) -> str:
    """HF writes `# Title [[anchor]]`; otherwise slug the text."""
    explicit = re.search(r"\[\[([^\]]+)\]\]", heading)
    if explicit:
        return explicit.group(1).strip()
    plain = re.sub(r"`|\*|\[\[.*?\]\]", "", heading).strip().lower()
    return _NOT_SLUG.sub("-", plain).strip("-") or "section"


@dataclass
class Page:
    """A rendered page: its title, its HTML, and the headings it contains."""

    title: str
    body: str
    headings: list[tuple[int, str, str]] = field(default_factory=list)


def _markdown() -> object:
    try:
        from markdown_it import MarkdownIt
    except ImportError:
        raise ReadError("reading the pages needs markdown-it-py:  uv sync --extra site") from None
    return MarkdownIt("commonmark", {"html": True, "linkify": False}).enable("table")


def render(source: Path) -> Page:
    """One `.mdx` file as HTML, with its questions and its heading list."""
    if not source.is_file():
        raise ReadError(f"no such page: {source}")
    text, questions = extract_questions(source.read_text(encoding="utf-8"))

    headings: list[tuple[int, str, str]] = []
    lines = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        heading = _HEADING.match(line)
        if heading and not in_fence:
            raw = heading.group(2)
            anchor = anchor_of(raw)
            shown = re.sub(r"\s*\[\[[^\]]+\]\]\s*", "", raw).strip()
            headings.append((len(heading.group(1)), shown, anchor))
            lines.append(f'{heading.group(1)} <a id="{anchor}"></a>{shown}')
            continue
        lines.append(line)

    body = _markdown().render("\n".join(lines))  # type: ignore[attr-defined]
    for number, question in enumerate(questions):
        marker = f"{PLACEHOLDER}{number}"
        rendered = render_question(question)
        body = body.replace(f"<p>{marker}</p>", rendered).replace(marker, rendered)

    title = next((shown for level, shown, _ in headings if level == 1), source.stem)
    return Page(title=title, body=body, headings=headings)


# --------------------------------------------------------------------------
# The table of contents
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Entry:
    """One page in the course order."""

    local: str
    title: str
    group: str

    @property
    def source(self) -> Path:
        return UNITS_ROOT / f"{self.local}.mdx"


def toctree() -> list[tuple[str, list[Entry]]]:
    """The course order, exactly as `_toctree.yml` gives it.

    THE TOCTREE IS THE ONLY ORDERING SOURCE. It is generated from the curriculum
    by `scripts/course_site.py`, so recomputing the order here would be a second
    opinion about the same question, free to drift from the one we ship.
    """
    try:
        import yaml
    except ImportError:
        raise ReadError("reading the pages needs pyyaml:  uv sync --extra site") from None
    if not TOCTREE.is_file():
        raise ReadError(f"{TOCTREE} is missing; run scripts/course_site.py first")
    payload = yaml.safe_load(TOCTREE.read_text(encoding="utf-8"))
    groups: list[tuple[str, list[Entry]]] = []
    for group in payload:
        title = str(group.get("title", ""))
        groups.append(
            (
                title,
                [
                    Entry(local=str(s["local"]), title=str(s.get("title", "")), group=title)
                    for s in group.get("sections", [])
                    if "local" in s
                ],
            )
        )
    return groups


def entries() -> list[Entry]:
    """Every page, flat, in course order."""
    return [entry for _, group in toctree() for entry in group]


def _matches(local: str, wanted: list[str]) -> bool:
    """Does `local` end with the segments a learner named?

    Aligned from the RIGHT and matched per segment, so `session-01/quiz` finds
    `unit1/session-01-assistant-configuration/quiz`. A plain substring test does
    not: the typed name is not a substring of the real path, because the real
    directory carries the session's title after its number.
    """
    parts = local.split("/")
    if len(wanted) > len(parts):
        return False
    # strict=False on purpose: a learner names the tail of a path, so `wanted`
    # is shorter than `parts` in every case this is asked about.
    for typed, actual in zip(reversed(wanted), reversed(parts), strict=False):
        if actual != typed and not actual.startswith(typed):
            return False
    return True


def find(slug: str) -> Entry:
    """The page a learner named, forgivingly.

    `find("session-01/quiz")` is what somebody types; the toctree calls it
    `unit1/session-01-assistant-configuration/quiz`. An exact local wins, then a
    right-aligned segment match -- and an ambiguous name says which pages it
    could have meant rather than silently showing one of them.
    """
    wanted = slug.strip().strip("/").removesuffix(".mdx")
    every = entries()
    for entry in every:
        if entry.local == wanted:
            return entry
    segments = wanted.split("/")
    hits = [entry for entry in every if _matches(entry.local, segments)]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        names = ", ".join(hit.local for hit in hits[:5])
        more = " ..." if len(hits) > 5 else ""
        raise ReadError(f"{slug!r} matches {len(hits)} pages: {names}{more}")
    raise ReadError(f"no page called {slug!r}. Try read.contents() for the list.")


# --------------------------------------------------------------------------
# Jupyter
# --------------------------------------------------------------------------

#: Inlined, because a notebook output has no stylesheet to link to.
NOTEBOOK_STYLE = """<style>
.dev3pack{line-height:1.6;max-width:52em}
.dev3pack .question{margin:1em 0 1.4em}
.dev3pack .choices{list-style:none;margin:0;padding:0}
.dev3pack .choice{margin:6px 0}
.dev3pack summary{cursor:pointer;padding:9px 12px;border:1px solid #d8d8de;
border-radius:8px;list-style:none}
.dev3pack summary::-webkit-details-marker{display:none}
.dev3pack summary:hover{border-color:#2f6f4f}
.dev3pack .explain{margin:6px 0 0;padding:8px 12px;font-size:.94em;opacity:.85;
border-left:2px solid #d8d8de}
.dev3pack .tick{color:#1d7a4c;font-weight:700}
.dev3pack code{background:rgba(127,127,127,.14);padding:.12em .35em;border-radius:4px}
.dev3pack pre{background:rgba(127,127,127,.1);padding:12px;border-radius:8px;overflow-x:auto}
.dev3pack pre code{background:none;padding:0}
.dev3pack table{border-collapse:collapse}
.dev3pack th,.dev3pack td{border:1px solid #d8d8de;padding:6px 9px;text-align:left}
</style>"""


def page(slug: str) -> object:
    """Show a course page inside the notebook.

        from bootcamp_agent import read
        read.page("session-01/quiz")

    Returns the display object rather than printing, so Jupyter renders it as
    the cell's value and a plain Python session can still inspect it.
    """
    entry = find(slug)
    rendered = render(entry.source)
    try:
        from IPython.display import HTML
    except ImportError:
        raise ReadError("read.page() needs IPython; outside a notebook use render()") from None
    return HTML(f'{NOTEBOOK_STYLE}<div class="dev3pack">{rendered.body}</div>')


def contents() -> object:
    """Show every page there is, grouped, as links a notebook can list."""
    blocks = []
    for title, group in toctree():
        available = [entry for entry in group if entry.source.is_file()]
        if not available:
            continue
        items = "".join(
            f"<li><code>{html.escape(entry.local)}</code> — {html.escape(entry.title)}</li>"
            for entry in available
        )
        blocks.append(f"<p><strong>{html.escape(title)}</strong></p><ul>{items}</ul>")
    body = "".join(blocks) or "<p>No pages are published yet.</p>"
    try:
        from IPython.display import HTML
    except ImportError:
        raise ReadError("read.contents() needs IPython") from None
    return HTML(f'{NOTEBOOK_STYLE}<div class="dev3pack">{body}</div>')
