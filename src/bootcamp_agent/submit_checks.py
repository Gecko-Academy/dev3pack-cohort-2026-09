"""What `capstone submit` checks before anything runs: the repository and the pin.

The bundle names two commits: the student's (the code that answered) and the
course package's (the code it ran on). Both must be ones anybody can open, so
the repository must be clean, pushed to GitHub, and pinned to a course commit.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

COURSE_PACKAGE = "dev3pack-bootcamp-ai-engineering"

#: The course's GitHub organisation. A student's capstone never lives under it: the
#: capstone template is cloned from here, and "make it yours" moves `origin` away.
COURSE_ORG = "gecko-academy"

_FULL_SHA = re.compile(r"[0-9a-f]{40}")
_GITHUB_REMOTE = re.compile(
    r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"(?P<owner>[A-Za-z0-9._-]+)/(?P<name>[A-Za-z0-9._-]+?)(?:\.git)?/?$"
)


class SubmitError(Exception):
    """The submission refused. Nothing was handed in. Safe to show as is."""


# ---------------------------------------------------------------- the repository


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


def github_https(url: str) -> str | None:
    """`https://github.com/<owner>/<name>` for a GitHub remote, else None."""
    found = _GITHUB_REMOTE.match(url.strip())
    if found is None:
        return None
    return f"https://github.com/{found.group('owner')}/{found.group('name')}"


@dataclass(frozen=True)
class RepoState:
    url: str
    commit: str


#: What each kind of hand-in calls its repository, and how a student makes one
#: theirs. The checks are the same; only the words a refusal uses differ.
_REPO_WORDS = {
    "final": {
        "missing": (
            "this is not a final assignment repository with a commit in it. Run this "
            "inside the folder `uv run bootcamp final new` made (for example "
            "../my-final-assignment), after your first commit."
        ),
        "make_it_yours": (
            "    git remote rename origin upstream\n"
            "    gh repo create my-final-assignment --public --source . --remote origin --push\n"
            "The final assignment starts in its own repository: from the course folder,\n"
            "    uv run bootcamp final new ../my-final-assignment"
        ),
    },
    "gecko": {
        "missing": (
            "this is not your Gecko capstone repository with a commit in it. Pass the "
            "folder you cloned the capstone template into, for example "
            "--repo ../my-gecko-buyer, after your first commit."
        ),
        "make_it_yours": (
            "    git remote rename origin upstream\n"
            "    gh repo create my-gecko-buyer --public --source . --remote origin --push"
        ),
    },
}


def check_repo(repo: Path, kind: str = "final") -> RepoState:
    """The public link and the commit, or a refusal that says what to run."""
    words = _REPO_WORDS[kind]
    head = _git(repo, "rev-parse", "--verify", "HEAD")
    if head.returncode != 0 or not _FULL_SHA.fullmatch(head.stdout.strip()):
        raise SubmitError(words["missing"])
    commit = head.stdout.strip()
    status = _git(repo, "status", "--porcelain")
    if status.returncode != 0 or status.stdout.strip():
        changed = status.stdout.strip().splitlines()[:5]
        raise SubmitError(
            "your repository has changes that are not committed:\n"
            + "\n".join(f"    {line}" for line in changed)
            + "\nThe submission links to your code on GitHub, so it must be the code that "
            "answers. Commit and push first:\n"
            '    git add -A && git commit -m "final submission" && git push'
        )
    origin = _git(repo, "remote", "get-url", "origin")
    if origin.returncode != 0 or not origin.stdout.strip():
        raise SubmitError(
            "your repository has no `origin` on GitHub yet. Publish it first:\n"
            "    gh repo create <name> --public --source . --push\n"
            "or, after creating an empty public repository in the browser:\n"
            "    git remote add origin https://github.com/<you>/<name>.git\n"
            "    git push -u origin main"
        )
    url = github_https(origin.stdout)
    if url is None:
        raise SubmitError(
            f"`origin` is {origin.stdout.strip()}, which is not a GitHub repository. The "
            "submission links to your code on GitHub. Point origin there:\n"
            "    git remote set-url origin https://github.com/<you>/<name>.git\n"
            "    git push -u origin main"
        )
    # A clone of the capstone template that skipped "make it yours" passes every
    # other check: clean, pushed (the template's own commits are on its origin), a
    # GitHub URL. It would hand in a link to the course's code instead of theirs.
    if url.split("/")[3].lower() == COURSE_ORG:
        raise SubmitError(
            f"`origin` is a course repository ({url}), not yours. The submission "
            "links to your code. Make it yours first:\n" + words["make_it_yours"]
        )
    pushed = _git(
        repo, "for-each-ref", "--contains", commit, "--format=%(refname)", "refs/remotes/origin"
    )
    if pushed.returncode != 0 or not pushed.stdout.strip():
        raise SubmitError(
            f"your last commit ({commit[:12]}) is not on GitHub yet, so the link would show "
            "other code than the code that answers. Push it:\n"
            "    git push\n"
            "If you pushed from another machine, run `git fetch` here first."
        )
    return RepoState(url=url, commit=commit)


def _locked_commit(lock: Path) -> str | None:
    """The course package's commit in `uv.lock`: `source = { git = "...#<sha>" }`."""
    if not lock.is_file():
        return None
    for block in lock.read_text(encoding="utf-8").split("[[package]]"):
        if re.search(rf'^name = "{re.escape(COURSE_PACKAGE)}"$', block, re.MULTILINE):
            found = re.search(r'source = \{ git = "[^"#]*#([0-9a-f]{40})"', block)
            if found:
                return found.group(1)
    return None


def _pinned_commit(pyproject: Path) -> str | None:
    """The commit in the pin `capstone new` writes: `<package> @ git+<url>@<ref>`."""
    if not pyproject.is_file():
        return None
    found = re.search(
        rf'"{re.escape(COURSE_PACKAGE)} @ git\+[^"@]+@([0-9a-f]{{40}})"',
        pyproject.read_text(encoding="utf-8"),
    )
    return found.group(1) if found else None


def installed_course_commit() -> str | None:
    """The commit pip/uv recorded when it installed the package from git, if it did."""
    try:
        raw = metadata.distribution(COURSE_PACKAGE).read_text("direct_url.json")
    except metadata.PackageNotFoundError:
        return None
    if not raw:
        return None
    try:
        commit = json.loads(raw).get("vcs_info", {}).get("commit_id")
    except (json.JSONDecodeError, AttributeError):
        return None
    return commit if isinstance(commit, str) and _FULL_SHA.fullmatch(commit) else None


def course_release(repo: Path, installed: str | None = None) -> str:
    """The 40-hex commit of the course package the agent runs on.

    `uv.lock` first: `capstone new` may pin a tag, and only the lock knows the
    commit a tag resolved to. Then the pin in `pyproject.toml`, when it is a
    commit. If the package installed in this environment came from git too, it
    must be the same commit, or the bundle would name code that did not run.
    """
    release = _locked_commit(repo / "uv.lock") or _pinned_commit(repo / "pyproject.toml")
    if release is None:
        raise SubmitError(
            "could not read which course commit this repository runs on: no "
            f"{COURSE_PACKAGE} commit in uv.lock or pyproject.toml. Run `uv lock`, commit "
            "uv.lock, push, and try again."
        )
    if installed and installed != release:
        raise SubmitError(
            f"uv.lock pins the course at {release[:12]}, but {installed[:12]} is installed. "
            "Run `uv sync`, then try again."
        )
    return release
