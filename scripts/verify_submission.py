"""Re-run a submitted notebook and say whether its claimed score holds.

    uv run python scripts/verify_submission.py submissions/octocat/ch03

A submission is a CLAIM plus its EVIDENCE. The claim is `submission.json`; the
evidence is the notebook beside it. This script makes the claim falsifiable: it
copies the submitted notebook into the course tree, runs it with the checks
non-strict, and compares what the notebook's own `check()` calls printed against
what the file says they printed.

WHY COPY RATHER THAN RUN IN PLACE. A chapter's notebook resolves its imports and
fixtures relative to the course, so `units/en/session-03-structured-outputs/notebook.ipynb`
is the only path at which chapter 3 can run. Copying is what lets somebody
else's notebook be judged by our harness rather than by their environment.

WHAT THIS PROVES, AND WHAT IT DOES NOT. It proves the notebook in the pull
request produces the results claimed for it. It cannot prove how much help was
taken, because the hint database never leaves the learner's machine, and help
only ever costs marks, so nobody gains by over-reporting it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bootcamp_agent import submission  # noqa: E402
from bootcamp_agent.coursework import CourseworkError, run_notebook  # noqa: E402

#: A bundle is exactly two files. Anything else in the folder is refused rather
#: than ignored: a verifier that silently skips what it does not understand is
#: how a payload rides along beside an honest claim.
ALLOWED = {submission.SUBMISSION_FILE, submission.NOTEBOOK_FILE}

#: Caps, because this reads files a stranger wrote. A claim is a few hundred
#: bytes and a teaching notebook is well under a megabyte; these are ceilings,
#: not targets.
MAX_CLAIM_BYTES = 64 * 1024
MAX_NOTEBOOK_BYTES = 8 * 1024 * 1024


class VerifyError(Exception):
    """The submission is malformed, or its claim did not survive the re-run."""


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    """Reject a JSON object that names the same key twice.

    `json.loads` keeps the last value, so `{"score": 100, "score": 9999}` parses
    to 9999 while a human reading the file sees 100. Two readers disagreeing
    about the same bytes is exactly what a claim must not allow.
    """
    seen: dict = {}
    for key, value in pairs:
        if key in seen:
            raise VerifyError(f"the claim names {key!r} twice; one file, one value")
        seen[key] = value
    return seen


def check_shape(directory: Path) -> None:
    """The bundle holds two regular files, both within their cap, and nothing else."""
    if not directory.is_dir() or directory.is_symlink():
        raise VerifyError(f"{directory} is not a directory")
    for entry in sorted(directory.iterdir()):
        if entry.name not in ALLOWED:
            raise VerifyError(f"unexpected file in the bundle: {entry.name}")
        if entry.is_symlink() or not entry.is_file():
            raise VerifyError(f"{entry.name} must be a regular file")
    caps = {
        submission.SUBMISSION_FILE: MAX_CLAIM_BYTES,
        submission.NOTEBOOK_FILE: MAX_NOTEBOOK_BYTES,
    }
    for name, cap in caps.items():
        path = directory / name
        if path.is_file() and path.stat().st_size > cap:
            raise VerifyError(f"{name} is {path.stat().st_size} bytes, over the {cap}-byte cap")


def read_claim(directory: Path) -> dict:
    """Load and shape-check the claim before anything expensive happens."""
    claim_path = directory / submission.SUBMISSION_FILE
    if not claim_path.is_file():
        raise VerifyError(f"no {submission.SUBMISSION_FILE} in {directory}")
    try:
        claim = json.loads(claim_path.read_text(), object_pairs_hook=_no_duplicate_keys)
    except json.JSONDecodeError as error:
        raise VerifyError(f"{claim_path} is not valid JSON: {error}") from error
    if not isinstance(claim, dict):
        raise VerifyError("the claim must be a JSON object")

    if claim.get("schema") != submission.SCHEMA:
        raise VerifyError(f"unknown schema {claim.get('schema')!r}, expected {submission.SCHEMA!r}")
    for field in ("chapter", "result", "student", "evidence"):
        if field not in claim:
            raise VerifyError(f"the submission has no {field!r}")
    if problem := submission.id_problem(claim):
        raise VerifyError(problem)
    return claim


def check_evidence(directory: Path, claim: dict) -> Path:
    """The notebook must be present and be the one the claim was made about."""
    notebook = directory / submission.NOTEBOOK_FILE
    if not notebook.is_file():
        raise VerifyError(f"no {submission.NOTEBOOK_FILE} beside the claim")

    expected = claim["evidence"].get("notebook_sha256")
    actual = submission.sha256_of(notebook)
    if expected != actual:
        raise VerifyError(
            "the notebook is not the one this score was claimed for "
            f"(claim says {str(expected)[:12]}…, the file is {actual[:12]}…)"
        )
    return notebook


def verify(directory: Path, timeout: int = 300) -> list[str]:
    """Re-run the submitted notebook. Returns the disagreements; empty is a pass."""
    check_shape(directory)
    claim = read_claim(directory)
    notebook = check_evidence(directory, claim)

    try:
        item = submission.resolve(claim["chapter"])
    except (KeyError, submission.SubmissionError) as error:
        raise VerifyError(f"unknown item {claim['chapter']!r}") from error
    if not item.verifiable:
        raise VerifyError(f"{item.id} cannot be re-run: {item.note}")

    # Put the course's own notebook back whatever happens, so one verification
    # cannot poison the next.
    original = item.notebook.read_bytes()
    try:
        shutil.copyfile(notebook, item.notebook)
        card = run_notebook(item.notebook, item.exercises, item.id, timeout=timeout)
    except CourseworkError as error:
        raise VerifyError(f"the submitted notebook did not run: {error}") from error
    finally:
        item.notebook.write_bytes(original)

    return submission.compare(claim, card)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="a submissions/<user>/<item> folder")
    parser.add_argument("--timeout", type=int, default=300, help="seconds per cell")
    args = parser.parse_args(argv)

    print(f"verifying {args.directory}")
    try:
        problems = verify(args.directory, timeout=args.timeout)
    except VerifyError as error:
        print(f"\nREFUSED: {error}")
        return 1

    if problems:
        print("\nREFUSED: the re-run disagrees with the claim")
        for problem in problems:
            print(f"  {problem}")
        print("\nRe-run `uv run bootcamp submit` and commit what it writes.")
        return 1

    claim = read_claim(args.directory)
    result = claim["result"]
    print(
        f"\nVERIFIED: {len(result['passed'])} passed, score {result['score']}/{result['max_score']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
