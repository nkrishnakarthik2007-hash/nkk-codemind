"""Ollama HTTP adapter using only the Python standard library.

Ollama must be installed and running separately. CodeMind does not download models
silently: users choose and pull a model themselves.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ModelInfo:
    name: str
    size_bytes: int | None = None
    parameter_size: str | None = None
    quantization: str | None = None


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    prompt_tokens: int | None = None
    generated_tokens: int | None = None
    total_duration_ns: int | None = None


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot complete a request."""


class OllamaProvider:
    """Small synchronous adapter for Ollama's local HTTP API."""

    def __init__(self, host: str | None = None, timeout: float = 180.0) -> None:
        self.host = (host or os.environ.get("CODEMIND_OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
        self.timeout = timeout

    def _request(self, endpoint: str, payload: dict | None = None) -> dict:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.host}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"} if data is not None else {},
            method="POST" if data is not None else "GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(5_000_001)
            if len(raw) > 5_000_000:
                raise OllamaError("Ollama response exceeded the 5 MB safety limit.")
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise OllamaError("Ollama returned an unexpected response.")
            return parsed
        except HTTPError as exc:
            detail = exc.read(2000).decode("utf-8", errors="replace")
            raise OllamaError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise OllamaError(
                f"Cannot reach Ollama at {self.host}. Start Ollama and check its local API: {exc}"
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OllamaError("Ollama returned invalid JSON.") from exc

    def list_models(self) -> list[ModelInfo]:
        response = self._request("/api/tags")
        models = response.get("models", [])
        if not isinstance(models, list):
            raise OllamaError("Ollama model list has an unexpected format.")
        return [
            ModelInfo(
                name=str(item.get("name", "")),
                size_bytes=item.get("size"),
                parameter_size=(item.get("details") or {}).get("parameter_size"),
                quantization=(item.get("details") or {}).get("quantization_level"),
            )
            for item in models
            if isinstance(item, dict) and item.get("name")
        ]

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        num_ctx: int = 2048,
        num_predict: int = 512,
        keep_alive: str | int = 0,
    ) -> GenerationResult:
        if not model.strip():
            raise ValueError("A model name is required.")
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")
        if not 256 <= num_ctx <= 32768:
            raise ValueError("Context size must be between 256 and 32768 tokens.")
        if not 1 <= num_predict <= 8192:
            raise ValueError("Output limit must be between 1 and 8192 tokens.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._request(
            "/api/chat",
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "keep_alive": keep_alive,
                "options": {"num_ctx": num_ctx, "num_predict": num_predict},
            },
        )
        message = response.get("message") or {}
        text = message.get("content")
        if not isinstance(text, str):
            detail = response.get("error") or "No message content was returned."
            raise OllamaError(str(detail))
        return GenerationResult(
            text=text,
            model=str(response.get("model") or model),
            prompt_tokens=response.get("prompt_eval_count"),
            generated_tokens=response.get("eval_count"),
            total_duration_ns=response.get("total_duration"),
        )