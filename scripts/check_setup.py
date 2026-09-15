"""The setup doctor.

Run:  uv run bootcamp doctor

Prints a green/red checklist. Every learner should see all green (warnings are
fine) BEFORE their next session. Screenshot the output and post it in the cohort
channel.

THE LAST LINE IS COMPUTED, NOT TYPED. It used to read "See you September 14!"
forever, so from the 15th onward the first thing a learner saw after a
successful install was a date that had already passed -- which reads as software
nobody has looked at since. It now names the next session from the curriculum,
and says something true after the last one.
"""

from __future__ import annotations

import os
import shutil
import site
import stat
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OK = "✅"
FAIL = "❌"
WARN = "⚠️ "


def _next_session(today: date | None = None) -> str:
    """ "See you Tuesday, session 2" -- the next session on or after today.

    Reads the curriculum rather than a literal, because a greeting frozen at the
    first session's date is wrong on every day of the course except one.
    """
    sys.path.insert(0, str(ROOT / "src"))
    from bootcamp_agent.curriculum import CHAPTERS

    now = today or date.today()
    upcoming = [chapter for chapter in CHAPTERS if chapter.on >= now]
    if not upcoming:
        return "That is the whole course, and your setup still works."
    session = upcoming[0]
    when = "today" if session.on == now else session.on.strftime("%A %d %B")
    return f"Next up: session {session.number}, {session.title} — {when}."
    
def _unhide_venv_pth_files() -> bool:
    """Clear macOS's hidden flag from .venv's .pth files.

    uv marks the files it installs into .venv hidden on macOS. Since CPython
    3.11, site.py silently skips any hidden .pth file -- including the
    editable-install .pth that points at src/ -- so bootcamp_agent never lands
    on sys.path and every `uv run bootcamp ...` command dies with
    ModuleNotFoundError before this script's own checks get a chance to run.
    This runs first and repairs it every time the doctor runs directly.

    Clearing the flag alone only fixes the *next* process -- site.py already
    ran before this function does -- so re-run site.addsitedir() on the same
    directories to put bootcamp_agent on sys.path for this run too.
    """
    if not hasattr(os, "chflags"):
        return False
    lib_dir = ROOT / ".venv" / "lib"
    if not lib_dir.is_dir():
        return False
    cleared = False
    site_package_dirs: set[Path] = set()
    for pth in lib_dir.glob("python*/site-packages/*.pth"):
        try:
            if os.stat(pth).st_flags & stat.UF_HIDDEN:
                os.chflags(pth, 0)
                cleared = True
                site_package_dirs.add(pth.parent)
        except OSError:
            pass
    for site_dir in site_package_dirs:
        site.addsitedir(str(site_dir))
    return cleared


def main() -> int:
    failures = 0

    def check(label: str, passed: bool, hint: str = "") -> None:
        nonlocal failures
        mark = OK if passed else FAIL
        print(f"{mark} {label}" + (f"  -> {hint}" if not passed and hint else ""))
        if not passed:
            failures += 1

    def warn(label: str, passed: bool, hint: str = "") -> None:
        mark = OK if passed else WARN
        print(f"{mark} {label}" + (f"  -> {hint}" if not passed and hint else ""))

    check(
        f"Python {sys.version_info.major}.{sys.version_info.minor} (need >= 3.11)",
        sys.version_info >= (3, 11),
        "install with: uv python install 3.11",
    )
    check("uv on PATH", shutil.which("uv") is not None, "https://docs.astral.sh/uv/")

    if _unhide_venv_pth_files():
        check("macOS hidden .pth files cleared (uv/site.py interaction)", True)

    try:
        import bootcamp_agent

        check(f"bootcamp_agent {bootcamp_agent.__version__} importable", True)
    except ImportError:
        check("bootcamp_agent importable", False, "run: uv sync --group dev")
        print(f"\n{failures} problem(s) found — fix them and rerun.")
        return 1

    from bootcamp_agent.agent import answer_question
    from bootcamp_agent.documents import CorpusError, load_corpus
    from bootcamp_agent.llm import FakeLLM

    try:
        documents = load_corpus(ROOT / "data" / "corpus")
        check(f"teaching corpus loads ({len(documents)} documents)", len(documents) == 6)
    except CorpusError as error:
        check("teaching corpus loads", False, str(error))
        documents = []

    if documents:
        result = answer_question("zxqv wubble", documents, FakeLLM())
        check(
            "FakeLLM round-trip (refusal path works)",
            result.answer.needs_human_review,
        )

    # The label is what a reader SEES, so it has to describe the state found,
    # not the condition tested. ".env present -> cp .env.example .env" told a
    # fresh clone that the file is present and therefore should be created.
    _has_env = (ROOT / ".env").is_file()
    warn(
        ".env present" if _has_env else "no .env yet",
        _has_env,
        "cp .env.example .env (optional for now — every scored notebook runs without it)",
    )

    if (ROOT / ".env").is_file():
        from bootcamp_agent.config import ConfigError, load_settings

        try:
            settings = load_settings()
            if settings.provider == "fake":
                warn("provider = fake (fine for class; set a key later for live calls)", True)
            elif settings.provider == "ollama":
                from bootcamp_agent.ollama import DEFAULT_BASE_URL, DEFAULT_MODEL, probe

                model = settings.model or DEFAULT_MODEL
                base_url = settings.base_url or DEFAULT_BASE_URL
                result = probe(model=model, base_url=base_url)
                check(f"Ollama server reachable at {base_url}", result.reachable, result.fix)
                if result.reachable:
                    check(f"Ollama model {model} pulled", result.model_present, result.fix)
                if result.ok:
                    from bootcamp_agent.llm import get_client

                    reply = get_client(settings).complete("Answer with one word.", "Say ready.")
                    check("Ollama round-trip (one short completion)", bool(reply.strip()))
            else:
                warn(
                    f"provider = {settings.provider} with API key",
                    settings.api_key is not None,
                    "key missing; live calls will fail until it is set",
                )
        except ConfigError as error:
            check("provider configuration valid", False, str(error))

    if failures:
        print(f"\n{failures} problem(s) found — fix them and rerun.")
        return 1
    print(f"\nAll set. {_next_session()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
