"""Pre-course setup doctor.

Run:  uv run python scripts/check_setup.py

Prints a green/red checklist. Every learner should see all green (warnings
are fine) BEFORE the first class on September 14. Screenshot the output and
post it in the cohort channel.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OK = "✅"
FAIL = "❌"
WARN = "⚠️ "


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

    warn(".env present", (ROOT / ".env").is_file(), "cp .env.example .env (optional for now)")

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
    print("\nAll set. See you September 14!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
