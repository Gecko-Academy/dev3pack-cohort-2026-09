"""The LLM seam: one Protocol, one deterministic fake, two thin live adapters.

The fake is the default everywhere (tests, notebooks, classroom demos): it is
deterministic, offline, and free. Live adapters import their SDK lazily so the
base install never requires a provider package.
"""

from __future__ import annotations

from typing import Protocol

from bootcamp_agent.config import ConfigError, Settings

DEFAULT_FAKE_ANSWER = (
    '{"answer": "I do not know based on the provided corpus.", "citations": [], '
    '"confidence": 0.0, "needs_human_review": true}'
)


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str:
        """Return the model's text for one system+user exchange."""
        ...


class FakeLLM:
    """Deterministic stand-in: keyword-matched canned responses, no network.

    The first key (in insertion order) found case-insensitively in `user`
    wins; otherwise `default` is returned. Every call is recorded in `calls`
    so tests and notebooks can assert on what was asked.
    """

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        default: str = DEFAULT_FAKE_ANSWER,
    ) -> None:
        self.responses = responses or {}
        self.default = default
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        lowered = user.lower()
        for keyword, response in self.responses.items():
            if keyword.lower() in lowered:
                return response
        return self.default


class AnthropicClient:
    """Thin adapter over the anthropic SDK (installed via the `anthropic` extra)."""

    def __init__(self, api_key: str, model: str) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class OpenAICompatibleClient:
    """Adapter for OpenAI and any OpenAI-compatible endpoint (e.g. OpenRouter)."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        import openai

        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""


def get_client(settings: Settings) -> LLMClient:
    """Resolve Settings into a client. Missing keys fail closed, without echoing them."""
    if settings.provider == "fake":
        return FakeLLM()
    if settings.provider == "ollama":
        # Local lane: no key, no SDK. Imported here so the module stays a thin seam.
        from bootcamp_agent.ollama import DEFAULT_BASE_URL, DEFAULT_MODEL, OllamaClient

        return OllamaClient(
            model=settings.model or DEFAULT_MODEL,
            base_url=settings.base_url or DEFAULT_BASE_URL,
        )
    if settings.provider not in ("anthropic", "openai"):
        raise ConfigError(f"No client for provider {settings.provider!r}")
    if not settings.api_key:
        raise ConfigError(
            f"Provider {settings.provider!r} needs an API key in the environment; "
            "see .env.example. (The key itself is never printed.)"
        )
    model = settings.model or (
        "claude-sonnet-5" if settings.provider == "anthropic" else "gpt-4o-mini"
    )
    if settings.provider == "anthropic":
        return AnthropicClient(api_key=settings.api_key, model=model)
    return OpenAICompatibleClient(api_key=settings.api_key, model=model, base_url=settings.base_url)
