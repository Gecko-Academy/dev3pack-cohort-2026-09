"""`bootcamp status --github <you>`: what is done, what is missing, and the command for each.

Students mixed up three things with similar names: the `cap01` notebook, the final
assignment (the only one that earns the certificate) and the Gecko capstone. One of
them finished `cap01` at 500/500 and believed the final was done (4 Oct 2026). This
reads what the submissions repository already publishes about one student and prints
a checklist, each missing piece followed by the exact command that finishes it.

READ-ONLY, PUBLIC, NO KEY. It reads `track.json` and `finals/<you>/result.json` from
the submissions repository, and, only when no final was handed in, whether
`<you>/my-final-assignment` exists on GitHub. It never sends anything.

WHAT IT CANNOT SEE: a pull request that has not merged yet. The track shows a
hand-in a few minutes after its merge, and this says so.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from bootcamp_agent.curriculum import SUBMISSIONS_REPO
from bootcamp_agent.questions_api import QuestionsError, urllib_transport

RAW = f"https://raw.githubusercontent.com/{SUBMISSIONS_REPO}/main"
TRACK_URL = f"{RAW}/track.json"
FORM_URL = f"https://github.com/{SUBMISSIONS_REPO}/issues/new?template=gecko-capstone.yml"
FINAL_PAGE = "https://gecko-academy.github.io/dev3pack-cohort-2026-09/unit3/final-assignment.html"
FINISH_LINE = f"https://github.com/{SUBMISSIONS_REPO}/blob/main/TRACK.md#finish-line"
DEADLINE = "5 October"
RESULT_PAGE = f"https://github.com/{SUBMISSIONS_REPO}/blob/main/finals/{{github}}/result.json"

Fetch = Callable[[str, float], tuple[int, bytes]]


class StatusError(Exception):
    """The status could not be read. Safe to show as is."""


@dataclass
class Status:
    github: str
    certificate: bool = False
    lines: list[str] = field(default_factory=list)

    def rendered(self) -> str:
        return "\n".join(self.lines)


def _get_json(fetch: Fetch, url: str) -> Any | None:
    """The parsed document, or None for a 404. Anything else is a StatusError."""
    try:
        code, body = fetch(url, 20)
    except QuestionsError as error:
        raise StatusError(f"could not reach GitHub: {error}") from error
    if code == 404:
        return None
    if code != 200:
        raise StatusError(f"GitHub answered {code} for {url}")
    try:
        return json.loads(body)
    except ValueError as error:
        raise StatusError(f"{url} is not JSON") from error


def _final_section(status: Status, row: dict | None, fetch: Fetch) -> None:
    gh = status.github
    final = (row or {}).get("final")
    say = status.lines.append
    say("1. FINAL ASSIGNMENT: earns the certificate")
    if final and final.get("certificate_eligible"):
        status.certificate = True
        say(f"   DONE. Scored {final.get('percent')}%: certificate earned.")
        return
    if final:
        say(f"   Handed in, but NOT passed yet: scored {final.get('percent')}%.")
        result = _get_json(fetch, f"{RAW}/finals/{gh}/result.json") or {}
        gates = result.get("gates") or {}
        if gates.get("overall_threshold") is False:
            say("   - Below 30%: your agent needs to answer more questions correctly.")
        critical = [
            r.get("task_id")
            for r in result.get("results", [])
            if r.get("critical") and not r.get("passed")
        ]
        if critical:
            say(f"   - Critical question(s) failed: {', '.join(map(str, critical))}.")
            say("     Every critical question must pass, whatever the score.")
        say("   What to do, inside your my-final-assignment folder:")
        say(f"     a. See every verdict:  {RESULT_PAGE.format(github=gh)}")
        say('     b. Watch one:  uv run bootcamp final trace "<the question>"')
        say(
            "     c. Check all answers, sending nothing:  "
            f"uv run bootcamp final submit --github {gh} --dry-run"
        )
        say('     d. Save:  git add -A && git commit -m "fix" && git push')
        say(f"     e. Hand in:  uv run bootcamp final submit --github {gh}")
        return
    exists = _get_json(fetch, f"https://api.github.com/repos/{gh}/my-final-assignment")
    if exists is not None:
        say("   NOT handed in yet. Your my-final-assignment repository exists.")
        say("   What to do, inside your my-final-assignment folder:")
        say("     a. Practise:  uv run bootcamp final grade")
        say('     b. Save:  git add -A && git commit -m "final" && git push')
        say(f"     c. Hand in:  uv run bootcamp final submit --github {gh}")
    else:
        say("   NOT started: you have no my-final-assignment repository.")
        say("   The cap01 notebook is NOT the final assignment. The final is your own agent,")
        say("   in its own repository, answering 15 private questions.")
        say("   What to do, from your course folder:")
        say("     a. git pull && uv sync")
        say("     b. uv run bootcamp final new ../my-final-assignment")
        say("     c. cd ../my-final-assignment && uv sync")
        say('     d. git add uv.lock && git commit -m "lock"')
        say("     e. gh repo create my-final-assignment --public --source . --push")
        say("     f. Build your agent, then:  uv run bootcamp final grade")
        say(f"     g. Hand in:  uv run bootcamp final submit --github {gh}")
    say(f"   Every step: {FINAL_PAGE}")
    say("   To pass: 30% or more AND every critical question right.")


def _gecko_section(status: Status, row: dict | None) -> None:
    say = status.lines.append
    gecko = (row or {}).get("gecko")
    say("2. GECKO CAPSTONE: your my-gecko-buyer link")
    if gecko:
        say(f"   DONE. Handed in at commit {str(gecko.get('commit', ''))[:7]}.")
        say("   Pushed more since? Edit your issue and the newest commit is recorded.")
    else:
        say("   NOT handed in. Push your receipts, refusals and smoke-report.json, then")
        say("   paste your my-gecko-buyer link here and press Submit:")
        say(f"     {FORM_URL}")


def _track_section(status: Status, track: dict) -> None:
    gh = status.github.lower()
    say = status.lines.append
    marked = [i for i in track.get("items", []) if i.get("scored")]
    mine = {
        e["item"]: e for e in track.get("entries", []) if str(e.get("github", "")).lower() == gh
    }
    earned = sum(int(mine[i["id"]].get("score") or 0) for i in marked if i["id"] in mine)
    total = sum(int(i.get("max_score") or 0) for i in marked)
    say(f"3. TRACK: {earned}/{total} marks (does not affect the certificate)")
    missing = [i for i in marked if i["id"] not in mine]
    partial = [
        i
        for i in marked
        if i["id"] in mine and (mine[i["id"]].get("score") or 0) < (i.get("max_score") or 0)
    ]
    if not missing and not partial:
        say("   DONE. Every marked item at full marks.")
        return
    for item in missing:
        say(f"   - {item['id']} not handed in ({item['title']}):")
        say(f"       uv run bootcamp submit {item['id']} --github {status.github} --push")
    for item in partial:
        got = mine[item["id"]].get("score") or 0
        say(
            f"   - {item['id']} at {got}/{item['max_score']}: finish the exercises, then "
            f"submit again with the same command."
        )


def read_status(github: str, fetch: Fetch = urllib_transport) -> Status:
    track = _get_json(fetch, TRACK_URL)
    if not isinstance(track, dict):
        raise StatusError("the track could not be read")
    canonical = next(
        (
            r["github"]
            for r in track.get("finish_line", [])
            if str(r.get("github", "")).lower() == github.lower()
        ),
        github,
    )
    status = Status(github=canonical)
    row = next((r for r in track.get("finish_line", []) if r.get("github") == canonical), None)
    status.lines += [f"Status for {canonical}, due {DEADLINE}", ""]
    _final_section(status, row, fetch)
    status.lines.append("")
    _gecko_section(status, row)
    status.lines.append("")
    _track_section(status, track)
    status.lines += [
        "",
        "CERTIFICATE: " + ("earned." if status.certificate else "not yet: see 1 above."),
        "A hand-in appears here a few minutes after its pull request merges.",
        f"Everyone's row: {FINISH_LINE}",
    ]
    return status
