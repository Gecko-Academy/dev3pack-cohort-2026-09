"""Build a regular expression out of plain words, and test it before you trust it.

    from bootcamp_agent.patterns import phrase, one_of, line_starts_with, near, check_pattern

    shape = near(one_of("send", "email"), one_of("api key", "password"), within=40)
    check_pattern(shape, should_match=["send the API key"], should_not_match=["rotate the API key"])

WHY THIS EXISTS. Nobody should have to remember that `\\s+` is "one or more
spaces" or that `(?:...)` is "a group that is not captured" to write a guard.
Those are the parts people copy from a generator without reading, and a pattern
you did not read is a pattern you cannot debug. So the vocabulary here is the
words you would use to describe the shape out loud, and every builder returns an
ordinary regex string you can print, read, and paste anywhere.

WHY `check_pattern` MATTERS MORE THAN THE BUILDERS. A pattern is a claim about
text, and the only evidence for a claim is examples it must match AND examples it
must leave alone. Writing only the first kind is how a guard ends up flagging
"The setup instructions are in SETUP.md" -- and a guard that cries wolf is a
guard somebody switches off.

IT IS ALSO A BOUNDED TOOL, which is session 4's whole subject. `build_pattern`
takes a structured request, refuses anything outside its contract before it does
any work, and never runs a pattern it was handed as raw regex. Every piece of
text is escaped, so a phrase like "a.b" means a dot and not "any character".
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

#: The furthest `near()` will reach. A window this wide already spans a sentence;
#: a wider one starts matching two unrelated sentences and calling it one thought.
MAX_WITHIN = 200

#: Flags every guard in this course uses. Case-insensitive because an attacker
#: writes IGNORE as happily as ignore; multiline so `^` means "start of a line".
FLAGS = re.IGNORECASE | re.MULTILINE


class PatternError(ValueError):
    """A request outside the builder's contract, refused before anything is built."""


def _words(text: str) -> str:
    """One phrase, escaped, with any run of whitespace between its words."""
    parts = text.split()
    if not parts:
        raise PatternError("a phrase needs at least one word")
    return r"\s+".join(re.escape(part) for part in parts)


def phrase(text: str) -> str:
    """These words, in this order, however many spaces sit between them.

    >>> phrase("you must now")
    'you\\\\s+must\\\\s+now'
    """
    return _words(text)


def one_of(*phrases: str) -> str:
    """Any one of these phrases.

    >>> one_of("api key", "token")
    '(?:api\\\\s+key|token)'
    """
    if not phrases:
        raise PatternError("one_of needs at least one phrase")
    return "(?:" + "|".join(_words(p) for p in phrases) + ")"


def gap(max_words: int) -> str:
    """Up to this many whole words in between -- 'ignore ALL YOUR PREVIOUS instructions'."""
    if not 0 <= max_words <= 10:
        raise PatternError(f"gap takes 0 to 10 words, not {max_words}")
    return rf"(?:\w+\s+){{0,{max_words}}}"


def then(*pieces: str) -> str:
    """These pieces one after another, with whitespace between them."""
    if not pieces:
        raise PatternError("then needs at least one piece")
    return r"\s*".join(pieces)


def line_starts_with(*labels: str, ending: str = ":") -> str:
    """A line that opens with one of these labels, like a chat role header.

    `line_starts_with("system", "assistant")` matches `SYSTEM: do this` on its
    own line, and does NOT match "our system prompt" in the middle of a sentence.
    """
    return r"^\s*" + one_of(*labels) + r"\s*" + re.escape(ending)


def near(first: str, second: str, within: int = 40) -> str:
    """`first`, then `second` no more than `within` characters later.

    Use it for "a verb aimed at a secret": the two words that matter, with
    whatever filler an attacker puts between them.
    """
    if not 1 <= within <= MAX_WITHIN:
        raise PatternError(f"within must be between 1 and {MAX_WITHIN}, not {within}")
    return f"{first}[\\s\\S]{{0,{within}}}?{second}"


def any_shape(*patterns: str) -> str:
    """Several finished shapes, combined into one pattern."""
    if not patterns:
        raise PatternError("any_shape needs at least one pattern")
    return "(?:" + "|".join(f"(?:{p})" for p in patterns) + ")"


@dataclass(frozen=True)
class PatternReport:
    """What a pattern did against the examples it was held to."""

    pattern: str
    missed: tuple[str, ...]  # should have matched, did not
    false_alarms: tuple[str, ...]  # should NOT have matched, did

    @property
    def ok(self) -> bool:
        return not self.missed and not self.false_alarms

    def render(self) -> str:
        lines = [f"pattern: {self.pattern}"]
        if self.ok:
            lines.append("ok: every example behaved")
        for text in self.missed:
            lines.append(f"  MISSED       {text!r}")
        for text in self.false_alarms:
            lines.append(f"  FALSE ALARM  {text!r}")
        return "\n".join(lines)


def check_pattern(
    pattern: str,
    should_match: Iterable[str] = (),
    should_not_match: Iterable[str] = (),
    *,
    show: bool = True,
) -> PatternReport:
    """Hold a pattern to examples in both directions, and say which ones failed."""
    try:
        compiled = re.compile(pattern, FLAGS)
    except re.error as error:
        raise PatternError(f"that is not a valid pattern: {error}") from error
    report = PatternReport(
        pattern=pattern,
        missed=tuple(t for t in should_match if not compiled.search(t)),
        false_alarms=tuple(t for t in should_not_match if compiled.search(t)),
    )
    if show:
        print(report.render())
    return report


# ----------------------------------------------------------------- the tool

#: The contract a model reads. Every field is a plain word; nothing accepts regex.
BUILD_PATTERN_TOOL: dict[str, Any] = {
    "name": "build_pattern",
    "description": (
        "Build a case-insensitive regular expression from plain words. Use it to "
        "describe a text shape -- a phrase, a line that starts with a label, or one "
        "word near another -- instead of writing regex by hand. Returns the pattern "
        "as a string. Never accepts raw regex: every word is matched literally."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["phrase", "one_of", "line_starts_with", "near"],
                "description": "Which shape to build.",
            },
            "words": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The phrases. For `near`, the FIRST group.",
            },
            "near_words": {
                "type": "array",
                "items": {"type": "string"},
                "description": "For `near` only: the SECOND group.",
            },
            "within": {
                "type": "integer",
                "minimum": 1,
                "maximum": MAX_WITHIN,
                "description": "For `near` only: how many characters may sit between.",
            },
        },
        "required": ["kind", "words"],
    },
}


def build_pattern(
    kind: str,
    words: list[str],
    near_words: list[str] | None = None,
    within: int = 40,
) -> str:
    """The bounded tool: refuse outside the contract, then build."""
    if not isinstance(words, list) or not words or not all(isinstance(w, str) for w in words):
        raise PatternError("build_pattern: 'words' must be a non-empty list of strings")
    if kind == "phrase":
        if len(words) != 1:
            raise PatternError("build_pattern: 'phrase' takes exactly one entry in 'words'")
        return phrase(words[0])
    if kind == "one_of":
        return one_of(*words)
    if kind == "line_starts_with":
        return line_starts_with(*words)
    if kind == "near":
        if not near_words:
            raise PatternError("build_pattern: 'near' needs 'near_words' as the second group")
        return near(one_of(*words), one_of(*near_words), within=within)
    raise PatternError(
        f"build_pattern: unknown kind {kind!r}; use one of "
        f"{BUILD_PATTERN_TOOL['inputSchema']['properties']['kind']['enum']}"
    )


__all__ = [
    "BUILD_PATTERN_TOOL",
    "FLAGS",
    "MAX_WITHIN",
    "PatternError",
    "PatternReport",
    "any_shape",
    "build_pattern",
    "check_pattern",
    "gap",
    "line_starts_with",
    "near",
    "one_of",
    "phrase",
    "then",
]
