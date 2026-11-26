import json

import pytest

from codemind.providers.openai_compatible import CloudProviderError, OpenAICompatibleProvider


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return json.dumps({
            "model": "free-code-model",
            "choices": [{"message": {"content": "print('ok')"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4},
        }).encode("utf-8")[:size]


def test_cloud_provider_requires_explicit_api_key(monkeypatch):
    monkeypatch.delenv("CODEMIND_API_KEY", raising=False)
    with pytest.raises(CloudProviderError, match="opt-in"):
        OpenAICompatibleProvider().generate("model", "hello")


def test_cloud_provider_sends_authorized_chat_request(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["auth"] = request.headers["Authorization"]
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr("codemind.providers.openai_compatible.urlopen", fake_urlopen)
    provider = OpenAICompatibleProvider(
        base_url="https://example-provider.test/v1",
        api_key="test-secret",
    )
    result = provider.generate("free-code-model", "Write a hello function")

    assert result.text == "print('ok')"
    assert captured["url"] == "https://example-provider.test/v1/chat/completions"
    assert captured["auth"] == "Bearer test-secret"
    assert captured["payload"]["max_tokens"] == 512


def test_cloud_provider_rejects_plain_http_endpoint():
    with pytest.raises(ValueError, match="HTTPS"):
        OpenAICompatibleProvider(base_url="http://provider.example/v1", api_key="secret")
