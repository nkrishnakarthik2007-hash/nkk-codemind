import json
from io import BytesIO

import pytest

from codemind.providers.ollama import OllamaError, OllamaProvider


class FakeResponse:
    def __init__(self, payload: dict):
        self.raw = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.raw[:size]


def test_list_models(monkeypatch):
    def fake_urlopen(request, timeout):
        assert request.full_url.endswith("/api/tags")
        return FakeResponse({"models": [{"name": "qwen2.5-coder:1.5b", "size": 123, "details": {"parameter_size": "1.5B", "quantization_level": "Q4_K_M"}}]})

    monkeypatch.setattr("codemind.providers.ollama.urlopen", fake_urlopen)
    models = OllamaProvider().list_models()

    assert models[0].name == "qwen2.5-coder:1.5b"
    assert models[0].quantization == "Q4_K_M"


def test_generate_sends_bounded_context_and_unloads_by_default(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({
            "model": "qwen2.5-coder:1.5b",
            "message": {"content": "print('hello')"},
            "prompt_eval_count": 20,
            "eval_count": 8,
            "total_duration": 1000,
        })

    monkeypatch.setattr("codemind.providers.ollama.urlopen", fake_urlopen)
    result = OllamaProvider().generate(
        "qwen2.5-coder:1.5b", "Write hello world", system="You are a coding assistant."
    )

    assert result.text == "print('hello')"
    assert captured["payload"]["keep_alive"] == 0
    assert captured["payload"]["options"]["num_ctx"] == 2048
    assert len(captured["payload"]["messages"]) == 2


def test_generate_rejects_unbounded_context():
    with pytest.raises(ValueError):
        OllamaProvider().generate("model", "prompt", num_ctx=100000)


def test_generate_rejects_empty_prompt():
    with pytest.raises(ValueError):
        OllamaProvider().generate("model", "   ")