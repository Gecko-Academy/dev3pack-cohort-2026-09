"""Hints you can always have, and that cost you something.

    check("ch03-e1", value)   # the verdict, and the fix, named
    hint("ch03-e1")           # the next nudge, -30 XP
    hint("ch03-e1", reveal=True)   # the worked answer, -70 XP

THE MODEL IS DATACAMP'S, AND IT IS BETTER THAN HIDING THE ANSWER. Their exercise
pane carries a "Receber Dica (-30 XP)" button: the hint is always one click
away, never gated, and it costs part of the exercise's points. That keeps the
incentive to think without ever leaving somebody stuck and stuck, which is what
a gate does.

Nothing here blocks. There is no unlock, no waiting period and no server. If you
want the answer immediately you can have it immediately, and the scorecard will
say so.

WHAT IS RECORDED, AND WHERE. A single SQLite file at ~/.bootcamp/progress.db, on
your machine, gitignored, and it never leaves unless you run
`bootcamp progress --export` yourself. It stores exercise ids and outcomes.

It does NOT store your answers, your name, your email, or anything you typed.
That is the same rule the depth track's data module makes you write down, and it
would be a poor course that taught a retention policy it did not keep.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

#: What an exercise is worth, and what each level of help costs. A hint leaves
#: most of the credit; a reveal leaves a little, because reading the answer
#: after trying is still worth more than skipping.
FULL_MARKS = 100
HINT_COST = 30
REVEAL_COST = 70

STORE_ENV = "BOOTCAMP_PROGRESS_DB"


def store_path() -> Path:
    """Where progress lives. Overridable, mostly so tests do not touch yours."""
    override = os.environ.get(STORE_ENV)
    return Path(override) if override else Path.home() / ".bootcamp" / "progress.db"


def _connect() -> sqlite3.Connection:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        "create table if not exists attempts ("
        " exercise text primary key,"
        " passed integer not null default 0,"
        " attempts integer not null default 0,"
        " hinted integer not null default 0,"
        " revealed integer not null default 0,"
        " first_seen text not null default (datetime('now')),"
        " last_seen text not null default (datetime('now')))"
    )
    connection.commit()
    return connection


@dataclass(frozen=True)
class Attempt:
    """One exercise's history. Outcomes only; never what was typed."""

    exercise: str
    passed: bool
    attempts: int
    hinted: bool
    revealed: bool

    @property
    def score(self) -> int:
        """Full marks, less whatever help was taken. Zero until it passes."""
        if not self.passed:
            return 0
        earned = FULL_MARKS
        if self.revealed:
            earned -= REVEAL_COST
        elif self.hinted:
            earned -= HINT_COST
        return max(earned, 0)


def record(exercise: str, *, passed: bool) -> None:
    """Note an attempt. Called by `check`; you should not need this yourself."""
    with _connect() as connection:
        connection.execute(
            "insert into attempts (exercise, passed, attempts) values (?, ?, 1) "
            "on conflict(exercise) do update set "
            " attempts = attempts.attempts + 1,"
            " passed = max(attempts.passed, excluded.passed),"
            " last_seen = datetime('now')",
            (exercise, int(passed)),
        )


def _mark(exercise: str, column: str) -> None:
    with _connect() as connection:
        connection.execute(
            f"insert into attempts (exercise, {column}) values (?, 1) "
            f"on conflict(exercise) do update set {column} = 1, last_seen = datetime('now')",
            (exercise,),
        )


def attempt(exercise: str) -> Attempt:
    with _connect() as connection:
        row = connection.execute(
            "select passed, attempts, hinted, revealed from attempts where exercise = ?",
            (exercise,),
        ).fetchone()
    if row is None:
        return Attempt(exercise, passed=False, attempts=0, hinted=False, revealed=False)
    return Attempt(exercise, bool(row[0]), int(row[1]), bool(row[2]), bool(row[3]))


def all_attempts() -> list[Attempt]:
    with _connect() as connection:
        rows = connection.execute(
            "select exercise, passed, attempts, hinted, revealed from attempts order by exercise"
        ).fetchall()
    return [Attempt(r[0], bool(r[1]), int(r[2]), bool(r[3]), bool(r[4])) for r in rows]


def hint(exercise: str, *, reveal: bool = False) -> bool:
    """Print the next level of help, and record that it was taken.

    Returns True when something was printed. The cost is applied once: asking
    twice does not charge twice, because re-reading a hint you already paid for
    should never be discouraged.
    """
    from bootcamp_agent.checks import CHECKS, UnknownCheck

    if exercise not in CHECKS:
        raise UnknownCheck(f"no exercise {exercise!r}; known: {sorted(CHECKS)}")

    text = (HINTS.get(exercise) or {}).get("reveal" if reveal else "hint")
    if not text:
        where = "reveal" if reveal else "hint"
        print(
            f"no {where} written for {exercise} yet. The ❌ line from check() names the fix, "
            "and the worked answer is in this chapter's solutions/notebook.ipynb"
        )
        return False

    current = attempt(exercise)
    already = current.revealed if reveal else current.hinted
    _mark(exercise, "revealed" if reveal else "hinted")

    cost = REVEAL_COST if reveal else HINT_COST
    banner = "answer" if reveal else "hint"
    price = "already taken, no further cost" if already else f"-{cost} XP"
    print(f"💡 {banner} for {exercise}  ({price})\n")
    print(text.strip())
    if not reveal:
        print(
            f"\nStill stuck? hint({exercise!r}, reveal=True) shows the answer (-{REVEAL_COST} XP)."
        )
    return True


#: Written per exercise, and deliberately not generated. A hint that does not
#: know which mistake you probably made is not a hint.
#:
#: Two tiers. `hint` is the nudge that gets an unstuck person moving; `reveal`
#: is the worked answer AND the reason, because an answer without the reason
#: teaches the next exercise nothing.
HINTS: dict[str, dict[str, str]] = {
    "w01-e2": {
        "hint": (
            "Think about what `Path('/').parent` returns. It is not an error, and it is not "
            "None. Print it and the loop's problem becomes obvious."
        ),
        "reveal": (
            "    while not (here / 'pyproject.toml').exists() and here != here.parent:\n"
            "        here = here.parent\n\n"
            "`Path('/').parent` is `Path('/')` again, so a loop that only checks for the file "
            "climbs past the root forever. Comparing a directory with its own parent is the "
            "only stopping condition that cannot run away, and you will see this idiom in "
            "every notebook in this course."
        ),
    },
    "w03-e1": {
        "hint": (
            "The default `[]` is written once, in the `def` line. How many times does Python "
            "execute that line? Not once per call."
        ),
        "reveal": (
            "    def add_tag(tag, tags=None):\n"
            "        if tags is None:\n"
            "            tags = []\n"
            "        tags.append(tag)\n"
            "        return tags\n\n"
            "A default argument is evaluated once, when the function is defined, so a bare "
            "`[]` is a single list shared by every call for the life of the process. `None` "
            "is immutable and cannot be shared, so building the list inside gives each call "
            "its own."
        ),
    },
    "w04-e1": {
        "hint": (
            "You need three things in the URL: the endpoint that means 'today', the currency "
            "you are starting from, and a filter so you get one rate back instead of thirty."
        ),
        "reveal": (
            "    https://api.frankfurter.dev/v1/latest?base=USD&symbols=BRL\n\n"
            "`/v1/latest` is today's rate; a date in the path is the historical endpoint. "
            "`base` is what you hold, `symbols` is what you want it in. Without `symbols` the "
            "response carries every currency the ECB publishes, and you pay for all of them "
            "in bytes, latency and attention."
        ),
    },
    "w04-e3": {
        "hint": (
            "Ask who is harmed. A public read endpoint answering without a key costs its "
            "owner some rate limiting. Does it expose anything that was meant to be private?"
        ),
        "reveal": (
            "It is not a vulnerability. Keys on an API like this buy a rate tier, not entry, "
            "and a public read endpoint answering publicly is the product working.\n\n"
            "What it is: a specification describing something the endpoint does not enforce. "
            "An agent reading only the spec concludes it needs a key it does not have, and "
            "either refuses to call or invents an Authorization header. A working endpoint "
            "looks closed to it. One request with no key settled the question in less time "
            "than reading the security section took."
        ),
    },
}
