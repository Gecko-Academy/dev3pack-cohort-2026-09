"""Lexical retrieval: deterministic, cheap, inspectable.

This is deliberately not an embedding index. A keyword baseline is debuggable
by eye, has no dependencies, and sets the bar any fancier retriever must beat
in the session-7 evaluation before it earns its place.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

from bootcamp_agent.documents import Document

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Words too common to signal relevance in this corpus.
_STOPWORDS = frozenset(
    "a an and are as at be but by can could did do does for from has have how i if in "
    "into is it its me my no not of on one only or our over should so some than that "
    "the their then they this to under was we what when where which who why will with "
    "would you your".split()
)


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    text: str
    position: int


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


def chunk_document(doc: Document, max_chars: int = 800) -> list[Chunk]:
    """Pack whole paragraphs into chunks of at most `max_chars` characters."""
    paragraphs = [p.strip() for p in doc.text.split("\n\n") if p.strip()]
    chunks: list[Chunk] = []
    current: list[str] = []
    length = 0
    for paragraph in paragraphs:
        # A single oversized paragraph still becomes its own (truncated) chunk.
        if length and length + len(paragraph) + 2 > max_chars:
            chunks.append(Chunk(doc.doc_id, "\n\n".join(current), len(chunks)))
            current, length = [], 0
        current.append(paragraph[:max_chars])
        length += len(paragraph) + 2
    if current:
        chunks.append(Chunk(doc.doc_id, "\n\n".join(current), len(chunks)))
    return chunks


def retrieve(
    query: str, documents: Sequence[Document], top_k: int = 3, max_chars: int = 800
) -> list[ScoredChunk]:
    """Score chunks by query-token overlap, weighted by inverse document frequency."""
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return []
    all_chunks = [chunk for doc in documents for chunk in chunk_document(doc, max_chars)]
    if not all_chunks:
        return []
    # Document frequency per token over chunks.
    df: dict[str, int] = {}
    chunk_tokens: list[set[str]] = []
    for chunk in all_chunks:
        tokens = set(_tokens(chunk.text))
        chunk_tokens.append(tokens)
        for token in tokens & query_tokens:
            df[token] = df.get(token, 0) + 1
    total = len(all_chunks)
    scored = []
    for chunk, tokens in zip(all_chunks, chunk_tokens, strict=True):
        overlap = tokens & query_tokens
        if not overlap:
            continue
        score = sum(math.log(1 + total / df[token]) for token in overlap)
        scored.append(ScoredChunk(chunk=chunk, score=round(score, 6)))
    scored.sort(key=lambda s: (-s.score, s.chunk.doc_id, s.chunk.position))
    return scored[:top_k]
