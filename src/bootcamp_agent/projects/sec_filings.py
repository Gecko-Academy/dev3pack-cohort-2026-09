"""Checks for project 02, SEC filings. Uncounted: they live in `BONUS`.

Importing this module registers them; the project notebook does that in its
setup cell. The ids start with `project-`, so no typo can land in a session.

WHAT THESE CHECK, AND WHAT THEY DELIBERATELY DO NOT. Nothing here pins a vector,
a score, or which chunk is nearest: those move with the model and the chunker
you choose. The checks hold whatever you chose. Cleaning leaves no markup and no
page furniture and keeps the words. Chunking loses no word and respects its
limit. The store holds every chunk with its company. The measurement covers
both methods on every labelled question.

No import here reaches ChromaDB or NumPy. The store is read through two methods
any collection has, `count()` and `get()`, so the check runs on a plain install.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Callable, Sequence
from functools import cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from ..bonus import register

PROJECT = Path(__file__).resolve().parents[3] / "projects" / "02-sec-filings"
DATA = PROJECT / "data"

#: Lines that are page furniture, not risk factors. The notebook writes its own
#: list; this is the grader's, so a pattern the notebook forgets still counts.
NOISE = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^table of contents$",
        r"^\d{1,3}$",
        r"^part [ivx]+$",
        r"^item 1a$",
        r".+\|\s*\d{4} form 10-k\s*\|\s*\d+$",
        r"^\d{1,3}\s*\|\s*.+$",
        r"^\d{4} form 10-k \d{1,3}$",
    )
)
_TAG = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’.,%$-]*")


@cache
def sources() -> tuple[dict[str, Any], ...]:
    return tuple(json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["filings"])


@cache
def questions() -> tuple[dict[str, str], ...]:
    return tuple(json.loads((DATA / "questions.json").read_text(encoding="utf-8"))["questions"])


def raw_filing(ticker: str) -> str:
    entry = next(s for s in sources() if s["ticker"].lower() == ticker.lower())
    return (DATA / entry["file"]).read_text(encoding="utf-8")


#: Tags that end a line on the page. EDGAR files put whole pages on one source
#: line, so lines come from these, never from the newlines in the file.
BLOCK = frozenset({"p", "div", "tr", "li", "br", "table", "h1", "h2", "h3", "h4", "h5", "h6"})


class _Visible(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def reference_words(raw: str) -> Counter[str]:
    """Every word a reader sees, minus the page furniture: what cleaning must keep."""
    parser = _Visible()
    parser.feed(raw)
    words: Counter[str] = Counter()
    for line in "".join(parser.parts).splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line and not any(pattern.match(line) for pattern in NOISE):
            words.update(_WORD.findall(line))
    return words


def words(text: str) -> int:
    return len(_WORD.findall(text))


@register("project-02-e1")
def _clean(clean: Callable[[str], str]) -> str | None:
    """Every filing cleaned: no markup, no page furniture, and the words kept."""
    if not callable(clean):
        return "pass the clean function itself: bonus('project-02-e1', clean)"
    for entry in sources():
        ticker = entry["ticker"]
        raw = raw_filing(ticker)
        text = clean(raw)
        if not isinstance(text, str) or not text.strip():
            return f"{ticker}: clean() returned nothing"
        tag = _TAG.search(text)
        if tag:
            return f"{ticker}: an HTML tag survived: {tag.group(0)[:40]!r}"
        for line in text.splitlines():
            line = line.strip()
            if line and any(pattern.match(line) for pattern in NOISE):
                return f"{ticker}: page furniture survived as a line: {line!r}"
        if not re.match(r"item\s*1a", text.lstrip(), re.IGNORECASE):
            return f"{ticker}: the cleaned text should open with the 'Item 1A' heading"
        wanted = reference_words(raw)
        kept = Counter(_WORD.findall(text))
        missing = sum((wanted - kept).values())
        if missing > 0.01 * sum(wanted.values()):
            return f"{ticker}: {missing} words of the filing went missing in cleaning"
    return None


def _field(item: Any, name: str) -> Any:
    return item.get(name) if isinstance(item, dict) else getattr(item, name, None)


@register("project-02-e2")
def _chunks(report: dict[str, Any]) -> str | None:
    """Chunks that respect their limit and lose no word of the documents."""
    if not isinstance(report, dict) or not {"documents", "chunks", "max_chars"} <= set(report):
        return "expected {'documents': documents, 'chunks': chunks, 'max_chars': 800}"
    documents: Sequence[Any] = report["documents"]
    chunks: Sequence[Any] = report["chunks"]
    limit = report["max_chars"]
    if len(documents) != len(sources()):
        return f"expected one document per filing ({len(sources())}), got {len(documents)}"
    if not chunks:
        return "no chunks"
    for chunk in chunks:
        text = _field(chunk, "text") or ""
        if not text.strip():
            return "an empty chunk: it would still be embedded, and match nothing"
        if len(text) > limit:
            return f"a chunk of {len(text)} characters is over the {limit} limit"
    by_doc: dict[str, int] = Counter(_field(c, "doc_id") for c in chunks)
    for document in documents:
        doc_id = _field(document, "doc_id")
        if not by_doc.get(doc_id):
            return f"{doc_id} produced no chunks"
        in_doc = sum(words(_field(c, "text")) for c in chunks if _field(c, "doc_id") == doc_id)
        if in_doc != words(_field(document, "text")):
            whole = words(_field(document, "text"))
            return f"{doc_id}: the chunks hold {in_doc} of {whole} words. Lost: {whole - in_doc}"
    return None


@register("project-02-e3")
def _store(stored: tuple[Any, Sequence[Any]]) -> str | None:
    """Every chunk stored once, each with its company."""
    try:
        collection, chunks = stored
    except (TypeError, ValueError):
        return "expected (collection, chunks)"
    if not callable(getattr(collection, "count", None)) or not callable(
        getattr(collection, "get", None)
    ):
        return "the first item must be the collection you stored the chunks in"
    if collection.count() != len(chunks):
        return f"{collection.count()} records stored for {len(chunks)} chunks"
    records = collection.get(include=["metadatas"])
    ids = records.get("ids") or []
    if len(set(ids)) != len(ids):
        return "two records share an id"
    for metadata in records.get("metadatas") or []:
        if not metadata or not metadata.get("ticker") or not metadata.get("company"):
            return "every record needs 'ticker' and 'company' metadata, to cite it and filter by it"
    return None


@register("project-02-e4")
def _measure(rows: Sequence[dict[str, Any]]) -> str | None:
    """Both methods, measured on every labelled question, split by kind."""
    kinds = Counter(q["kind"] for q in questions())
    if not isinstance(rows, (list, tuple)) or not rows:
        return "expected a list of rows: {'method', 'kind', 'hits', 'total'}"
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not {"method", "kind", "hits", "total"} <= set(row):
            return "every row needs 'method', 'kind', 'hits' and 'total'"
        if row["kind"] not in kinds:
            return f"unknown kind {row['kind']!r}; the questions have {sorted(kinds)}"
        label = f"{row['method']}/{row['kind']}"
        if row["total"] != kinds[row["kind"]]:
            return (
                f"{label}: total {row['total']}, but there are {kinds[row['kind']]} such questions"
            )
        if not isinstance(row["hits"], int) or not 0 <= row["hits"] <= row["total"]:
            return f"{label}: hits must be a whole number from 0 to {row['total']}"
        seen.add((row["method"], row["kind"]))
    wanted = {(method, kind) for method in ("keyword", "embeddings") for kind in kinds}
    if seen != wanted:
        return f"missing rows: {sorted(wanted - seen)}"
    return None
