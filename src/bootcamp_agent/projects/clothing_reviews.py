"""Checks for project 01, clothing reviews. Uncounted: they live in `BONUS`.

Importing this module registers them; the project notebook does that in its
setup cell. The ids start with `project-`, so no typo can land in a session.

WHAT THESE CHECK, AND WHAT THEY DELIBERATELY DO NOT. Embeddings depend on the
model: `nomic-embed-text` makes 768 numbers per review, another model makes 384.
So no check pins a dimension, a coordinate, or which review is nearest. They check
what is true whichever model you chose -- one vector per non-empty review, one
2-D point per vector, topics that point at real reviews, and three neighbours that
are real, distinct, and not the review you asked about.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Sequence
from functools import cache
from pathlib import Path
from typing import Any

from ..bonus import register

DATA = (
    Path(__file__).resolve().parents[3]
    / "projects"
    / "01-clothing-reviews"
    / "data"
    / "reviews.csv"
)

#: The review the brief asks about, verbatim.
QUERY = "Absolutely wonderful - silky and sexy and comfortable"


@cache
def review_texts() -> tuple[str, ...]:
    """Every non-empty review, in file order -- the list the brief means by 'the reviews'.

    Forty-two rows have no text at all. Embedding an empty string still returns a
    vector, so skipping them is a decision the project asks you to make, not a
    detail the model makes for you.
    """
    with DATA.open(encoding="utf-8", newline="") as handle:
        return tuple(
            row["Review Text"]
            for row in csv.DictReader(handle)
            if (row.get("Review Text") or "").strip()
        )


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _as_rows(value: Any) -> list[Sequence[Any]] | None:
    """A list of rows from a list, a tuple, or a NumPy array, without importing NumPy."""
    if hasattr(value, "tolist"):
        value = value.tolist()
    if not isinstance(value, (list, tuple)):
        return None
    return list(value)


@register("project-01-e1")
def _embeddings(embeddings: Any) -> str | None:
    """One vector per non-empty review, all the same length, all numbers."""
    rows = _as_rows(embeddings)
    if rows is None:
        return "store the embeddings as a list, one vector per review"
    expected = len(review_texts())
    if len(rows) == expected + 42:
        return (
            f"you have {len(rows)} vectors, which includes the 42 reviews with no text. "
            "An empty review still gets a vector, and that vector means nothing -- drop them first"
        )
    if len(rows) != expected:
        return f"expected {expected} vectors (one per review with text), got {len(rows)}"
    lengths = {len(row) if isinstance(row, (list, tuple)) else -1 for row in rows}
    if -1 in lengths:
        return "every embedding must be a list of numbers"
    if len(lengths) != 1:
        return f"the vectors have different lengths {sorted(lengths)}; one model makes one length"
    (dimension,) = lengths
    if dimension < 16:
        return f"a {dimension}-number vector is not a text embedding; did you store a slice?"
    if not all(_is_number(x) for x in rows[0]):
        return "the vectors must hold numbers"
    if len({tuple(row[:8]) for row in rows[:50]}) < 45:
        return "most of your vectors are identical -- the same text was embedded over and over"
    return None


@register("project-01-e2")
def _embeddings_2d(embeddings_2d: Any) -> str | None:
    """One 2-D point per review, which is what a scatter plot needs."""
    rows = _as_rows(embeddings_2d)
    if rows is None:
        return "store the reduced embeddings as an array, e.g. the result of fit_transform"
    if len(rows) != len(review_texts()):
        return f"expected {len(review_texts())} points, one per review, got {len(rows)}"
    if any(not isinstance(row, (list, tuple)) or len(row) != 2 for row in rows):
        return "every point needs exactly two coordinates -- n_components=2"
    if not all(_is_number(x) for row in rows for x in row):
        return "the coordinates must be numbers"
    if len({(round(x, 3), round(y, 3)) for x, y in rows}) < len(rows) // 2:
        return "most points sit on top of each other; the reduction did not spread them out"
    return None


@register("project-01-e3")
def _topics(topic_reviews: Any) -> str | None:
    """A few topics, each pointing at real reviews -- and not the same ones for every topic."""
    if not isinstance(topic_reviews, dict) or not topic_reviews:
        return "store a dict mapping each topic to the reviews closest to it"
    if len(topic_reviews) < 3:
        return (
            "use at least three topics, like quality, fit and comfort; "
            f"you have {len(topic_reviews)}"
        )
    known = set(review_texts())
    for topic, found in topic_reviews.items():
        if not isinstance(found, (list, tuple)) or not found:
            return f"{topic!r} has no reviews"
        strangers = [text for text in found if text not in known]
        if strangers:
            return f"{topic!r} contains text that is not a review: {str(strangers[0])[:60]!r}"
    sets = [frozenset(found) for found in topic_reviews.values()]
    if len(set(sets)) == 1:
        return "every topic returned the same reviews, so the topic made no difference"
    return None


@register("project-01-e4")
def _most_similar(most_similar_reviews: Any) -> str | None:
    """Three real, distinct reviews -- and not the one you searched with."""
    if not isinstance(most_similar_reviews, list):
        return "store the result as a list of review texts"
    if len(most_similar_reviews) != 3:
        return f"the brief asks for 3 reviews, got {len(most_similar_reviews)}"
    if QUERY in most_similar_reviews:
        return (
            "the review you searched with is in its own results. It is always its own "
            "nearest neighbour -- ask for one more and leave it out"
        )
    if len(set(most_similar_reviews)) != 3:
        return "the three reviews must be different"
    known = set(review_texts())
    for text in most_similar_reviews:
        if text not in known:
            return f"not a review from the data: {str(text)[:60]!r}"
    return None
