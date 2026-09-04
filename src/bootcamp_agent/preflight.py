"""The notebook preflight: five checks, one fix line per failure, never raises.

Every notebook's first cell calls `preflight(REPO_ROOT)`. It prints a
checklist and returns the client for the configured lane. When the lane is
not usable (no Ollama server, missing key, SDK not installed) it prints the
fix and returns a `FakeLLM`, so the notebook still runs top to bottom.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from bootcamp_agent.config import ConfigError, Settings, load_settings
from bootcamp_agent.documents import CorpusError, load_corpus
from bootcamp_agent.llm import FakeLLM, LLMClient, get_client

OK = "✅"
FAIL = "❌"
WARN = "⚠️ "


@dataclass(frozen=True)
class Check:
    label: str
    passed: bool
    fix: str = ""
    blocking: bool = True

    def line(self) -> str:
        mark = OK if self.passed else (FAIL if self.blocking else WARN)
        return f"{mark} {self.label}" + (f"  -> {self.fix}" if not self.passed and self.fix else "")


@dataclass
class PreflightReport:
    checks: list[Check] = field(default_factory=list)
    lane: str = "fake"
    client: LLMClient = field(default_factory=FakeLLM)

    @property
    def ok(self) -> bool:
        return all(check.passed or not check.blocking for check in self.checks)


def _kernel_is_repo_venv(repo_root: Path) -> bool:
    prefix = Path(sys.prefix).resolve()
    venv = (repo_root / ".venv").resolve()
    return prefix == venv or venv in prefix.parents


def _lane_check(settings: Settings) -> tuple[Check, LLMClient]:
    """Resolve the configured lane to a client, or explain why it falls back to FakeLLM."""
    if settings.provider == "fake":
        return Check("lane = fake (deterministic, offline)", True), FakeLLM()
    if settings.provider == "ollama":
        from bootcamp_agent.ollama import DEFAULT_BASE_URL, DEFAULT_MODEL, probe

        model = settings.model or DEFAULT_MODEL
        base_url = settings.base_url or DEFAULT_BASE_URL
        result = probe(model=model, base_url=base_url)
        if result.ok:
            return Check(f"lane = ollama ({model} at {base_url})", True), get_client(settings)
        return (
            Check("lane = ollama, falling back to fake", False, result.fix, blocking=False),
            FakeLLM(),
        )
    try:
        client = get_client(settings)
    except (ConfigError, ImportError) as error:
        fix = str(error)
        if isinstance(error, ImportError):
            fix = f"SDK missing; run: uv sync --extra {settings.provider}"
        return (
            Check(f"lane = {settings.provider}, falling back to fake", False, fix, blocking=False),
            FakeLLM(),
        )
    return Check(f"lane = {settings.provider} (key present)", True), client


def run_preflight(repo_root: Path) -> PreflightReport:
    """Run the checks without printing. `preflight()` is the printing wrapper."""
    report = PreflightReport()
    report.checks.append(
        Check(
            f"Python {sys.version_info.major}.{sys.version_info.minor} (need >= 3.11)",
            sys.version_info >= (3, 11),
            "install with: uv python install 3.11",
        )
    )
    report.checks.append(
        Check(
            "kernel is the repo .venv",
            _kernel_is_repo_venv(repo_root),
            "pick the .venv kernel in Jupyter, or start it with: uv run jupyter lab",
            blocking=False,
        )
    )
    try:
        documents = load_corpus(repo_root / "data" / "corpus")
        report.checks.append(
            Check(f"corpus loads ({len(documents)} documents)", len(documents) == 6)
        )
    except CorpusError as error:
        report.checks.append(Check("corpus loads", False, str(error)))

    try:
        settings = load_settings(dotenv_path=repo_root / ".env")
    except ConfigError as error:
        report.checks.append(Check("provider configuration valid", False, str(error)))
        return report
    lane_check, client = _lane_check(settings)
    report.checks.append(lane_check)
    report.lane = settings.provider if lane_check.passed else "fake"
    report.client = client
    return report


def preflight(repo_root: Path) -> LLMClient:
    """Print the checklist and return the lane's client (FakeLLM on any fallback)."""
    report = run_preflight(repo_root)
    for check in report.checks:
        print(check.line())
    if report.ok:
        print(f"ready. LIVE is the {report.lane} lane.")
    else:
        print("fix the ❌ lines above, then rerun this cell. The notebook continues on FakeLLM.")
    return report.client
