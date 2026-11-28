import json

import codemind_lab.backends as backend_module
import codemind_lab.engine as engine_module
from codemind_lab.config import LabConfig
from gama.models import ModelTier


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.payload[:size]


def test_ollama_discovery_lists_downloaded_models(monkeypatch):
    monkeypatch.setattr(
        backend_module,
        "urlopen",
        lambda request, timeout: FakeResponse({
            "models": [{"name": "qwen3:0.6b", "size": 1234}]
        }),
    )
    models = backend_module.list_ollama_models("http://127.0.0.1:11434")
    assert models[0]["name"] == "qwen3:0.6b"


def test_ollama_discovery_rejects_remote_http():
    try:
        backend_module.list_ollama_models("http://example.com:11434")
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("remote HTTP must be rejected")


class StubBackend:
    name = "stub"
    def __init__(self):
        self.last_usage = {"prompt_tokens": 5, "completion_tokens": 10}

    def complete(self, prompt, tier):
        assert tier is ModelTier.SMALL
        return "CODEMIND_PROFILE_OK"


def test_profile_records_latency_tokens_and_ram_snapshots(monkeypatch):
    backend = StubBackend()
    monkeypatch.setattr(
        engine_module,
        "build_backends",
        lambda config: ({"tiny": backend}, object()),
    )
    memory_values = iter([3 * 1024**3, 2.8 * 1024**3, 2.9 * 1024**3, 2.7 * 1024**3])
    monkeypatch.setattr(
        engine_module,
        "available_memory_bytes",
        lambda: int(next(memory_values)),
    )
    result = engine_module.profile_models(
        LabConfig(models=()), ["tiny"], prompt="test", repeats=2
    )
    report = result["results"]["tiny"]
    assert len(report["runs"]) == 2
    assert report["runs"][0]["prompt_tokens"] == 5
    assert report["runs"][0]["completion_tokens"] == 10
    assert report["runs"][0]["free_ram_before_gb"] == 3.0
    assert report["runs"][0]["free_ram_after_gb"] == 2.8
    assert "not peak process RAM" in report["memory_note"]
