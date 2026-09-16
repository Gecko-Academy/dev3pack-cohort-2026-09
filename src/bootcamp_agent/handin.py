"""Fork, commit, push and open the pull request — so nobody has to know git.

    uv run bootcamp submit ch02 --github you --push

WHY THIS EXISTS, in one number. On day one 26 people forked the submissions
repository and 2 opened a pull request. Everything before this step worked for
them; the seven manual git commands after it did not. This is that step, as one
flag.

WHAT IT REFUSES TO DO. It never touches the course repository, never force-
pushes, and never opens a pull request against anything but the submissions
repo. It re-uses an open pull request rather than stacking a second one, because
a learner re-submitting is the normal case and not a mistake.

HOW IT IS TESTED. Every git and gh call goes through one injected runner, so the
whole sequence can be driven offline against a fake and asserted command by
command. A flow whose only test is running it for real is a flow nobody dares
change.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from bootcamp_agent.curriculum import SUBMISSIONS_REPO


class HandInError(Exception):
    """The hand-in could not be completed, with a message a learner can act on."""


@dataclass(frozen=True)
class Ran:
    code: int
    out: str


def _run(command: list[str], cwd: Path | None = None) -> Ran:
    finished = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return Ran(finished.returncode, (finished.stdout + finished.stderr).strip())


Runner = type(_run)


def _require_gh(run: object) -> None:
    if shutil.which("gh") is None:
        raise HandInError(
            "`--push` needs the GitHub CLI, which is not installed.\n"
            "    https://cli.github.com  — then: gh auth login\n"
            "Without it, the folder is written and the manual steps are printed."
        )
    if run(["gh", "auth", "status"]).code != 0:  # type: ignore[operator]
        raise HandInError("gh is installed but not signed in. Run: gh auth login")


def _fork_name(forked_output: str, github: str) -> str:
    """What the fork is ACTUALLY called, from what gh just said about it.

    Deriving it as `<you>/<upstream name>` is wrong for anybody whose fork has a
    different name -- and on this course that is not hypothetical. The
    submissions repository used to carry the cohort date; everyone who forked
    before it was renamed still has `dev3pack-submissions-2026-09`, and the
    derived name 404s with "Could not resolve to a Repository", which reads like
    the fork failed rather than like it was looked for under the wrong name.

    gh names the fork in both of its outcomes -- "Created fork <owner>/<name>"
    and "<owner>/<name> already exists" -- so the answer is in the reply we
    already have. The derived name is only the fallback.
    """
    import re

    found = re.search(rf"\b{re.escape(github)}/([A-Za-z0-9._-]+)", forked_output)
    if found:
        return f"{github}/{found.group(1)}"
    return f"{github}/{SUBMISSIONS_REPO.split('/')[1]}"


def push(bundle: Path, github: str, item_id: str, run: object = _run) -> str:
    """Put `bundle` on the learner's fork and open a pull request. Returns its URL.

    `bundle` is the directory `submit` just wrote: `<root>/<github>/<item>`.
    """
    _require_gh(run)
    if not bundle.is_dir():
        raise HandInError(f"nothing to hand in: {bundle} does not exist")

    branch = f"submit/{item_id}"

    # Idempotent: gh says "already exists" and exits 0 when the fork is there.
    forked = run(["gh", "repo", "fork", SUBMISSIONS_REPO, "--clone=false", "--remote=false"])
    if forked.code != 0 and "already exists" not in forked.out.lower():
        raise HandInError(f"could not fork {SUBMISSIONS_REPO}:\n{forked.out}")

    fork = _fork_name(forked.out, github)

    work = Path.home() / ".bootcamp" / "handin" / github
    if not (work / ".git").is_dir():
        work.parent.mkdir(parents=True, exist_ok=True)
        if work.exists():
            shutil.rmtree(work)
        cloned = run(["gh", "repo", "clone", fork, str(work), "--", "--depth=1"])
        if cloned.code != 0:
            raise HandInError(f"could not clone your fork {fork}:\n{cloned.out}")
    else:
        run(["git", "fetch", "origin"], work)

    # Start from the fork's default branch every time, so a stale fork does not
    # carry an old submission into this pull request. The name is ASKED FOR: a
    # fork made before a rename can sit on `master`, or on the cohort-dated
    # branch, and hard-coding `main` turns that into "pathspec did not match".
    head = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], work)
    default = head.out.strip() if head.code == 0 and "/" in head.out else "origin/main"
    started = run(["git", "checkout", "-B", branch, default], work)
    if started.code != 0:
        raise HandInError(f"could not start a branch from {default} in your fork:\n{started.out}")

    # UNDER `submissions/`, WHICH IS NOT A DETAIL. The submissions repository
    # triggers CI on `paths: ["submissions/**"]` and its collector globs
    # `submissions/*/*/submission.json`. A bundle one level up gets no checks
    # at all, so the collector correctly refuses to merge it and the pull
    # request sits open for ever, looking like a stuck scheduler.
    destination = work / "submissions" / github / item_id
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(bundle, destination)

    run(["git", "add", f"submissions/{github}/{item_id}"], work)
    committed = run(["git", "commit", "-m", f"{item_id} — {github}"], work)
    if committed.code != 0 and "nothing to commit" not in committed.out.lower():
        raise HandInError(f"could not commit your submission:\n{committed.out}")

    pushed = run(["git", "push", "--force-with-lease", "origin", branch], work)
    if pushed.code != 0:
        raise HandInError(f"could not push to your fork:\n{pushed.out}")

    existing = run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            SUBMISSIONS_REPO,
            "--head",
            f"{github}:{branch}",
            "--state",
            "open",
            "--json",
            "url",
            "--jq",
            ".[0].url",
        ]
    )
    if existing.code == 0 and existing.out.startswith("http"):
        return existing.out.splitlines()[0]

    opened = run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            SUBMISSIONS_REPO,
            "--head",
            f"{github}:{branch}",
            "--title",
            f"{item_id} — {github}",
            "--body",
            f"Submission for `{item_id}`, built by `bootcamp submit`.",
        ]
    )
    if opened.code != 0:
        raise HandInError(f"pushed, but could not open the pull request:\n{opened.out}")
    for line in opened.out.splitlines():
        if line.startswith("http"):
            return line
    return f"https://github.com/{SUBMISSIONS_REPO}/pulls"


__all__ = ["HandInError", "Ran", "push"]
