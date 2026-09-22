"""Thin CLI over the package. Parse args, call the package, format output.

If logic starts creeping in here, it belongs in the package instead.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from collections.abc import Iterator
from pathlib import Path

from bootcamp_agent.agent import answer_question
from bootcamp_agent.config import ConfigError, load_settings
from bootcamp_agent.documents import CorpusError, load_corpus
from bootcamp_agent.evals import EvalError, format_report, load_cases, run_evals
from bootcamp_agent.llm import get_client

ROOT = Path(__file__).resolve().parent.parent.parent

#: The same marks the doctor and the notebook preflight use, so one learner
#: reading three outputs sees one vocabulary.
OK = "✅"
FAIL = "❌"
CORPUS_DIR = ROOT / "data" / "corpus"
GOLDEN_PATH = ROOT / "data" / "evals" / "golden.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bootcamp-agent",
        description="Source-grounded developer research assistant (bootcamp capstone).",
    )
    parser.add_argument("question", nargs="?", help="Question to answer from the corpus")
    parser.add_argument("--trace", action="store_true", help="Print the agent trace")
    parser.add_argument("--eval", action="store_true", help="Run the golden evaluation set")
    args = parser.parse_args(argv)

    try:
        settings = load_settings()
        client = get_client(settings)
        documents = load_corpus(CORPUS_DIR)
    except (ConfigError, CorpusError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.eval:
        try:
            report = run_evals(load_cases(GOLDEN_PATH), documents, client)
        except EvalError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        print(format_report(report))
        return 0 if report.pass_rate == 1.0 else 1

    if not args.question:
        parser.print_help()
        return 2

    result = answer_question(args.question, documents, client)
    if args.trace:
        for event in result.trace:
            print(f"[{event.kind}] {event.detail}")
        print()
    answer = result.answer
    print(f"answer: {answer.answer}")
    print(f"citations: {list(answer.citations)}")
    print(f"confidence: {answer.confidence}")
    print(f"needs_human_review: {answer.needs_human_review}")
    return 0


def _doctor() -> int:
    """Delegate to the setup doctor. One implementation, two entry points."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from check_setup import main as check_setup_main

    return check_setup_main()


def _start() -> int:
    """From a fresh clone to a green doctor, in one command.

    WHY THIS EXISTS. On day one, 26 learners forked the submissions repository
    and 2 opened a pull request. Several reported `bootcamp: command not found`,
    which is what you get for running a command from the wrong directory or
    without `uv run` -- and the doctor, the thing that would have told them,
    could not run until the install it was diagnosing had already worked.

    So this does the install, then the diagnosis, then says the ONE next thing.
    It is safe to run twice: every step checks before it acts.
    """
    import shutil
    import subprocess

    print("\nSetting up the course. This is safe to run as many times as you like.\n")

    if not (ROOT / "pyproject.toml").is_file():
        print(f"{FAIL} this is not the course folder: {Path.cwd()}", file=sys.stderr)
        print(
            "\n   Run it from inside the clone:\n"
            "     cd dev3pack-cohort-2026-09\n"
            "     uv run bootcamp start",
            file=sys.stderr,
        )
        return 2
    print(f"{OK} in the course folder")

    if shutil.which("uv") is None:
        print(f"{FAIL} uv is not installed", file=sys.stderr)
        print(
            "\n   macOS / Linux:  curl -LsSf https://astral.sh/uv/install.sh | sh\n"
            '   Windows:        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"\n'
            "\n   Then close this terminal, open a new one, and run this again.",
            file=sys.stderr,
        )
        return 2
    print(f"{OK} uv is installed")

    try:
        import bootcamp_agent  # noqa: F401
    except ImportError:
        print("·  installing the course (about a minute the first time)…")
        result = subprocess.run(["uv", "sync", "--group", "dev"], cwd=ROOT)
        if result.returncode != 0:
            print(f"\n{FAIL} `uv sync --group dev` failed, above.", file=sys.stderr)
            return 1
    print(f"{OK} the course is installed")

    env, example = ROOT / ".env", ROOT / ".env.example"
    if not env.exists() and example.is_file():
        shutil.copyfile(example, env)
        print(f"{OK} wrote .env (the offline lane; no key needed)")

    print("\nChecking it works:\n")
    failures = _doctor()

    if failures:
        print("\nFix the ❌ lines above, then run this again.")
        return 1

    print("\nYou are ready. Next:\n\n    uv run jupyter lab\n\nthen open 00-START-HERE.ipynb.\n")
    return 0


def _check(item_id: str) -> int:
    """Run one item's notebook and print its scorecard.

    Any submittable item, not only a session: a week-0 unit and the capstone
    have notebooks and checks too, and a learner who can submit them should be
    able to run them the same way.
    """
    from bootcamp_agent import submission
    from bootcamp_agent.coursework import CourseworkError, render, run_notebook, stored_scorecard
    from bootcamp_agent.curriculum import UnknownChapter

    try:
        item = submission.resolve(item_id)
    except (UnknownChapter, submission.SubmissionError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if not item.verifiable:
        # NOT RE-RUNNING IS NOT THE SAME AS HAVING NOTHING TO SAY. This used to
        # stop here and send the learner to Jupyter, which was defensible while
        # sessions 1 and 10 carried no marks. They carry marks now, and the marks
        # rest on exactly the outputs sitting in this file -- so a learner who
        # asks "did it pass?" must be able to get the answer from the same
        # command as everybody else, rather than by submitting to find out.
        #
        # `submit` has always read the file this way. This is the same read.
        print(f"{item.id}: {item.note}")
        print("Nothing can replay it, so this reads the outputs you saved.\n")
        try:
            card = stored_scorecard(item.notebook, item.id, item.exercises)
        except CourseworkError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        print(render(card))
        if not card.passed and not card.failed:
            print("\nThat is what the saved file says, which is nothing yet.")
            print("Open it in Jupyter, run every cell, SAVE, then check again.")
        return 0 if not card.failed and not card.not_reached else 1
    print(f"running {item.id} ({item.title})…")
    try:
        card = run_notebook(item.notebook, item.exercises, item.id)
    except CourseworkError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(render(card))
    return 0 if not card.failed and not card.not_reached else 1


def _export(destination: Path | None) -> int:
    """Write this machine's progress to a file the learner can read and send.

    The week-0 page promises exactly this, and the promise is load-bearing: the
    course tells learners their progress database never leaves their machine,
    and offers this as the way to share it if they WANT to. An escape hatch that
    does not exist makes the paragraph around it a lie.

    Outcomes only, which is all the store holds: which exercises passed, how
    many attempts, and whether help was taken. Never what was typed.
    """
    import json

    from bootcamp_agent.hints import FULL_MARKS, all_attempts, store_path

    attempts = all_attempts()
    payload = {
        "schema": "dev3pack.progress.v1",
        "source": str(store_path()),
        "note": "Outcomes only. This file records no answers, no name, and no email.",
        "exercises": [
            {
                "exercise": entry.exercise,
                "passed": entry.passed,
                "attempts": entry.attempts,
                "hinted": entry.hinted,
                "revealed": entry.revealed,
                "score": entry.score,
                "out_of": FULL_MARKS,
            }
            for entry in sorted(attempts, key=lambda a: a.exercise)
        ],
    }
    text = json.dumps(payload, indent=2) + "\n"
    if destination is None:
        print(text, end="")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    print(f"wrote {destination} — {len(attempts)} exercise(s), outcomes only")
    print("Read it before you send it anywhere. Nothing here is sent for you.")
    return 0


def _progress() -> int:
    """Run everything that can be run, and tally it in course order.

    Week 0 and the capstone are here beside the sessions, because a learner who
    did week 0 and asks "where am I" is asking about all of it. They are marked
    for what they are: week 0 runs and is never marked, the capstone is scored,
    and an assistant-driven session cannot be run here at all.
    """
    from bootcamp_agent import submission
    from bootcamp_agent.coursework import (
        CourseworkError,
        run_notebook,
    )
    from bootcamp_agent.curriculum import CAPSTONE, CHAPTERS, WEEK0_UNITS

    rows: list[tuple[str, str, str | None]] = []
    for unit in WEEK0_UNITS:
        rows.append((unit.prefix, _titled(unit.title), "week 0"))
    for chapter in CHAPTERS:
        rows.append((chapter.chapter_id, _titled(chapter.title), chapter.weekday))
    rows.append((CAPSTONE.prefix, _titled(CAPSTONE.title), "project"))

    worst = 0
    for item_id, title, when in rows:
        label = f"{item_id:<6} {when or '':<10} {title}"
        try:
            item = submission.resolve(item_id)
        except submission.SubmissionError:
            print(f"{label} demo day")
            continue
        # ARRIVAL IS ASKED FIRST. "In Jupyter" is advice about how to run a
        # session, and it is wrong before that session exists: `ch10 … in
        # Jupyter` invited a student to open a file their clone did not have,
        # while every other unpublished session correctly said when it arrives.
        pending = _arrival(item.notebook, when)
        if pending is not None:
            print(f"{label} {pending}")
            continue
        if not item.verifiable:
            print(f"{label} in Jupyter")
            continue
        try:
            with _quiet_children():
                card = run_notebook(item.notebook, item.exercises, item.id)
        except CourseworkError as error:
            print(f"{label} error: {str(error)[:40]}")
            worst = 1
            continue
        tally = f"{len(card.passed)}/{card.total}"
        print(f"{label} {tally}{'' if item.scored else '  (not marked)'}")
        if card.failed or card.not_reached:
            worst = 1
    return worst


#: Wide enough for the longest session title, minus an ellipsis. A title cut
#: mid-word ran straight into the status — "…the repository i in Jupyter" reads
#: as one broken sentence rather than a title and a state.
_TITLE = 44


def _titled(title: str) -> str:
    """A title padded to a fixed width, and visibly cut when it does not fit."""
    shown = title if len(title) <= _TITLE else title[: _TITLE - 1].rstrip() + "…"
    return f"{shown:<{_TITLE}}"


@contextlib.contextmanager
def _quiet_children() -> Iterator[None]:
    """Swallow what the notebooks' kernels write to the terminal.

    `progress` runs every runnable chapter, and each one starts a kernel that
    announces "Kernel is running over TCP without encryption … susceptible to
    eavesdropping" — true, harmless, and printed about eighteen times above the
    table it is meant to be showing. Unfinished week-0 exercises add their own:
    unit 9 has the learner write `timezone_server.py`, so before they do, the
    cell that launches it prints `can't open file …: No such file or directory`.

    Both are expected output from work that has not been done yet, and neither
    is a fault. Shown to somebody on their first day they read as a broken
    install — which is exactly how a tester read them.

    REDIRECTED AT THE FILE DESCRIPTOR, because the noise comes from child
    processes: `contextlib.redirect_stderr` only moves Python's own `sys.stderr`
    and a subprocess writes past it. `check` deliberately does NOT do this — one
    chapter, being debugged, should show everything.
    """
    saved = os.dup(2)
    try:
        with open(os.devnull, "w") as null:
            os.dup2(null.fileno(), 2)
        yield
    finally:
        os.dup2(saved, 2)
        os.close(saved)


def _arrival(notebook: Path, when: str | None) -> str | None:
    """The line for an item whose files have not been published yet, or None.

    A learner's clone only carries the weeks that have opened, so most session
    directories are simply absent on day one. That is the schedule working, not
    a fault, and it must not be reported as one.

    THE SIGNAL IS THE DIRECTORY, not the notebook. The publisher withholds a
    session whole, so an absent directory means "not yet"; a directory that
    exists without its notebook means a damaged checkout, and that still has to
    be shouted about.
    """
    if notebook.parent.is_dir():
        return None
    # The `when` column is a date for a session and a word for anything else
    # ("project" for the capstone), and only a date can follow "arrives".
    dated = when is not None and any(character.isdigit() for character in when)
    return f"arrives {when}" if dated else "not published yet"


def _no_evidence(item: object) -> str:
    """Why this notebook cannot be handed in yet, or "" when it can.

    A submission is a claim plus the evidence for it, and the evidence lives in
    the saved cell outputs. Handing in a notebook that was never run used to
    print `wrote ...` and exit 0, which is how somebody hands in nothing on day
    one and finds out a week later.
    """
    import nbformat

    from bootcamp_agent.coursework import evidence_of

    notebook = getattr(item, "notebook", None)
    if notebook is None or not notebook.is_file():
        return ""
    found = evidence_of(nbformat.read(notebook, as_version=4))

    if found.never_ran:
        return (
            f"\n{item.id}: this notebook has never been run.\n\n"
            f"  code cells        {found.code_cells}\n"
            f"  cells executed    {found.executed_cells}\n"
            f"  cells with output {found.cells_with_output}\n\n"
            "Nothing was handed in. A submission is a claim plus the evidence for\n"
            "it, and there is no evidence here.\n\n"
            "Do this:\n"
            "  1. Run every cell, top to bottom.\n"
            "  2. Save the notebook.\n"
            "  3. Run this command again."
        )

    if not getattr(item, "verifiable", True) and found.verdict_lines == 0:
        return (
            f"\n{item.id}: nothing in this notebook says an exercise passed.\n\n"
            f"{item.id} is assistant-driven, so nobody re-runs it — the ✅ lines your\n"
            "own notebook printed are the only evidence there is, and this file has\n"
            f"none. Expected lines like:  ✅ {item.id}-e1 passed\n\n"
            f"  cells executed    {found.executed_cells}\n"
            f"  ✅/❌ lines found  {found.verdict_lines}\n\n"
            "Nothing was handed in.\n\n"
            "Most likely you ran the cells but did not SAVE. Press Ctrl+S, then run\n"
            "this again. Or you have not run the check() cells yet — run them, save,\n"
            "then run this again."
        )
    return ""


def _manual_route(github: str, item_id: str, where: Path) -> str:
    """How to hand in without `gh`. The text lives beside `push`, in `handin`.

    The file list is read off the bundle, so a carried `challenge.ipynb` is named
    in the upload steps exactly like the notebook is.
    """
    from bootcamp_agent.handin import manual_route

    files = tuple(sorted(p.name for p in where.iterdir() if p.is_file())) if where.is_dir() else ()
    if files:
        return manual_route(github, item_id, where, files=files)
    return manual_route(github, item_id, where)


def _submit(chapter_id: str, github: str, cohort: str, into: str | None, push: bool = False) -> int:
    """Build the bundle a learner opens a pull request with."""
    from pathlib import Path

    from bootcamp_agent import submission
    from bootcamp_agent.coursework import (
        CourseworkError,
        run_notebook,
        stored_scorecard,
    )

    try:
        item = submission.resolve(chapter_id)
    except (KeyError, submission.SubmissionError) as error:
        print(f"cannot submit that: {error}")
        return 2

    # Before anything is built, run or printed: is there anything to hand in?
    refusal = _no_evidence(item)
    if refusal:
        print(refusal, file=sys.stderr)
        return 3

    if not item.verifiable:
        # Sessions 1 and 10 need an assistant open — they edit its configuration
        # and author a skill. Running them unattended would score zero for work
        # that was genuinely done, so they are handed in as they stand and said
        # to be, rather than a failure being manufactured. The ids come from
        # `manual_reason` in the curriculum, never from a list written here.
        print(f"{item.id} ({item.title}) — {item.note}")
        # "and no marks" was true until sessions 1 and 10 became scored, and then
        # this line went on saying it directly above "score 100/100". A learner
        # reading a tool contradict itself about their own marks has no way to
        # tell which half is the bug.
        print("submitting your notebook as it stands, with no re-run.")
        print("The marks below are read from the outputs you saved.")
        # "As it stands" means what the notebook SAYS. Handing in `None` here
        # filled `not_reached` with every exercise and claimed `ran: false`, so
        # a learner whose notebook plainly showed `✅ ch01-e1 passed` was told it
        # never ran — on day one, having done the work. Read the outputs they
        # left instead; we are declining to RE-run it, not pretending it never ran.
        card = stored_scorecard(item.notebook, item.id, item.exercises)
    else:
        print(f"running {item.id} ({item.title})…")
        try:
            card = run_notebook(item.notebook, item.exercises, item.id)
        except CourseworkError as error:
            print(f"could not run it: {error}")
            return 1

    # ch05/ch10 only: the week's challenge, if it was done (and saved) in its demo.
    from bootcamp_agent.weekly.carry import carry

    carried = carry(item.id, ROOT, item.notebook)
    challenge = carried.carried.raw if carried.carried else None

    try:
        payload = submission.build(item, card, item.notebook, github, cohort, challenge=challenge)
    except submission.SubmissionError as error:
        print(str(error))
        return 2

    root = Path(into) if into else Path.cwd() / "submissions"
    where = submission.write(payload, item.notebook, root / github / item.id, challenge=challenge)
    if carried.message:
        print(carried.message)

    result = payload["result"]
    if item.scored:
        print(f"\n{item.id}: {len(result['passed'])}/{len(item.exercises)} passed")
        print(f"score {result['score']}/{result['max_score']}")
    elif card is not None:
        print(f"\n{item.id}: {len(result['passed'])}/{len(item.exercises)} passed, not marked")
    if result["failed"] or result["not_reached"]:
        print("\nnot finished yet, and you can submit anyway:")
        for exercise in result["failed"]:
            print(f"  ❌ {exercise}")
        for exercise in result["not_reached"]:
            print(f"  ·  {exercise} never ran")
    print(f"\nwrote {where}")

    if not push:
        print(_manual_route(github, item.id, where))
        return 0

    from bootcamp_agent.handin import HandInError
    from bootcamp_agent.handin import push as hand_in

    print("\nhanding it in…")
    try:
        url = hand_in(where, github, item.id)
    except HandInError as error:
        # The bundle is already written, so this is never a dead end: say what
        # failed, and leave the manual route standing.
        print(f"\n{error}", file=sys.stderr)
        print(f"\nYour submission is still at {where}.", file=sys.stderr)
        print(_manual_route(github, item.id, where), file=sys.stderr)
        return 1
    print(f"\n{OK} handed in: {url}")
    print("Green CI means accepted. Merging is automatic — nobody has to be asked.")
    return 0


def _read(port: int, build_only: bool) -> int:
    """Build the course pages and serve them, so they can be read as pages.

    The pages are MDX with `<Question>` blocks in them. Opened as files they show
    the quiz as raw JSX, which is the format's doing rather than ours -- Hugging
    Face's own course reads the same way on GitHub. Rendering them locally is how
    a learner gets the quiz, offline, with nothing to install beyond this repo.
    """
    import subprocess

    script = Path(__file__).resolve().parent.parent.parent / "scripts" / "course_html.py"
    if not script.is_file():
        print("the site generator is not in this checkout", file=sys.stderr)
        return 1
    command = [sys.executable, str(script)]
    if not build_only:
        command += ["--serve", "--port", str(port)]
    try:
        return subprocess.call(command)
    except KeyboardInterrupt:
        return 0


def _capstone_new(folder: str, github: str | None, course_ref: str | None) -> int:
    """Create the student's own capstone repository beside the course clone."""
    from bootcamp_agent.capstone_repo import CapstoneError, create, next_steps

    try:
        made = create(Path(folder), course_root=ROOT, github=github, course_ref=course_ref)
    except CapstoneError as error:
        print(f"{FAIL} {error}", file=sys.stderr)
        return 2
    print(next_steps(made))
    return 0 if made.committed else 1


def _capstone_grade(agent: str, name: str, report: str, count: int, seed: int | None) -> int:
    """The practice grader, run inside a capstone repository on its own agent."""
    from bootcamp_agent.capstone_repo import CapstoneError, grade_repo
    from bootcamp_agent.final_grade import write_report

    repo = Path.cwd()
    try:
        provider = load_settings().provider
    except ConfigError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"grading {agent} on the practice set, model lane: {provider}\n")
    try:
        outcome, lines = grade_repo(
            repo, agent_spec=agent, name=name, random_count=count, seed=seed
        )
    except CapstoneError as error:
        print(f"{FAIL} {error}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    destination = repo / report
    write_report(outcome, destination)
    print(f"report written: {report}")
    return 0 if outcome["passed"] else 1


def _capstone_trace(question: str, agent: str) -> int:
    """One question through the capstone's agent, with every step it took."""
    from bootcamp_agent.capstone_repo import CapstoneError, trace_lines

    try:
        lines = trace_lines(Path.cwd(), question, agent_spec=agent)
    except (CapstoneError, ConfigError, CorpusError) as error:
        print(f"{FAIL} {error}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    return 0


def _capstone_submit(args: argparse.Namespace) -> int:
    """The final assignment: practise locally, answer the final set, open the pull request."""
    from bootcamp_agent.capstone_submit import SubmitError, submit
    from bootcamp_agent.questions_api import API_ENV, FinalNotOpen, NotPublished, QuestionsError

    repo = Path.cwd()
    try:
        settings = load_settings(dotenv_path=repo / ".env")
    except ConfigError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    try:
        done = submit(
            repo,
            github=args.github,
            api_base=args.api or os.environ.get(API_ENV),
            settings=settings,
            agent_spec=args.agent,
            dry_run=args.dry_run,
            into=Path(args.into) if args.into else None,
            question_timeout_s=args.timeout,
            budget_s=args.budget,
        )
    except FinalNotOpen as error:
        print(f"\nThe final questions are not open yet. They open at {error.opens_at}.")
        print("Nothing was handed in. Run this again after that.")
        return 1
    except NotPublished:
        print("\nThe final questions are not published yet. Nothing was handed in.")
        return 1
    except (SubmitError, QuestionsError) as error:
        print(f"{FAIL} {error}", file=sys.stderr)
        return 2
    return 0 if args.dry_run or done.pr_url else 1


def bootcamp(argv: list[str] | None = None) -> int:
    """The participant's own command: check the setup, a chapter, or everything."""
    parser = argparse.ArgumentParser(
        prog="bootcamp",
        description="Check your setup and your chapter exercises.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("start", help="install everything and check it works — run this first")
    sub.add_parser("doctor", help="check this machine: Python, kernel, corpus, provider lane")
    checker = sub.add_parser("check", help="run one item's notebook and print its scorecard")
    checker.add_argument(
        "chapter", help="a session (ch03), a week-0 unit (w05), or the capstone (cap01)"
    )
    progress = sub.add_parser("progress", help="run every runnable chapter and tally the checks")
    progress.add_argument(
        "--export",
        nargs="?",
        const="-",
        metavar="FILE",
        help="write your own progress (outcomes only) to a file instead of running anything",
    )
    reader = sub.add_parser("read", help="render the course pages and open them locally")
    reader.add_argument("--port", type=int, default=8000)
    reader.add_argument("--build-only", action="store_true", help="write site/ and stop")
    submitter = sub.add_parser("submit", help="build the submission bundle to hand in")
    submitter.add_argument(
        "chapter", help="a session (ch03), a week-0 unit (w05), or the capstone (cap01)"
    )
    submitter.add_argument("--github", required=True, help="your GitHub username")
    submitter.add_argument("--cohort", default="2026-09", help="which cohort (default 2026-09)")
    submitter.add_argument("--into", help="submissions root (default ./submissions)")
    submitter.add_argument(
        "--push",
        action="store_true",
        help="fork, commit and open the pull request for you (needs the gh CLI)",
    )
    capstone = sub.add_parser(
        "capstone", help="your own capstone repository: new, grade, trace, submit"
    )
    capstone_sub = capstone.add_subparsers(dest="capstone_command")
    creator = capstone_sub.add_parser(
        "new", help="create your capstone repository beside the course (never pushes)"
    )
    creator.add_argument("folder", help="where to create it, outside the course: ../my-capstone")
    creator.add_argument(
        "--github", help="the GitHub repository name to publish as (NAME or OWNER/NAME)"
    )
    creator.add_argument(
        "--course-ref",
        help="the course commit to pin (default: the published commit this clone holds)",
    )
    grader = capstone_sub.add_parser(
        "grade", help="inside your capstone: grade its agent on the practice set"
    )
    grader.add_argument("--agent", default="agent.py", help="FILE[:CLASS] (default agent.py)")
    grader.add_argument("--name", default="", help="your display name, for the report")
    grader.add_argument("--report", default="score_report.json", help="where to write the report")
    grader.add_argument("--random", type=int, default=0, metavar="N", help="a sample of N")
    grader.add_argument("--seed", type=int, default=None, help="make --random repeatable")
    tracer = capstone_sub.add_parser(
        "trace", help="inside your capstone: answer one question and print every step"
    )
    tracer.add_argument("question", help="the question, in quotes")
    tracer.add_argument("--agent", default="agent.py", help="FILE[:CLASS] (default agent.py)")
    final = capstone_sub.add_parser(
        "submit", help="inside your capstone: answer the final questions and open the pull request"
    )
    final.add_argument("--github", required=True, help="your GitHub username")
    final.add_argument(
        "--api", help="the course app's address (default: the DEV3PACK_API_BASE variable)"
    )
    final.add_argument("--agent", default="agent.py", help="FILE[:CLASS] (default agent.py)")
    final.add_argument(
        "--dry-run",
        action="store_true",
        help="write the bundle to a temporary folder and print it; open no pull request",
    )
    final.add_argument("--into", help="where to write the bundle (default ~/.bootcamp/final)")
    final.add_argument(
        "--timeout", type=float, default=120.0, help="seconds per question (default 120)"
    )
    final.add_argument(
        "--budget", type=float, default=1800.0, help="seconds for the whole run (default 1800)"
    )
    args = parser.parse_args(argv)

    if args.command == "start":
        return _start()
    if args.command == "doctor":
        return _doctor()
    if args.command == "check":
        return _check(args.chapter)
    if args.command == "progress":
        if getattr(args, "export", None):
            return _export(None if args.export == "-" else Path(args.export))
        return _progress()
    if args.command == "read":
        return _read(args.port, args.build_only)
    if args.command == "submit":
        return _submit(args.chapter, args.github, args.cohort, args.into, args.push)
    if args.command == "capstone":
        if args.capstone_command == "new":
            return _capstone_new(args.folder, args.github, args.course_ref)
        if args.capstone_command == "grade":
            return _capstone_grade(args.agent, args.name, args.report, args.random, args.seed)
        if args.capstone_command == "trace":
            return _capstone_trace(args.question, args.agent)
        if args.capstone_command == "submit":
            return _capstone_submit(args)
        capstone.print_help()
        return 2
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
