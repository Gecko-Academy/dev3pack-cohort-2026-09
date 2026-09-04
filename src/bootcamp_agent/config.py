"""Settings loaded from the environment.

The provider seam starts here: everything provider-specific reduces to the
four fields of `Settings`. Tests pass an explicit `env` mapping; the CLI
passes nothing and gets `os.environ` (with `.env` loaded by python-dotenv).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

KNOWN_PROVIDERS = ("fake", "ollama", "anthropic", "openai")

# The local lane. Ollama needs no key and serves an OpenAI-compatible API.
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434/v1"


class ConfigError(Exception):
    """Raised for unusable configuration. Never includes secret material."""


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str | None
    api_key: str | None
    base_url: str | None


def load_settings(
    env: Mapping[str, str] | None = None, dotenv_path: Path | None = None
) -> Settings:
    """Build Settings from `env`, defaulting to the real environment + .env file.

    `dotenv_path` pins the .env file; notebooks pass the repo root's, because
    their working directory is a chapter folder.
    """
    if env is None:
        load_dotenv(dotenv_path)
        env = os.environ

    provider = env.get("BOOTCAMP_PROVIDER", "fake").strip() or "fake"
    if provider not in KNOWN_PROVIDERS:
        raise ConfigError(
            f"Unknown BOOTCAMP_PROVIDER {provider!r}; expected one of {KNOWN_PROVIDERS}"
        )

    key_var = {
        "fake": None,
        "ollama": None,
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }[provider]
    api_key = env.get(key_var) or None if key_var else None
    if provider == "openai":
        base_url = env.get("OPENAI_BASE_URL") or None
    elif provider == "ollama":
        base_url = env.get("OLLAMA_BASE_URL") or OLLAMA_DEFAULT_BASE_URL
    else:
        base_url = None
    return Settings(
        provider=provider,
        model=env.get("BOOTCAMP_MODEL") or None,
        api_key=api_key,
        base_url=base_url,
    )
