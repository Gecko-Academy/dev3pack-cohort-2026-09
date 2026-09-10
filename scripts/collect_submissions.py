"""Merge the day's green submissions and regenerate the track.

    uv run python scripts/collect_submissions.py                  # dry run, read it
    uv run python scripts/collect_submissions.py --merge          # do it
    git -C ../dev3pack-submissions push

THE SAME SHAPE AS `publish_cohort.py`, on purpose: a dry run that shows exactly
what would happen, a flag that does it, and a push you make yourself. Two rituals
a week should not need two habits.

WHY A HUMAN STILL MERGES. Until the verification bundle exists, CI cannot re-run
a submitted notebook, so it checks the shape, the ownership, the notebook's hash
and the score's own arithmetic, and no more. The merge is where a person takes
responsibility for what those checks cannot see. This script refuses to merge
anything CI has not passed, which is a floor, not a substitute.

IT NEVER PUSHES. The last step stays yours, exactly as the publisher's does.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

#: The public archive. Named once here; the setup note names it too.
SUBMISSIONS_REPO = "Gecko-Academy/dev3pack-submissions"


class CollectError(Exception):
    """The round was refused. Nothing was merged."""


def _gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=120, check=False)
    if result.returncode != 0:
        raise CollectError(f"gh {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout


def open_submissions(repo: str) -> list[dict]:
    """Every open pull request, with the verdict CI reached on it."""
    listed = json.loads(
        _gh(
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            "200",
            "--json",
            "number,title,author,statusCheckRollup,files,isDraft,mergeable,baseRefName,headRefOid",
        )
    )
    rows = []
    for pull in listed:
        checks = pull.get("statusCheckRollup") or []
        conclusions = {c.get("conclusion") for c in checks if c.get("conclusion")}
        if not checks:
            state = "no checks yet"
        elif conclusions <= {"SUCCESS", "SKIPPED", "NEUTRAL"}:
            state = "green"
        elif any(c.get("status") not in {"COMPLETED", None} for c in checks):
            state = "still running"
        else:
            state = "red"
        # A green check is about ONE commit. Merging without naming that commit
        # merges whatever arrived after it, which is the whole distance between
        # "CI passed" and "CI passed on what I am about to merge".
        if pull.get("isDraft"):
            state = "draft"
        elif pull.get("baseRefName") not in (None, "main"):
            state = f"wrong base ({pull['baseRefName']})"
        elif pull.get("mergeable") == "CONFLICTING":
            state = "conflicting"
        rows.append(
            {
                "number": pull["number"],
                "author": pull["author"]["login"],
                "title": pull["title"],
                "state": state,
                "head": pull.get("headRefOid"),
                "files": [f["path"] for f in pull.get("files", [])],
            }
        )

    # One learner handing the same item in twice leaves two green pull requests
    # writing the same path. Merging both means the second silently overwrites
    # the first, and the round reads as two submissions when it was one.
    seen: dict[tuple[str, str], int] = {}
    for row in sorted(rows, key=lambda r: r["number"]):
        if row["state"] != "green":
            continue
        items = {Path(path).parent.name for path in row["files"] if path.startswith("submissions/")}
        for item in items:
            key = (row["author"], item)
            if key in seen:
                row["state"] = f"duplicate of #{seen[key]} for {item}"
            else:
                seen[key] = row["number"]
    return sorted(rows, key=lambda r: r["number"])


def merge(repo: str, number: int, head: str | None) -> None:
    """Squash-merge, refusing if the branch moved since its checks were read."""
    command = ["pr", "merge", str(number), "--repo", repo, "--squash", "--delete-branch"]
    if head:
        command += ["--match-head-commit", head]
    _gh(*command)


def regenerate(checkout: Path, cohort: str) -> str:
    """Rebuild the track in the checkout. Returns what the script printed."""
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "track.py"),
            "--from",
            str(checkout),
            "--cohort",
            cohort,
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        raise CollectError(f"the track could not be rebuilt:\n{result.stdout}{result.stderr}")
    return result.stdout


def _git(checkout: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(checkout), *args],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        raise CollectError(f"git {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=SUBMISSIONS_REPO)
    parser.add_argument(
        "--into",
        type=Path,
        help="checkout of the submissions repo (default: ../dev3pack-submissions)",
    )
    parser.add_argument("--cohort", default="2026-09")
    parser.add_argument("--merge", action="store_true", help="actually merge and rebuild")
    args = parser.parse_args(argv)

    checkout = args.into or ROOT.parent / "dev3pack-submissions"

    rows = open_submissions(args.repo)
    green = [r for r in rows if r["state"] == "green"]

    print(f"{args.repo}: {len(rows)} open, {len(green)} green\n")
    for row in rows:
        mark = {"green": "✓", "red": "✗"}.get(row["state"], "·")
        who = f"{row['author']:<20}"
        print(f"  {mark} #{row['number']:<4} {who} {row['state']:<14} {row['title'][:40]}")
        if row["state"] == "red":
            print("      leave it: the author fixes it and the checks re-run")

    if not args.merge:
        print(
            f"\nDry run. Nothing merged. Re-run with --merge to take the {len(green)} green one(s)."
        )
        return 0

    if not (checkout / ".git").is_dir():
        raise CollectError(
            f"{checkout} is not a git checkout. Clone it there first:\n"
            f"  git clone git@github.com:{args.repo}.git {checkout}"
        )

    for row in green:
        merge(args.repo, row["number"], row.get("head"))
        print(f"  merged #{row['number']} from {row['author']}")

    _git(checkout, "pull", "--quiet", "origin", "main")
    print("\n" + regenerate(checkout, args.cohort).strip())

    if not _git(checkout, "status", "--porcelain").strip():
        print("\nthe track was already current; nothing to commit")
        return 0

    _git(checkout, "add", "-A")
    _git(checkout, "commit", "-m", f"track: {len(green)} submission(s) merged")
    print(f"\nCommitted. Push it when you are ready:\n  git -C {checkout} push")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CollectError as error:
        print(f"\n{error}", file=sys.stderr)
        raise SystemExit(1) from error
