"""The local lane: Ollama over its OpenAI-compatible HTTP API, stdlib only.

No SDK and no API key. The client posts the same `system` + `user` exchange
the other adapters send, so the seam (`LLMClient.complete`) stays one method.
`probe` is what the setup doctor and the notebook preflight call: it answers
"is the server up" and "is the model pulled" with a fix command for each.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen2.5:7b-instruct"


class OllamaError(Exception):
    """A local-server failure with the fix in the message."""


class OllamaClient:
    """Chat completion against an Ollama server (or any OpenAI-compatible endpoint)."""

    def __init__(
        self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL, timeout: float = 120
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def complete(self, system: str, user: str) -> str:
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        request = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise OllamaError(
                f"Ollama answered HTTP {error.code} for model {self._model!r}. "
                f"Pull it with: ollama pull {self._model}"
            ) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise OllamaError(
                f"No Ollama server at {self._base_url}. Start it with: ollama serve"
            ) from error
        try:
            return payload["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as error:
            raise OllamaError("Ollama returned a response without choices[0].message") from error


@dataclass(frozen=True)
class ProbeResult:
    reachable: bool
    model_present: bool
    models: tuple[str, ...] = field(default_factory=tuple)
    fix: str = ""

    @property
    def ok(self) -> bool:
        return self.reachable and self.model_present


def probe(
    model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL, timeout: float = 3
) -> ProbeResult:
    """Check the server and the model without sending a prompt. Never raises."""
    base = base_url.rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/models", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return ProbeResult(
            reachable=False,
            model_present=False,
            fix=f"no server at {base}; install Ollama (https://ollama.com) and run: ollama serve",
        )
    models = tuple(
        str(item.get("id", ""))
        for item in payload.get("data", [])
        if isinstance(item, dict) and item.get("id")
    )
    if model in models or f"{model}:latest" in models:
        return ProbeResult(reachable=True, model_present=True, models=models)
    return ProbeResult(
        reachable=True,
        model_present=False,
        models=models,
        fix=f"model {model!r} is not pulled; run: ollama pull {model}",
    )
