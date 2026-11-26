import json
import zipfile

from codemind.diagnostics import (
    configure_logging,
    create_support_bundle,
    record_event,
    redact_text,
)


def test_redact_common_credentials():
    text = (
        "api_key=super-secret-value "
        "Authorization: Bearer abcdefghijklmnop "
        "ghp_abcdefghijklmnopqrstuvwxyz123456"
    )
    cleaned = redact_text(text)
    assert "super-secret-value" not in cleaned
    assert "abcdefghijklmnop" not in cleaned
    assert "ghp_abcdefghijklmnopqrstuvwxyz123456" not in cleaned
    assert "[REDACTED]" in cleaned


def test_logs_operational_metadata_without_sensitive_fields(tmp_path):
    log_path = configure_logging(tmp_path)
    record_event(
        "command_started",
        command="ask",
        prompt="private prompt text",
        model="local-model",
        api_key="secret-token-value",
        path="/private/project",
    )

    entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(entries) == 1
    assert entries[0]["event"] == "command_started"
    assert entries[0]["data"]["command"] == "ask"
    assert entries[0]["data"]["model"] == "local-model"
    assert "prompt" not in entries[0]["data"]
    assert "path" not in entries[0]["data"]
    assert "secret-token-value" not in log_path.read_text(encoding="utf-8")


def test_support_bundle_contains_manifest_and_logs_only(tmp_path):
    configure_logging(tmp_path)
    record_event("test_event", command="inspect")
    destination = create_support_bundle(tmp_path / "support.zip", home=tmp_path)

    with zipfile.ZipFile(destination) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "logs/codemind.jsonl" in names
        assert not any("documents" in name or ".sqlite" in name for name in names)


def test_upload_requires_a_token(tmp_path, monkeypatch):
    from codemind.diagnostics import upload_support_bundle

    bundle = tmp_path / "support.zip"
    bundle.write_bytes(b"diagnostic-data")
    monkeypatch.delenv("CODEMIND_GITHUB_TOKEN", raising=False)

    import pytest

    with pytest.raises(ValueError, match="CODEMIND_GITHUB_TOKEN"):
        upload_support_bundle(bundle, "owner/private-diagnostics")


def test_upload_refuses_public_repositories(tmp_path, monkeypatch):
    import json
    import pytest

    from codemind.diagnostics import upload_support_bundle

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"private": False}).encode()

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())
    bundle = tmp_path / "support.zip"
    bundle.write_bytes(b"diagnostic-data")

    with pytest.raises(ValueError, match="must be private"):
        upload_support_bundle(bundle, "owner/public-repo", token="test-token")


def test_uploads_to_private_repo_and_creates_issue(tmp_path, monkeypatch):
    import json

    from codemind.diagnostics import upload_support_bundle

    calls = []

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(self.payload).encode()

    responses = [
        {"private": True},
        {"content": {"html_url": "https://github.com/owner/private-diagnostics/blob/main/report.zip"}},
        {"html_url": "https://github.com/owner/private-diagnostics/issues/1"},
    ]

    def fake_urlopen(request, timeout=30):
        calls.append((request.method, request.full_url, request.headers))
        return Response(responses.pop(0))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    bundle = tmp_path / "support.zip"
    bundle.write_bytes(b"diagnostic-data")

    issue_url = upload_support_bundle(
        bundle, "owner/private-diagnostics", token="test-token"
    )

    assert issue_url.endswith("/issues/1")
    assert [call[0] for call in calls] == ["GET", "PUT", "POST"]
    assert all(call[2].get("Authorization") == "Bearer test-token" for call in calls)
