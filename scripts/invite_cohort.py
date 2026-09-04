"""Invite a cohort from a CSV, and report who has actually accepted.

    uv run python scripts/invite_cohort.py roster.csv           # dry run
    uv run python scripts/invite_cohort.py roster.csv --send    # actually invite
    uv run python scripts/invite_cohort.py --status             # who accepted

The CSV is `name,email`, one learner per row.

THE EMAIL MUST BE THE ONE GITHUB KNOWS. An invitation sent to an address GitHub
has never seen is accepted by the API, delivered to nobody, and expires in seven
days in silence. It is the commonest failure in this whole flow and it produces
no error anywhere, which is why `--status` exists: the only way to know an
invitation worked is to look at who accepted it.

THE ROSTER IS PERSONAL DATA. Names and email addresses of real people. This
refuses to read a roster that sits inside the repository unless git is ignoring
it, because the failure mode is committing thirty students' addresses and then
rewriting history to remove them. Keep it outside the repo.

Requires the `gh` CLI, authenticated with `admin:org` scope:

    gh auth refresh -h github.com -s admin:org
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ORG = "Gecko-Academy"
TEAM = "cohort-2026-09"

#: Deliberately permissive. This catches a typed mistake, not an invalid
#: address: only GitHub can say whether an address is one it knows.
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class InviteError(Exception):
    """The invite run was refused. Nothing was sent."""


def _gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60, check=False)
    if result.returncode != 0:
        raise InviteError(f"gh {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout


def read_roster(path: Path) -> list[tuple[str, str]]:
    """Read `name,email` rows, refusing a roster that could be committed."""
    if not path.is_file():
        raise InviteError(f"no roster at {path}")

    # Personal data must not sit committable inside the repo.
    try:
        inside = path.resolve().relative_to(ROOT)
    except ValueError:
        inside = None
    if inside is not None:
        ignored = subprocess.run(["git", "check-ignore", "-q", str(inside)], cwd=ROOT, check=False)
        if ignored.returncode != 0:
            raise InviteError(
                f"{inside} is inside the repository and git is NOT ignoring it.\n"
                "It holds real names and email addresses. Move it outside the repo, or add "
                "it to .gitignore first. Committing a roster is not undone by deleting it."
            )

    rows: list[tuple[str, str]] = []
    problems: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for line, row in enumerate(csv.DictReader(handle), start=2):
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip()
            if not email:
                problems.append(f"line {line}: no email")
                continue
            if not EMAIL.match(email):
                problems.append(f"line {line}: {email!r} is not an email address")
                continue
            rows.append((name or email, email))
    if problems:
        raise InviteError("the roster has problems:\n  " + "\n  ".join(problems))
    duplicates = {e for _, e in rows if [x for _, x in rows].count(e) > 1}
    if duplicates:
        raise InviteError(f"the roster repeats: {sorted(duplicates)}")
    if not rows:
        raise InviteError("the roster is empty; expected a header row `name,email`")
    return rows


def team_id() -> int:
    return int(json.loads(_gh("api", f"orgs/{ORG}/teams/{TEAM}"))["id"])


def pending() -> dict[str, str]:
    """Invitations sent and not yet accepted, by email."""
    sent = json.loads(_gh("api", f"orgs/{ORG}/invitations", "--paginate"))
    return {i["email"]: i.get("created_at", "") for i in sent if i.get("email")}


def members() -> set[str]:
    listed = json.loads(_gh("api", f"orgs/{ORG}/members", "--paginate"))
    return {m["login"] for m in listed}


def status() -> int:
    waiting = pending()
    joined = members()
    print(f"{ORG}: {len(joined)} member(s), {len(waiting)} invitation(s) still pending\n")
    for login in sorted(joined):
        print(f"  joined   {login}")
    for email, when in sorted(waiting.items()):
        print(f"  pending  {email:40} sent {when[:10]}")
    if waiting:
        print(
            "\nAn invitation expires after seven days. A pending row can also mean the "
            "address is not one GitHub knows, in which case it will never arrive."
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roster", nargs="?", type=Path, help="CSV with name,email")
    parser.add_argument("--send", action="store_true", help="actually invite; otherwise dry run")
    parser.add_argument("--status", action="store_true", help="who has accepted, who has not")
    args = parser.parse_args(argv)

    if args.status:
        return status()
    if args.roster is None:
        parser.print_help()
        return 2

    rows = read_roster(args.roster)
    already = pending().keys() | set()
    joined = members()

    print(f"roster: {len(rows)} learner(s) -> {ORG}, team {TEAM}, permission read\n")
    to_send = []
    for name, email in rows:
        if email in already:
            print(f"  skip     {name:28} {email:36} invitation already pending")
        else:
            to_send.append((name, email))
            print(f"  invite   {name:28} {email}")

    if not args.send:
        print(f"\nDry run. Nothing sent. {len(to_send)} would be invited.")
        print("Re-run with --send once the list above is right.")
        return 0

    identifier = team_id()
    for name, email in to_send:
        _gh(
            "api",
            "-X",
            "POST",
            f"orgs/{ORG}/invitations",
            "-f",
            f"email={email}",
            "-F",
            f"team_ids[]={identifier}",
            "-f",
            "role=direct_member",
        )
        print(f"  sent     {name:28} {email}")
    print(f"\n{len(to_send)} invitation(s) sent. Check acceptance with --status.")
    print(f"{len(joined)} learner(s) had already joined.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InviteError as error:
        print(f"\n{error}", file=sys.stderr)
        raise SystemExit(1) from error
