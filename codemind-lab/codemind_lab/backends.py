"""GAMA-compatible model backends with a strict one-call-at-a-time CPU policy."""

from __future__ import annotations

import json
import os
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from gama.backends import ModelBackend
from gama.models import ModelTier

from .config import LabConfig, ModelSpec, check_memory_budget

_CALL_LOCK = threading.Lock()
_MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class ProviderError(RuntimeError):
    """A configured local model endpoint could not complete a request."""


class CpuGuard:
    """Serializes inference calls and checks available RAM before each model call."""

    def __init__(self, config: LabConfig):
        self.config = config

    def run(self, spec: ModelSpec, operation):
        # One active inference request prevents accidental multi-model RAM spikes.
        with _CALL_LOCK:
            check_memory_budget(spec, self.config.reserve_ram_gb)
            return operation()


class OllamaNativeBackend(ModelBackend):
    """Ollama /api/chat adapter; keep_alive=0 unloads the model after each call."""

    name = "codemind-ollama"

    def __init__(self, spec: ModelSpec, guard: CpuGuard, timeout: int = 180):
        self.spec = spec
        self.guard = guard
        self.timeout = timeout
        parsed = urlparse(spec.base_url)
        local_hosts = {"localhost", "127.0.0.1", "::1"}
        if not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Provider URL must have a host and no embedded credentials.")
        if parsed.scheme != "https" and parsed.hostname not in local_hosts:
            raise ValueError("Non-local OpenAI-compatible endpoints must use HTTPS.")
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Provider URL must use HTTP or HTTPS.")
        self.available = True
        self.last_usage = None
        self.last_finish_reason = None
        self.last_duration_seconds = None

    def complete(self, prompt: str, tier: ModelTier, **kwargs) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        def request_model():
            messages = []
            system = kwargs.get("system")
            if system:
                messages.append({"role": "system", "content": str(system)})
            messages.append({"role": "user", "content": prompt})
            payload = {
                "model": self.spec.model,
                "messages": messages,
                "stream": False,
                "keep_alive": 0 if self.spec.unload_after_call else "5m",
                "options": {
                    "num_ctx": self.spec.context_tokens,
                    "num_thread": self.guard.config.cpu_threads,
                    "num_predict": min(
                        self.spec.max_output_tokens,
                        int(kwargs.get("max_tokens", self.spec.max_output_tokens)),
                    ),
                    "temperature": float(kwargs.get("temperature", 0.2)),
                },
            }
            return self._post(f"{self.spec.base_url}/api/chat", payload)

        started = time.perf_counter()
        data = self.guard.run(self.spec, request_model)
        self.last_duration_seconds = time.perf_counter() - started
        message = data.get("message") or {}
        text = message.get("content")
        if not isinstance(text, str):
            raise ProviderError(str(data.get("error") or "Ollama returned no message content."))
        self.last_usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }
        self.last_finish_reason = data.get("done_reason")
        return text

    def _post(self, url: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(raw) > _MAX_RESPONSE_BYTES:
                raise ProviderError("Model response exceeded the 8 MB safety limit.")
            data = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read(2000).decode("utf-8", errors="replace")
            raise ProviderError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderError(f"Cannot reach Ollama at {self.spec.base_url}: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError("Ollama returned invalid JSON.") from exc
        if not isinstance(data, dict):
            raise ProviderError("Ollama returned an unexpected response.")
        return data


class OpenAICompatibleBackend(ModelBackend):
    """Adapter for LM Studio, llama.cpp server and documented OpenAI-compatible APIs."""

    name = "codemind-openai"

    def __init__(self, spec: ModelSpec, guard: CpuGuard, timeout: int = 180):
        self.spec = spec
        self.guard = guard
        self.timeout = timeout
        self.available = True
        self.last_usage = None
        self.last_finish_reason = None
        self.last_duration_seconds = None

    def complete(self, prompt: str, tier: ModelTier, **kwargs) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        def request_model():
            messages = []
            system = kwargs.get("system")
            if system:
                messages.append({"role": "system", "content": str(system)})
            messages.append({"role": "user", "content": prompt})
            payload = {
                "model": self.spec.model,
                "messages": messages,
                "stream": False,
                "max_tokens": min(
                    self.spec.max_output_tokens,
                    int(kwargs.get("max_tokens", self.spec.max_output_tokens)),
                ),
                "temperature": float(kwargs.get("temperature", 0.2)),
            }
            body = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if self.spec.api_key_env:
                key = os.environ.get(self.spec.api_key_env)
                if not key:
                    raise ProviderError(
                        f"Missing API key environment variable {self.spec.api_key_env}."
                    )
                headers["Authorization"] = f"Bearer {key}"
            request = Request(
                f"{self.spec.base_url}/chat/completions",
                data=body,
                headers=headers,
                method="POST",
            )
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    raw = response.read(_MAX_RESPONSE_BYTES + 1)
                if len(raw) > _MAX_RESPONSE_BYTES:
                    raise ProviderError("Model response exceeded the 8 MB safety limit.")
                data = json.loads(raw.decode("utf-8"))
            except HTTPError as exc:
                detail = exc.read(2000).decode("utf-8", errors="replace")
                raise ProviderError(f"Provider HTTP {exc.code}: {detail}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                raise ProviderError(f"Cannot reach {self.spec.base_url}: {exc}") from exc
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProviderError("Provider returned invalid JSON.") from exc
            if not isinstance(data, dict):
                raise ProviderError("Provider returned an unexpected response.")
            return data

        started = time.perf_counter()
        data = self.guard.run(self.spec, request_model)
        self.last_duration_seconds = time.perf_counter() - started
        choices = data.get("choices") or []
        message = choices[0].get("message") if choices and isinstance(choices[0], dict) else None
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str):
            raise ProviderError(str(data.get("error") or "Provider returned no message content."))
        self.last_usage = data.get("usage")
        self.last_finish_reason = choices[0].get("finish_reason") if choices else None
        return text


def build_backends(config: LabConfig) -> tuple[dict[str, ModelBackend], CpuGuard]:
    guard = CpuGuard(config)
    result: dict[str, ModelBackend] = {}
    for spec in config.models:
        kind = spec.backend.lower()
        if kind == "ollama":
            result[spec.name] = OllamaNativeBackend(
                spec, guard, timeout=config.request_timeout_seconds
            )
        elif kind in {"openai", "lmstudio", "llamacpp"}:
            result[spec.name] = OpenAICompatibleBackend(
                spec, guard, timeout=config.request_timeout_seconds
            )
        else:
            raise ValueError(f"Unsupported backend {spec.backend!r} for model {spec.name!r}.")
    return result, guard


def build_router(config: LabConfig, routing_table: dict[str, str] | None = None):
    """Build GAMA's measured task router over CodeMind's CPU-guarded model adapters."""
    backends, _ = build_backends(config)
    first = next(iter(backends))
    return GamaBackend(backends, routing_table=routing_table or {}, default=first)


def build_sequential_ensemble(config: LabConfig, member_names: list[str] | None = None):
    """Build GAMA's sequential Mixture-of-Agents composite under the CPU call lock."""
    backends, _ = build_backends(config)
    names = member_names or list(backends)[:config.max_ensemble_members]
    if not 1 <= len(names) <= config.max_ensemble_members:
        raise ValueError(
            f"Choose between 1 and {config.max_ensemble_members} ensemble members."
        )
    missing = [name for name in names if name not in backends]
    if missing:
        raise ValueError(f"Unknown model names: {', '.join(missing)}")
    members = [backends[name] for name in names]
    # GAMA runs ensemble members sequentially. Synthesis is used instead of naive
    # majority voting because free-form code answers rarely match byte-for-byte.
    return EnsembleBackend(
        members,
        strategy="synthesize",
        aggregator=members[-1],
        aggregator_prompt=(
            "Compare the candidate solutions. Check for correctness, completeness and "
            "consistency with the original request. Return one improved final answer only."
        ),
    )
