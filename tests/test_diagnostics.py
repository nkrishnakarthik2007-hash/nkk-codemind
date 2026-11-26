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
