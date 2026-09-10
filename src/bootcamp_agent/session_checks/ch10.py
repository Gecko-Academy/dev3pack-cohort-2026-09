"""Session 10: the architecture decision record.

`ch10-e1` lives in `checks.py` and judges the skill the learner authored. This
module adds `ch10-e2`, the session's other artifact: one architecture decision
they actually made in the capstone, written down so a stranger can tell whether
it is still the right one.

WHAT MAKES A DECISION CHECKABLE. The record is prose, and prose is easy to fake.
Four fields make it falsifiable anyway:

  decision            what was chosen, phrased as a choice rather than as a
                      description of the code as it stands
  options_considered  at least two. One option is a justification written
                      afterwards; two is the smallest record of a real choice
  why_not             the reason the option they turned down lost, today
  reverses_it         the measurement or event that would change their mind

`reverses_it` is the load-bearing field, and it is judged exactly the way the
depth track judges `d3-e1.reverses_when`: it needs a number and a unit, because
"when it gets slow" is an opinion and "p95 above 2000 ms for 15 minutes" is a
trigger somebody can check. The unit vocabulary is imported from
:mod:`bootcamp_agent.depth_checks` rather than copied, so a reversal trigger has
one standard in this course instead of two that drift apart. That import also
registers the optional depth track into the shared registry, which costs a dict
of a dozen entries and changes nothing a session notebook reads: `review()`
scores by id prefix.

Nothing here runs a model or touches the network. The session is handed in, not
marked, so these messages are written to be read by the learner while they fix
the record — every one of them names the fix.
"""

from __future__ import annotations

import re
from typing import Any

from bootcamp_agent.checks import register
from bootcamp_agent.depth_checks import _UNITS as REVERSAL_UNITS

#: The record's fields, exactly. An extra key is usually a field from the depth
#: track's `d3-e1` pasted in, so the message names both.
FIELDS = ("decision", "options_considered", "why_not", "reverses_it")

#: Words that mean the line was left unwritten, as in `checks.py`.
_PLACEHOLDERS = ("", "...", "todo", "tbd", "n/a", "na", "none", "-", "?")

#: Words that turn a sentence into a choice. "The capstone loop is hand-written"
#: describes the code; "we keep the hand-written loop" records that somebody
#: decided it, and only the second can be reversed later.
_CHOICE_WORDS = (
    "chose",
    "chosen",
    "choose",
    "choosing",
    "decide",
    "decided",
    "pick",
    "picked",
    "select",
    "selected",
    "keep",
    "keeping",
    "kept",
    "adopt",
    "adopted",
    "use",
    "uses",
    "using",
    "used",
    "went with",
    "go with",
    "going with",
    "stay",
    "staying",
    "stick",
    "sticking",
    "switch",
    "switched",
    "replace",
    "replaced",
    "ship",
    "shipped",
    "build",
    "built",
    "wrote",
    "write",
    "reject",
    "rejected",
    "drop",
    "dropped",
)
_CHOICE = re.compile(r"\b(" + "|".join(_CHOICE_WORDS) + r")\b", re.IGNORECASE)


def _unwritten(text: object, minimum: int = 20) -> bool:
    """True when a field is missing, a placeholder, or too short to be an answer."""
    if not isinstance(text, str):
        return True
    stripped = text.strip()
    return stripped.lower() in _PLACEHOLDERS or len(stripped) < minimum


def _fields_problem(record: object) -> str | None:
    if not isinstance(record, dict):
        return f"expected the adr dict with keys {FIELDS}"
    missing = sorted(set(FIELDS) - set(record))
    extra = sorted(set(record) - set(FIELDS))
    if missing:
        return f"the record is missing {missing}; the four fields are {FIELDS}"
    if extra:
        return (
            f"the record carries {extra}, which this check does not read; "
            f"keep it to {FIELDS} (the depth track's d3-e1 uses different names)"
        )
    return None


def _decision_problem(decision: object) -> str | None:
    if _unwritten(decision, minimum=20):
        return "'decision' is not written yet: one sentence naming what you chose"
    if not _CHOICE.search(str(decision)):
        return (
            "'decision' describes the code instead of recording a choice. Phrase it as "
            "something you chose: 'we keep the hand-written loop in agent.py', not "
            "'the capstone loop is hand-written'"
        )
    return None


def _options_problem(options: object) -> str | None:
    if not isinstance(options, (list, tuple)):
        return "'options_considered' is a list of the options you weighed, at least two of them"
    if len(options) < 2:
        return (
            f"'options_considered' names {len(options)} option; one option is a justification "
            "written afterwards, not a decision. Add the option you turned down"
        )
    for index, option in enumerate(options):
        if _unwritten(option, minimum=4):
            return (
                f"options_considered[{index}] is {option!r}; name the option in a few words, "
                "the way you would say it out loud"
            )
    seen = [str(option).strip().lower() for option in options]
    if len(set(seen)) != len(seen):
        return (
            "'options_considered' lists the same option twice; two names for one option "
            "is still one option"
        )
    return None


def _why_not_problem(why_not: object, decision: object) -> str | None:
    if _unwritten(why_not, minimum=25):
        return (
            "'why_not' is the reason the option you turned down lost. Write the reason, "
            "not the verdict: 'it adds a dependency and a second vocabulary for four nodes'"
        )
    if str(why_not).strip().lower() == str(decision).strip().lower():
        return (
            "'why_not' repeats the decision. It answers the other question: why the option "
            "you did not take lost, today"
        )
    return None


def _reversal_problem(trigger: object) -> str | None:
    """The reversal test, judged as `depth_checks._d3_e1` judges `reverses_when`."""
    if _unwritten(trigger, minimum=20):
        return (
            "'reverses_it' is the whole exercise: the measurement or the event that would "
            "make you change this decision. Write the condition out"
        )
    text = str(trigger)
    if not re.search(r"\d", text):
        return (
            "'reverses_it' has no number in it. 'When it gets slow' is an opinion; "
            "'when p95 stays over 2000 ms for 15 minutes' is a trigger somebody can check"
        )
    if not any(unit in text.lower() for unit in REVERSAL_UNITS):
        return (
            "'reverses_it' has a number but no unit. A number without a unit cannot be "
            "compared against anything"
        )
    return None


@register("ch10-e2")
def _ch10_e2(record: Any) -> str | None:
    """One architecture decision, with the two options, the reason, and the reversal."""
    if problem := _fields_problem(record):
        return problem
    if problem := _decision_problem(record["decision"]):
        return problem
    if problem := _options_problem(record["options_considered"]):
        return problem
    if problem := _why_not_problem(record["why_not"], record["decision"]):
        return problem
    return _reversal_problem(record["reverses_it"])
