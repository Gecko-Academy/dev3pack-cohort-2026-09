"""`bootcamp gecko submit`: hand in the LINK to your Gecko capstone.

The Gecko capstone lives in the student's own `my-gecko-buyer` repository and is
judged from there. What travels is one file, `submissions/<github>/gecko/
submission.json`: which repository, at which commit. Nothing is scored here.

Runs from the COURSE folder, pointed at the capstone with `--repo`, because
`my-gecko-buyer` does not install the course package.

The repository checks are the final assignment's (`submit_checks.check_repo`):
clean, on GitHub, not the course template, HEAD pushed. The link must show the
code and the receipts the judges will read.

Missing evidence is a WARNING, never a refusal: a student with no landed
purchase yet still hands in, and the judges see what is there.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from bootcamp_agent import handin
from bootcamp_agent.capstone_submit import check_github
from bootcamp_agent.submit_checks import RepoState, SubmitError, check_repo

ITEM_ID = "gecko"
SUBMIT_COMMAND = "bootcamp gecko submit"
DEADLINE = "5 October"

Say = Callable[[str], None]

__all__ = ["SubmitError", "Submitted", "evidence_warnings", "submission_payload", "submit"]


def evidence_warnings(repo: Path) -> list[str]:
    """What the judges will look for and not find. Empty means it is all there."""
    found: list[str] = []
    receipts = sorted((repo / "receipts").glob("*.md")) if (repo / "receipts").is_dir() else []
    if not receipts:
        found.append(
            "no receipts/*.md: no landed purchase is committed. Run "
            '`uv run buyer "one espresso" --devnet`, commit receipts/, push, hand in again.'
        )
    if not (repo / "smoke-report.json").is_file():
        found.append(
            "no smoke-report.json: run `make smoke` (or `make smoke-recorded`), commit it, push."
        )
    if not (repo / "refusals").is_dir() or not any((repo / "refusals").iterdir()):
        found.append(
            "no refusals/: commit the refusals your buyer wrote (`make smoke` writes them)."
        )
    return found


def submission_payload(*, github: str, state: RepoState, now: datetime) -> dict[str, str]:
    return {
        "kind": ITEM_ID,
        "github": github,
        "repo": state.url,
        "commit": state.commit,
        "submitted_at": now.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_bundle(root: Path, github: str, submission: dict[str, str]) -> Path:
    """`<root>/<github>/gecko/submission.json`, alone in its folder."""
    where = root / github / ITEM_ID
    if where.exists():
        shutil.rmtree(where)
    where.mkdir(parents=True)
    (where / "submission.json").write_text(
        json.dumps(submission, indent=2) + "\n", encoding="utf-8"
    )
    return where


def default_root() -> Path:
    return Path.home() / ".bootcamp" / "gecko"


@dataclass(frozen=True)
class Submitted:
    bundle: Path
    pr_url: str | None
    warnings: list[str]


def submit(
    repo: Path,
    *,
    github: str,
    push: bool = False,
    dry_run: bool = False,
    into: Path | None = None,
    git_run: object = handin._run,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    say: Say = print,
) -> Submitted:
    """Check the repository, write the link, open the pull request. Raises SubmitError."""
    github = check_github(github)
    repo = repo.expanduser().resolve()
    if not repo.is_dir():
        raise SubmitError(
            f"{repo} is not a folder. Pass your capstone folder: --repo ../my-gecko-buyer"
        )
    state = check_repo(repo, kind="gecko")
    # The submissions check refuses a repository under another account (it would
    # be somebody else's buyer), so say it here, before a pull request fails.
    owner = state.url.split("/")[3]
    if owner.lower() != github.lower():
        raise SubmitError(
            f"{state.url} belongs to {owner!r}, not to {github!r}. Hand in your own "
            f"my-gecko-buyer, under https://github.com/{github}/."
        )
    say(f"repository: {state.url}")
    say(f"commit:     {state.commit}")

    warnings = evidence_warnings(repo)
    for warning in warnings:
        say(f"  warning: {warning}")
    if not warnings:
        say("  evidence: receipts/, refusals/ and smoke-report.json are committed")

    submission = submission_payload(github=github, state=state, now=now())
    root = Path(tempfile.mkdtemp(prefix="gecko-link-")) if dry_run else (into or default_root())
    where = write_bundle(root, github, submission)

    if dry_run or not push:
        say(f"\n--- {where / 'submission.json'}")
        say((where / "submission.json").read_text(encoding="utf-8").rstrip())
        if dry_run:
            say("\ndry run: nothing was handed in.")
            return Submitted(where, None, warnings)
        say(
            handin.manual_route(
                github,
                ITEM_ID,
                where,
                files=("submission.json",),
                command=f"uv run {SUBMIT_COMMAND} --repo {repo} --github {github} --push",
            )
        )
        return Submitted(where, None, warnings)

    try:
        url = handin.push(where, github, ITEM_ID, run=git_run, command=SUBMIT_COMMAND)
    except handin.HandInError as error:
        say(f"\n{error}")
        say(
            handin.manual_route(
                github, ITEM_ID, where, files=("submission.json",), command=SUBMIT_COMMAND
            )
        )
        return Submitted(where, None, warnings)
    say(f"\nhanded in: {url}")
    say(
        f"It merges itself once its check passes, and your link appears under Finish line "
        f"in TRACK.md. Push more and hand in again any time before {DEADLINE}: the latest "
        "commit counts."
    )
    return Submitted(where, url, warnings)
