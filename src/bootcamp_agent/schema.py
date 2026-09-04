"""The structured answer contract between the model and the application.

Parsing is strict on purpose: the model's output is untrusted input, and a
schema only protects you if violations fail loudly at the boundary.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*)\n```\s*$", re.DOTALL)

REQUIRED_FIELDS = {"answer", "citations", "confidence", "needs_human_review"}

ANSWER_JSON_INSTRUCTIONS = """\
Respond with ONLY a JSON object, no prose before or after, in exactly this shape:
{"answer": "<your answer>", "citations": ["<doc-id>", ...], "confidence": <0.0-1.0>,
 "needs_human_review": <true|false>}
Rules: cite only doc-ids that appear in the provided context; if the context does
not support an answer, say you do not know, use an empty citations list, set
confidence to 0.0, and set needs_human_review to true."""


class AnswerParseError(Exception):
    """Raised when the model's output does not satisfy the ResearchAnswer contract."""


@dataclass(frozen=True)
class ResearchAnswer:
    answer: str
    citations: tuple[str, ...]
    confidence: float
    needs_human_review: bool


def parse_research_answer(raw: str) -> ResearchAnswer:
    """Parse strict ResearchAnswer JSON; tolerate a single markdown code fence."""
    text = raw.strip()
    fence = _FENCE_RE.match(text)
    if fence is not None:
        text = fence.group(1).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise AnswerParseError(f"Not valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise AnswerParseError(f"Expected a JSON object, got {type(payload).__name__}")
    keys = set(payload)
    if keys != REQUIRED_FIELDS:
        missing = REQUIRED_FIELDS - keys
        unknown = keys - REQUIRED_FIELDS
        raise AnswerParseError(f"Wrong fields: missing={sorted(missing)} unknown={sorted(unknown)}")
    answer = payload["answer"]
    citations = payload["citations"]
    confidence = payload["confidence"]
    needs_review = payload["needs_human_review"]
    if not isinstance(answer, str) or not answer.strip():
        raise AnswerParseError("'answer' must be a non-empty string")
    if not isinstance(citations, list) or not all(isinstance(c, str) for c in citations):
        raise AnswerParseError("'citations' must be a list of strings")
    if not isinstance(confidence, int | float) or isinstance(confidence, bool):
        raise AnswerParseError("'confidence' must be a number")
    if not 0.0 <= float(confidence) <= 1.0:
        raise AnswerParseError(f"'confidence' out of range [0, 1]: {confidence}")
    if not isinstance(needs_review, bool):
        raise AnswerParseError("'needs_human_review' must be a boolean")
    return ResearchAnswer(
        answer=answer,
        citations=tuple(citations),
        confidence=float(confidence),
        needs_human_review=needs_review,
    )
