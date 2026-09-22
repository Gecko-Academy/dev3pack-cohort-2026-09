"""The student's own capstone repository: create it, grade it, trace it.

`bootcamp capstone new` runs in a clone of the course and writes a NEW
repository outside it, from `capstone-template/`: the agent, the contract tests,
the docs skeletons, a CI workflow, and a copy of the six-document corpus. It
pins the course package to the exact commit the clone holds, makes one first
commit, and pushes nothing. Publishing is the student's act, not ours.

`bootcamp capstone grade` and `bootcamp capstone trace` run INSIDE that
repository, from the installed package. They load the student's `agent.py` by
path, so nothing about the course checkout is needed there.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from bootcamp_agent import final_grade
from bootcamp_agent.curriculum import COURSE_REPO, COURSE_URL

TEMPLATE_DIR = "capstone-template"
CORPUS_DIR = Path("data") / "corpus"

#: Never copied out of the template, tracked or not. The template is published
#: publicly and so is every repository made from it: a `.env` left inside
#: `capstone-template/` by somebody testing it must not reach a student's
#: first commit.
_NEVER_COPY = (".env", "score_report.json", "grade.txt", "*.pyc")
_NEVER_COPY_DIRS = {".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".course", ".git"}

_TOKEN = re.compile(r"\{\{([a-z_]+)\}\}")
_FULL_SHA = re.compile(r"[0-9a-f]{40}")
_HEXISH = re.compile(r"[0-9a-f]{4,39}")
_TAG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_GITHUB_NAME = re.compile(r"[A-Za-z0-9._-]+")
#: Branch names move. A pin that moves is not a pin.
_NOT_A_PIN = {"main", "master", "head"}

UNKNOWN_OWNER = "<your-github-username>"


class CapstoneError(Exception):
    """The capstone command refused. Nothing was written. Safe to show as is."""


@dataclass(frozen=True)
class NewCapstone:
    path: Path
    shown_path: str
    repo_name: str
    github_slug: str
    course_ref: str
    committed: bool
    commit_problem: str


# ---------------------------------------------------------------- new


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def resolve_course_ref(course_root: Path) -> str:
    """The newest PUBLISHED course commit this clone holds.

    A student may have committed notebook work in their clone, and those commits
    exist nowhere else, so HEAD would be a pin nobody can install. The merge
    base with `origin/main` is the last commit they share with the cohort
    repository. Only a clone of that repository can answer; anything else is
    asked for the commit instead of guessed at.
    """
    origin = _git(["remote", "get-url", "origin"], course_root)
    url = origin.stdout.strip()
    if origin.returncode != 0 or COURSE_REPO.lower() not in url.lower():
        raise CapstoneError(
            f"this checkout is not a clone of {COURSE_REPO}, so it cannot say which "
            "published commit to pin.\n"
            "    Pass it: --course-ref <the full 40-character commit of the cohort repository>"
        )
    for args in (["merge-base", "HEAD", "origin/main"], ["rev-parse", "HEAD"]):
        found = _git(args, course_root)
        if found.returncode == 0 and _FULL_SHA.fullmatch(found.stdout.strip()):
            return found.stdout.strip()
    raise CapstoneError(
        "could not read the course commit from this clone; pass --course-ref <commit>"
    )


def check_course_ref(ref: str) -> str:
    """A commit or a tag. Never a branch, and never an abbreviated commit."""
    ref = ref.strip()
    if _FULL_SHA.fullmatch(ref):
        return ref
    if _HEXISH.fullmatch(ref):
        raise CapstoneError(
            f"--course-ref {ref!r} looks like an abbreviated commit. Use all 40 characters: "
            "CI checks the course out by it, and a short one is refused there."
        )
    if ref.lower() in _NOT_A_PIN or not _TAG.fullmatch(ref):
        raise CapstoneError(
            f"--course-ref {ref!r} is not a pin. Give a full commit or a tag, never a branch."
        )
    return ref


def _names(folder: Path, github: str | None) -> tuple[str, str]:
    """(repository name, owner/name slug) from --github, or from the folder."""
    if github is None:
        owner, name = None, folder.name
    else:
        owner, _, name = github.strip().rpartition("/")
        owner = owner or None
    for part in (owner, name):
        if part is not None and not _GITHUB_NAME.fullmatch(part):
            raise CapstoneError(
                f"{github or folder.name!r} is not a GitHub repository name: use letters, "
                "digits, '.', '-' and '_' (and one '/' after an owner)"
            )
    return name, f"{owner or UNKNOWN_OWNER}/{name}"


def _package_name(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return normalized or "capstone"


def _badge_line(slug: str, repo_name: str) -> str:
    if slug.startswith(UNKNOWN_OWNER):
        return (
            "<!-- add the CI badge once the repository exists:\n"
            f"![check](https://github.com/{UNKNOWN_OWNER}/{repo_name}/actions/workflows/"
            "check.yml/badge.svg) -->"
        )
    return f"![check](https://github.com/{slug}/actions/workflows/check.yml/badge.svg)"


def _template_files(course_root: Path) -> list[Path]:
    """The template's files, relative to it: what git tracks, when it can say."""
    template = course_root / TEMPLATE_DIR
    listed = _git(["ls-files", "-z", "--", TEMPLATE_DIR], course_root)
    if listed.returncode == 0 and listed.stdout:
        candidates = [
            Path(entry).relative_to(TEMPLATE_DIR) for entry in listed.stdout.split("\0") if entry
        ]
    else:
        candidates = [path.relative_to(template) for path in template.rglob("*") if path.is_file()]
    return sorted(
        relative
        for relative in candidates
        if (template / relative).is_file()
        and not any(part in _NEVER_COPY_DIRS for part in relative.parts)
        and not any(fnmatch(relative.name, pattern) for pattern in _NEVER_COPY)
    )


def _fill(text: str, values: dict[str, str], where: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise CapstoneError(f"template {where}: unknown placeholder {match.group(0)}")
        return values[key]

    return _TOKEN.sub(replace, text)


def create(
    folder: Path,
    *,
    course_root: Path,
    github: str | None = None,
    course_ref: str | None = None,
) -> NewCapstone:
    """Write a new capstone repository at `folder` and make its first commit."""
    template = course_root / TEMPLATE_DIR
    corpus = course_root / CORPUS_DIR
    if not template.is_dir() or not corpus.is_dir():
        raise CapstoneError(
            f"no {TEMPLATE_DIR}/ and data/corpus/ here ({course_root}). Run this from your "
            "clone of the course, with its latest week pulled."
        )
    shown = str(folder)
    target = folder.expanduser().resolve()
    if target == course_root.resolve() or target.is_relative_to(course_root.resolve()):
        raise CapstoneError(
            f"{shown} is inside the course clone. Your capstone is its own repository, so "
            "it lives beside the course, not in it:\n"
            f"    uv run bootcamp capstone new ../{folder.name}"
        )
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise CapstoneError(f"{shown} already exists and is not empty; nothing was overwritten")
    if shutil.which("git") is None:
        raise CapstoneError("git is not installed; install it, then run this again")
    repo_name, slug = _names(target, github)
    ref = check_course_ref(course_ref) if course_ref else resolve_course_ref(course_root)
    files = _template_files(course_root)

    values = {
        "capstone_name": target.name,
        "package_name": _package_name(target.name),
        "repo_name": repo_name,
        "github_slug": slug,
        "badge_line": _badge_line(slug, repo_name),
        "course_repo": COURSE_REPO,
        "course_url": COURSE_URL,
        "course_ref": ref,
    }
    rendered = {
        relative: _fill((template / relative).read_text(encoding="utf-8"), values, relative)
        for relative in files
    }

    # Everything is rendered before anything is written, so a bad template
    # refuses with an empty folder rather than half a repository.
    target.mkdir(parents=True, exist_ok=True)
    for relative, text in rendered.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
    shutil.copytree(corpus, target / CORPUS_DIR, ignore=shutil.ignore_patterns(".*"))

    committed, problem = _first_commit(target, target.name, ref)
    return NewCapstone(
        path=target,
        shown_path=shown,
        repo_name=repo_name,
        github_slug=slug,
        course_ref=ref,
        committed=committed,
        commit_problem=problem,
    )


def _first_commit(target: Path, name: str, ref: str) -> tuple[bool, str]:
    """`git init -b main` and one commit. Never a remote, never a push."""
    init = _git(["init", "-b", "main"], target)
    if init.returncode != 0:
        return False, init.stderr.strip() or "git init failed"
    _git(["add", "-A"], target)
    message = f"Start {name} from the Dev3Pack capstone template\n\nCourse package pinned to {ref}."
    commit = _git(["commit", "-m", message], target)
    if commit.returncode != 0:
        said = (commit.stderr or commit.stdout).strip().splitlines()
        return False, said[-1] if said else "git commit failed"
    return True, ""


def next_steps(made: NewCapstone) -> str:
    lines = [
        f"Created {made.shown_path}: your capstone repository.",
        f"The course package is pinned to {made.course_ref} of {COURSE_REPO}.",
    ]
    if made.committed:
        lines.append("One commit on main. Nothing was pushed.")
    else:
        lines += [
            "",
            f"The files are written, but git could not commit them: {made.commit_problem}",
            "If git asked who you are, tell it once (use your own name and the email on your",
            "GitHub account), then commit:",
            '    git config --global user.name "Your Name"',
            '    git config --global user.email "<the email on your GitHub account>"',
            f"    cd {made.shown_path} && git add -A && git commit -m 'Start my capstone'",
        ]
    lines += [
        "",
        "Next, inside it:",
        f"    cd {made.shown_path}",
        "    uv sync",
        "    uv run pytest                    # the contract: passes, and xfails you earn later",
        "    uv run bootcamp capstone grade   # the practice score, on the offline fake model",
        "",
        "Publish it. It is public on purpose: it is your showcase.",
        "With the GitHub CLI (https://cli.github.com, then: gh auth login):",
        f"    gh repo create {made.repo_name} --public --source . --push",
        "Or in the browser: create an EMPTY public repository named "
        f"{made.repo_name} at https://github.com/new",
        "(no README, no licence, no .gitignore), then:",
        f"    git remote add origin https://github.com/{made.github_slug}.git",
        "    git push -u origin main",
        "",
        "Never commit .env. It is in .gitignore already; keep it there.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- grade and trace


def load_student_agent(repo: Path, spec: str) -> tuple[type, Path]:
    path, class_name = final_grade.parse_agent_spec(spec)
    if not path.is_absolute():
        path = repo / path
    try:
        return final_grade.load_agent_class(path, class_name), path.resolve()
    except final_grade.AgentLoadError as error:
        raise CapstoneError(
            f"{error}. Run this inside your capstone repository, or pass --agent FILE[:CLASS]."
        ) from error


def grade_repo(
    repo: Path,
    *,
    agent_spec: str = "agent.py",
    name: str = "",
    random_count: int = 0,
    seed: int | None = None,
) -> tuple[dict, list[str]]:
    """Grade the repository's agent on the practice set: the report, and the lines to print."""
    agent_class, agent_path = load_student_agent(repo, agent_spec)
    entries = final_grade.load_questions(final_grade.PRACTICE_QUESTIONS)
    lines: list[str] = []
    if random_count:
        entries = final_grade.sample(entries, random_count, seed)
        lines.append(f"practising on {len(entries)} of the set, sampled by category\n")
    results = final_grade.grade(agent_class(), entries)
    lock = repo / "uv.lock"
    report = final_grade.assemble_report(
        name=name,
        mode="practice",
        question_set_id="public-practice-v2",
        question_sha256=final_grade.sha256_file(final_grade.PRACTICE_QUESTIONS),
        results=results,
        grader_source_sha256=final_grade.sha256_file(Path(final_grade.__file__)),
        artifacts={
            "agent_tree_sha256": final_grade.tree_hash([agent_path, repo / CORPUS_DIR], repo),
            # Outside the course there is no generated course contract to hash;
            # the pinned package in uv.lock stands for it.
            "course_contract_sha256": None,
            "dependencies_lock_sha256": final_grade.sha256_file(lock) if lock.is_file() else None,
        },
    )
    return report, lines + final_grade.format_results(results, report)


def trace_lines(repo: Path, question: str, *, agent_spec: str = "agent.py") -> list[str]:
    """Run one question through the repository's agent and show every step it took."""
    agent_class, _ = load_student_agent(repo, agent_spec)
    agent = agent_class()
    run = getattr(agent, "run", None)
    if not callable(run):
        raise CapstoneError(
            f"{agent_class.__name__} has no run(question) method, so its trace cannot be "
            "read. The template's agent.py has one: it returns the whole AgentResult, and "
            "__call__ returns only its answer."
        )
    result = run(question)
    trace = getattr(result, "trace", None)
    answer = getattr(result, "answer", None)
    if trace is None or answer is None:
        raise CapstoneError("run(question) must return the AgentResult (answer and trace)")
    lines = [f"[{event.kind}] {event.detail}" for event in trace]
    lines += [
        "",
        f"answer: {answer.answer}",
        f"citations: {list(answer.citations)}",
        f"confidence: {answer.confidence}",
        f"needs_human_review: {answer.needs_human_review}",
    ]
    return lines
