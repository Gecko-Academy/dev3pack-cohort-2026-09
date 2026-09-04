"""The document model and the loader for the teaching corpus.

Corpus format: markdown files whose first lines are HTML-comment headers,
so the files stay readable and renderable everywhere:

    <!-- title: Structured Outputs -->
    <!-- tags: llm, json, validation -->

    Body starts here...

The loader is deliberately strict: teaching corpora are versioned inputs,
and a malformed header should fail loudly, not load half a corpus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_HEADER_RE = re.compile(r"^<!--\s*(title|tags)\s*:\s*(.+?)\s*-->\s*$")


class CorpusError(Exception):
    """Raised when the corpus directory or a document header is unusable."""


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    text: str
    source: str
    tags: tuple[str, ...]


def _parse_document(path: Path, base: Path) -> Document:
    lines = path.read_text(encoding="utf-8").splitlines()
    title: str | None = None
    tags: tuple[str, ...] = ()
    body_start = 0
    for index, line in enumerate(lines):
        match = _HEADER_RE.match(line)
        if match is None:
            body_start = index
            break
        key, value = match.group(1), match.group(2)
        if key == "title":
            title = value
        else:
            tags = tuple(tag.strip() for tag in value.split(",") if tag.strip())
        body_start = index + 1
    if title is None:
        raise CorpusError(f"{path.name}: missing '<!-- title: ... -->' header")
    text = "\n".join(lines[body_start:]).strip()
    if not text:
        raise CorpusError(f"{path.name}: document body is empty")
    return Document(
        doc_id=path.stem,
        title=title,
        text=text,
        source=str(path.relative_to(base)),
        tags=tags,
    )


def load_corpus(directory: Path) -> list[Document]:
    """Load every .md file in `directory`, sorted by doc_id for determinism."""
    if not directory.is_dir():
        raise CorpusError(f"Corpus directory not found: {directory}")
    paths = sorted(directory.glob("*.md"))
    if not paths:
        raise CorpusError(f"No .md documents in {directory}")
    return [_parse_document(path, directory) for path in paths]
