"""Weekly challenges: optional, judged by behaviour, and added to their session's row.

Importing a module here registers its check in `bonus.BONUS`, never in
`checks.CHECKS`, so a session's own exercises (and `review()`, and
`bootcamp check`) are exactly what they were. A learner who skips the week
loses nothing.

WHERE THE POINTS GO (founder ruling, 2026-09-22). A challenge is written at the
end of its session notebook and handed in with it. The submissions repository's
track reads the LAST `   week N challenge: S/500` line the check printed into that
notebook and adds it to the session's score, capped at the challenge's own full
marks. No new item and no new column: week 1 adds to ch05, week 2 to ch10.
That line is a contract with `render_track.py`; change its wording in both places
or in neither.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Challenge:
    """One weekly challenge, and the session row its points are added to."""

    week: int
    session: str
    bonus_id: str
    out_of: int = 500


#: session id -> its challenge. The one table `items.json` and the tests read.
CHALLENGES: dict[str, Challenge] = {
    "ch05": Challenge(week=1, session="ch05", bonus_id="week1-bot"),
    "ch10": Challenge(week=2, session="ch10", bonus_id="week2-store"),
}


def challenge_points(session_id: str) -> int:
    """The most a session's weekly challenge can add to its row; 0 if it has none."""
    challenge = CHALLENGES.get(session_id)
    return challenge.out_of if challenge else 0


__all__ = ["CHALLENGES", "Challenge", "challenge_points"]
