"""`bootcamp capstone submit`: the final assignment, answered and handed in.

Runs INSIDE the student's capstone repository. In order:

1. The repository must be clean and pushed, because the bundle links to one
   commit on GitHub, and that link must show the code that produced the answers.
2. The practice grader runs first, locally, the way `capstone grade` does. The
   student sees a score and the model behind it before anything leaves.
3. The final questions come from the course app. They carry no answer keys.
4. The agent answers each one under a per-question timeout and a total budget.
   An agent that raises, hangs or returns the wrong shape gets a flagged
   refusal for that question, never a crash of the whole run.
5. `submissions/<github>/final/` gets exactly `answers.json` and
   `submission.json`, and the pull request is opened the way homework `submit`
   opens one (`handin.push`), or the browser route is printed.

The score is NOT computed here. The answer keys never leave the app; the
submissions repository scores the bundle after the pull request merges.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from bootcamp_agent import final_grade, final_run, handin, questions_api
from bootcamp_agent.capstone_repo import CapstoneError, grade_repo, load_student_agent
from bootcamp_agent.config import Settings
from bootcamp_agent.final_run import FinalRun
from bootcamp_agent.submit_checks import (
    RepoState,
    SubmitError,
    check_repo,
    course_release,
    installed_course_commit,
)

COHORT = "2026-09"
ITEM_ID = "final"
SUBMIT_COMMAND = "bootcamp capstone submit"

_GITHUB_LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")

Say = Callable[[str], None]


# ---------------------------------------------------------------- the model and the practice run


def model_label(settings: Settings) -> str:
    if settings.provider == "fake":
        return "fake (the offline FakeLLM)"
    return f"{settings.provider}:{settings.model}" if settings.model else settings.provider


def practice_lines(repo: Path, agent_spec: str, settings: Settings) -> list[str]:
    """The practice score and the model, labelled as practice: what `capstone grade` says."""
    report, _ = grade_repo(repo, agent_spec=agent_spec)
    score = report["score"]
    verdict = "PASSED" if report["passed"] else "NOT YET"
    lines = [
        f"practice score: {score['passed']}/{score['total']} ({score['percent']}%), {verdict}",
        f"model: {model_label(settings)}",
    ]
    if not report["gates"]["critical_safety"]:
        lines.append("critical safety gate failed on the practice set")
    lines.append("practice only: the final score is computed after your pull request merges")
    if settings.provider == "fake":
        lines += [
            "",
            "WARNING: this run uses the fake model. The fake answers nothing: it only refuses.",
            "Your private score will be about the fake's, 30%, with the critical gate failed.",
            "Set BOOTCAMP_PROVIDER and your key in .env to submit your agent's real answers.",
        ]
    return lines


# ---------------------------------------------------------------- the bundle


def answers_payload(
    run: FinalRun, *, course_release: str, question_set_id: str
) -> dict[str, object]:
    return {
        "cohort": COHORT,
        "course_release": course_release,
        "question_set_id": question_set_id,
        "answers": {
            task_id: {
                "answer": answer.answer,
                "citations": list(answer.citations),
                "confidence": float(answer.confidence),
                "needs_human_review": answer.needs_human_review,
            }
            for task_id, answer in run.answers.items()
        },
    }


def agent_label(repo: Path, spec: str) -> str:
    """`agent.py:YourAgent`: the file relative to the repository, and the class."""
    path, class_name = final_grade.parse_agent_spec(spec)
    resolved = (path if path.is_absolute() else repo / path).resolve()
    try:
        shown = resolved.relative_to(repo.resolve()).as_posix()
    except ValueError as error:
        raise SubmitError(
            f"the agent {spec} is outside this repository, so the link could not show it"
        ) from error
    return f"{shown}:{class_name}"


def submission_payload(
    *, github: str, state: RepoState, agent: str, now: datetime
) -> dict[str, object]:
    return {
        "kind": ITEM_ID,
        "github": github,
        "repo": state.url,
        "commit": state.commit,
        "agent": agent,
        "submitted_at": now.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_bundle(root: Path, github: str, answers: dict, submission: dict) -> Path:
    """`<root>/<github>/final/` holding exactly the two files."""
    where = root / github / ITEM_ID
    if where.exists():
        shutil.rmtree(where)
    where.mkdir(parents=True)
    for name, payload in (("answers.json", answers), ("submission.json", submission)):
        (where / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return where


def check_github(github: str) -> str:
    github = github.strip()
    if not _GITHUB_LOGIN.fullmatch(github):
        raise SubmitError(f"--github {github!r} is not a GitHub username")
    return github


NEXT_STEPS = (
    "What happens next:",
    "  - The pull request merges itself once its check passes.",
    "  - Your real score arrives a few minutes later, in finals/{github}/result.json",
    "    in the submissions repository.",
    "  - Submit as often as you like. The leaderboard shows your best score.",
    "  - The certificate unlocks above 30% with every critical question passed.",
)


def next_steps(github: str) -> str:
    return "\n".join(line.format(github=github) for line in NEXT_STEPS)


def default_root() -> Path:
    # Outside the student's repository: a bundle written inside it would make
    # the next submission refuse as "changes not committed".
    return Path.home() / ".bootcamp" / "final"


def dry_run_root() -> Path:
    return Path(tempfile.mkdtemp(prefix="capstone-final-"))


def load_agent(repo: Path, spec: str) -> Callable[[str], object]:
    try:
        agent_class, _ = load_student_agent(repo, spec)
    except CapstoneError as error:
        raise SubmitError(str(error)) from error
    try:
        return agent_class()
    except Exception as error:  # noqa: BLE001 - a constructor that raises has no answers to give
        raise SubmitError(
            f"{agent_class.__name__}() raised {type(error).__name__}: {error}. "
            "Run `uv run bootcamp capstone grade` to see it fail the same way."
        ) from error


# ---------------------------------------------------------------- the whole command


@dataclass(frozen=True)
class Submitted:
    bundle: Path
    pr_url: str | None
    flagged: dict[str, str]


def submit(
    repo: Path,
    *,
    github: str,
    api_base: str | None,
    settings: Settings,
    agent_spec: str = "agent.py",
    dry_run: bool = False,
    into: Path | None = None,
    question_timeout_s: float = final_run.DEFAULT_QUESTION_TIMEOUT_S,
    budget_s: float = final_run.DEFAULT_BUDGET_S,
    transport: questions_api.Transport | None = None,
    git_run: object = handin._run,
    installed_commit: Callable[[], str | None] = installed_course_commit,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    say: Say = print,
) -> Submitted:
    """Check, practise, answer, bundle, hand in. Raises SubmitError or QuestionsError.

    Every check that needs no model and no network runs before the ones that
    do, so a refusal costs the student seconds rather than a practice run.
    """
    github = check_github(github)
    if not api_base:
        raise SubmitError(
            f"no API address. Pass --api <address>, or set {questions_api.API_ENV}. "
            "The address is in the course announcement."
        )
    api_base = questions_api.check_api_base(api_base)
    state = check_repo(repo)
    release = course_release(repo, installed_commit())
    agent_name = agent_label(repo, agent_spec)
    say(f"repository: {state.url} at {state.commit[:12]}")
    say(f"course package: {release[:12]}\n")

    say("1/3  the practice set, locally (nothing leaves this machine)")
    try:
        for line in practice_lines(repo, agent_spec, settings):
            say(f"     {line}" if line else "")
    except CapstoneError as error:
        raise SubmitError(str(error)) from error

    say("\n2/3  the final questions")
    questions = questions_api.fetch_questions(
        api_base, "final", transport=transport or questions_api.urllib_transport
    )
    say(f"     {len(questions.questions)} questions, set {questions.question_set_id}")
    run = final_run.answer_all(
        load_agent(repo, agent_spec),
        questions.questions,
        question_timeout_s=question_timeout_s,
        budget_s=budget_s,
        say=lambda line: say(f"     {line}"),
    )
    try:
        final_run.check_caps(run.answers)
    except final_run.CapError as error:
        raise SubmitError(str(error)) from error

    answers = answers_payload(
        run, course_release=release, question_set_id=questions.question_set_id
    )
    submission = submission_payload(github=github, state=state, agent=agent_name, now=now())
    root = dry_run_root() if dry_run else (into or default_root())
    where = write_bundle(root, github, answers, submission)
    say(f"\n3/3  the bundle: {where}")
    if run.flagged:
        say(f"     {len(run.flagged)} question(s) became flagged refusals, listed above")

    if dry_run:
        for name in ("answers.json", "submission.json"):
            say(f"\n--- {name}")
            say((where / name).read_text(encoding="utf-8").rstrip())
        say("\ndry run: no pull request was opened.")
        return Submitted(where, None, run.flagged)

    try:
        url = handin.push(where, github, ITEM_ID, run=git_run, command=SUBMIT_COMMAND)
    except handin.HandInError as error:
        say(f"\n{error}")
        say(f"\nYour bundle is still at {where}.")
        say(
            handin.manual_route(
                github,
                ITEM_ID,
                where,
                files=("answers.json", "submission.json"),
                command=f"uv run {SUBMIT_COMMAND} --github {github}",
            )
        )
        say("\n" + next_steps(github))
        return Submitted(where, None, run.flagged)
    say(f"\nhanded in: {url}\n")
    say(next_steps(github))
    return Submitted(where, url, run.flagged)
