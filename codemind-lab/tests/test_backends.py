import json

from gama.models import ModelTier

from codemind_lab.backends import OllamaNativeBackend, OpenAICompatibleBackend
from codemind_lab.config import LabConfig, ModelSpec
from codemind_lab.backends import CpuGuard


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.payload[:size]


def test_ollama_backend_requests_unload_and_small_context(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["payload"] = json.loads(request.data.decode())
        seen["timeout"] = timeout
        return FakeResponse({
            "model": "qwen2.5-coder:0.5b",
            "message": {"content": "print('ok')"},
            "prompt_eval_count": 12,
            "eval_count": 4,
            "done_reason": "stop",
        })

    monkeypatch.setattr("codemind_lab.backends.urlopen", fake_urlopen)
    cfg = LabConfig(models=())
    spec = ModelSpec(
        "tiny", "ollama", "qwen2.5-coder:0.5b", "http://127.0.0.1:11434",
        estimated_ram_gb=None, context_tokens=1024, max_output_tokens=128,
        unload_after_call=True,
    )
    backend = OllamaNativeBackend(spec, CpuGuard(cfg))
    answer = backend.complete("Write a tiny program", ModelTier.SMALL)

    assert answer == "print('ok')"
    assert seen["url"].endswith("/api/chat")
    assert seen["payload"]["keep_alive"] == 0
    assert seen["payload"]["options"]["num_ctx"] == 1024
    assert seen["payload"]["options"]["num_predict"] == 128
    assert backend.last_usage["completion_tokens"] == 4


def test_openai_compatible_backend_reads_key_from_environment(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["authorization"] = request.headers.get("Authorization")
        return FakeResponse({
            "model": "local-model",
            "choices": [{"message": {"content": "hello"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1},
        })

    monkeypatch.setenv("CODEMIND_TEST_KEY", "secret-test-key")
    monkeypatch.setattr("codemind_lab.backends.urlopen", fake_urlopen)
    cfg = LabConfig(models=())
    spec = ModelSpec(
        "lmstudio", "openai", "local-model", "http://127.0.0.1:1234/v1",
        api_key_env="CODEMIND_TEST_KEY",
    )
    backend = OpenAICompatibleBackend(spec, CpuGuard(cfg))
    assert backend.complete("Say hello", ModelTier.SMALL) == "hello"
    assert seen["authorization"] == "Bearer secret-test-key"
