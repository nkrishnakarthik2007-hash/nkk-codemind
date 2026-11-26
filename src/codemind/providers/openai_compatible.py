"""Opt-in OpenAI-compatible hosted inference adapter.

Works with providers exposing the /chat/completions API. The user must explicitly
select this provider and supply its API key through CODEMIND_API_KEY.
"""

from __future__ import annotations

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import GenerationResult


class CloudProviderError(RuntimeError):
    """Raised when a hosted inference request fails."""


class OpenAICompatibleProvider:
    """Generic adapter for compatible hosted inference APIs."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.environ.get("CODEMIND_BASE_URL")
            or "https://openrouter.ai/api/v1"
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("CODEMIND_API_KEY")
        self.timeout = timeout

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        num_ctx: int = 2048,
        num_predict: int = 512,
    ) -> GenerationResult:
        if not self.api_key:
            raise CloudProviderError(
                "Cloud inference is opt-in. Set CODEMIND_API_KEY and select "
                "--provider openai-compatible explicitly."
            )
        if not model.strip() or not prompt.strip():
            raise ValueError("A model name and non-empty prompt are required.")
        if not 1 <= num_predict <= 8192:
            raise ValueError("Output limit must be between 1 and 8192 tokens.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": num_predict,
            "stream": False,
        }).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "NKK-CodeMind/0.1",
            },
            method="POST",
        )
        started = time.perf_counter_ns()
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(5_000_001)
            if len(raw) > 5_000_000:
                raise CloudProviderError("Hosted model response exceeded the 5 MB safety limit.")
            data = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read(2000).decode("utf-8", errors="replace")
            raise CloudProviderError(f"Hosted provider HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise CloudProviderError(f"Hosted provider request failed: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CloudProviderError("Hosted provider returned invalid JSON.") from exc

        choices = data.get("choices") or []
        message = choices[0].get("message") if choices and isinstance(choices[0], dict) else None
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str):
            raise CloudProviderError(str(data.get("error") or "No message content was returned."))
        usage = data.get("usage") or {}
        return GenerationResult(
            text=text,
            model=str(data.get("model") or model),
            prompt_tokens=usage.get("prompt_tokens"),
            generated_tokens=usage.get("completion_tokens"),
            total_duration_ns=time.perf_counter_ns() - started,
        )
