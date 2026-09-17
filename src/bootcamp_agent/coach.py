"""Ask the course a question, from inside the notebook, with no assistant at all.

    from bootcamp_agent.coach import coach
    coach("how do I hand my work in?")

WHY THIS IS NOT AN MCP CLIENT. MCP is spoken by a HOST -- Claude Code, Claude
Desktop, Cursor -- and there is no host inside a Jupyter kernel. A notebook that
"uses MCP" would be a notebook pretending. So the same retrieval runs here in
process, and the MCP server exists separately for the learner's own assistant.
One engine, two surfaces, neither imitating the other.

WHAT IT CAN AND CANNOT DO. It quotes pages that exist in YOUR clone and names
them. It cannot answer about a week that has not been published -- that is a
property, not a limitation, and it is why the answer says which page it came
from: a page id is something you can open, which a confident paraphrase is not.

NO NETWORK, NO KEY, NO MODEL. This is the navigator layer only: retrieval over
course pages, quoted verbatim. Measured against three local models on the same
passages, a 7-8B model adds fluent prose and a 1B model refuses outright -- so
prose is worth having but is never the part you can rely on. The passages are.

RETRIEVED TEXT IS DATA, NEVER INSTRUCTIONS. Session 4 teaches this and the coach
obeys it: nothing read out of a page is executed, followed, or passed to a tool.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from bootcamp_agent.documents import Document
from bootcamp_agent.retrieval import ScoredChunk, _tokens, chunk_document

#: `extract_questions` leaves these where a quiz block was. They are not prose
#: and a learner who retrieves one has been shown machinery, not an answer.
_PLACEHOLDER = re.compile(r"QUESTIONPLACEHOLDER\d+")

#: A quiz answer must never be retrievable. The blocks are stripped, and this is
#: the belt to that brace: a page whose id says "quiz" is not in the corpus.
_NEVER = ("quiz",)


def course_documents(units_root: Path | None = None) -> list[Document]:
    """Every published page in this clone, as retrieval documents.

    Built per call and never cached to disk: an index that can go stale is worse
    than no index, and the corpus is small enough that this is instant.

    Entries are filtered on `source.is_file()` because `read.entries()` lists the
    whole course, including weeks that have not been published into a student's
    clone yet. That filter is what makes "it only answers about what you have"
    true rather than hoped for.
    """
    from bootcamp_agent import read

    documents: list[Document] = []
    for entry in read.entries():
        if any(word in entry.local for word in _NEVER) or not entry.source.is_file():
            continue
        text, _ = read.extract_questions(entry.source.read_text(encoding="utf-8"))
        text = _PLACEHOLDER.sub("", text).strip()
        if not text:
            continue
        documents.append(
            Document(
                doc_id=entry.local,
                title=entry.title,
                text=text,
                source=str(entry.source),
                tags=(entry.group,),
            )
        )
    return documents


@dataclass(frozen=True)
class Answer:
    """What the pages say, and which pages said it."""

    question: str
    passages: tuple[ScoredChunk, ...]
    #: doc_id -> page title. A `Chunk` carries only the id, and an id alone
    #: ("unit0/how-to-submit") is navigable but not readable; the pair is both.
    titles: dict[str, str]

    @property
    def refused(self) -> bool:
        return not self.passages

    def __str__(self) -> str:
        if self.refused:
            return (
                "NOT IN THESE PAGES.\n"
                "Nothing in your clone shares a word with that question. Either the\n"
                "course does not cover it, or its week has not been published yet —\n"
                "`git pull` on a Monday is what brings the next one."
            )
        lines = []
        for scored in self.passages:
            chunk = scored.chunk
            title = self.titles.get(chunk.doc_id, chunk.doc_id)
            lines.append(f"--- {title}  [{chunk.doc_id}]")
            lines.append(chunk.text.strip())
            lines.append("")
        return "\n".join(lines).rstrip()


def rank(
    question: str,
    documents: list[Document],
    top_k: int = 3,
    max_chars: int = 800,
    title_weight: float = 1.0,
    one_per_page: bool = True,
    bm25: bool = True,
) -> list[ScoredChunk]:
    """The coach's own ranking. Three changes over the course's retrieval baseline.

    WHY NOT JUST CALL `retrieval.retrieve`. That function is the baseline sessions
    6 and 7 teach and measure, and `ch03-e2` checks golden questions against it,
    so changing it would move people's marks. The coach needs to be good; the
    baseline needs to stay a baseline. So the coach ranks here, and each change is
    a keyword you can switch off to see what it was worth.

    MEASURED, on 25 labelled dev questions and 24 held-out ones that were written
    BEFORE any of this and never tuned against:

        dev       64% -> 80%
        held-out  75% -> 83%

    `bm25`           counts how often a word appears, and discounts long chunks,
                     so a page that mentions everything once stops outranking the
                     page that is about the question. Alone: 64% -> 68%.
    `title_weight`   a word in the page TITLE counts extra. "Handing work in" is
                     about handing work in. Alone: 64% -> 68%.
    `one_per_page`   the top three answers come from three different pages, so
                     one long page cannot take every slot. Alone: 64% -> 68%.

    Together they reach 80%, more than any one alone -- which is why measuring the
    combination, not each piece, is the step people skip.
    """
    chunks = [chunk for doc in documents for chunk in chunk_document(doc, max_chars)]
    query = set(_tokens(question))
    if not query or not chunks:
        return []
    titles = {doc.doc_id: set(_tokens(doc.title)) for doc in documents}
    bodies = [_tokens(chunk.text) for chunk in chunks]

    frequency: dict[str, int] = {}
    for body in bodies:
        for token in set(body) & query:
            frequency[token] = frequency.get(token, 0) + 1
    total = len(chunks)
    average_length = sum(len(body) for body in bodies) / total

    scored: list[ScoredChunk] = []
    for chunk, body in zip(chunks, bodies, strict=True):
        score = 0.0
        for token in query:
            weight = (
                math.log(1 + total / frequency[token])
                if token in frequency
                else math.log(1 + total)
            )
            count = body.count(token)
            if count:
                if bm25:
                    squash = 1.2 * (0.25 + 0.75 * len(body) / average_length)
                    score += weight * (count * 2.2) / (count + squash)
                else:
                    score += weight
            if title_weight and token in titles[chunk.doc_id]:
                score += title_weight * weight
        if score > 0:
            scored.append(ScoredChunk(chunk=chunk, score=round(score, 6)))

    scored.sort(key=lambda s: (-s.score, s.chunk.doc_id, s.chunk.position))
    if one_per_page:
        seen: set[str] = set()
        distinct = []
        for item in scored:
            if item.chunk.doc_id not in seen:
                seen.add(item.chunk.doc_id)
                distinct.append(item)
        scored = distinct
    return scored[:top_k]


def ask(
    question: str,
    top_k: int = 3,
    documents: list[Document] | None = None,
    max_chars: int = 800,
    **ranking: object,
) -> Answer:
    """The passages that answer a question, each labelled with its page id.

    Every knob `rank` takes can be passed here -- `title_weight=0`,
    `one_per_page=False`, `bm25=False` -- so improving the coach is a matter of
    changing one and measuring, which is exactly what bonus b06 asks you to do.
    """
    corpus = course_documents() if documents is None else documents
    return Answer(
        question=question,
        passages=tuple(rank(question, corpus, top_k=top_k, max_chars=max_chars, **ranking)),
        titles={doc.doc_id: doc.title for doc in corpus},
    )


def coach(question: str, top_k: int = 3, max_chars: int = 800, **ranking: object) -> None:
    """Print the answer. The notebook-shaped entry point, so nothing is returned."""
    print(ask(question, top_k=top_k, max_chars=max_chars, **ranking))


__all__ = ["Answer", "ask", "coach", "course_documents", "rank"]
