from codemind_lab.config import LabConfig, ModelSpec, check_memory_budget, load_config


def test_config_enforces_single_active_call(tmp_path):
    config_file = tmp_path / "models.json"
    config_file.write_text(
        '{"policy":{"max_parallel_calls":2},"models":[{"name":"tiny","model":"tiny","base_url":"http://localhost"}]}',
        encoding="utf-8",
    )
    try:
        load_config(config_file)
    except ValueError as exc:
        assert "max_parallel_calls=1" in str(exc)
    else:
        raise AssertionError("parallel inference must be rejected in CPU-first mode")


def test_missing_estimate_does_not_guess_runtime_memory(monkeypatch):
    monkeypatch.setattr("codemind_lab.config.available_memory_bytes", lambda: 0)
    spec = ModelSpec("local", "openai", "test", "http://localhost")
    check_memory_budget(spec, reserve_ram_gb=1.5)


def test_memory_estimate_is_checked(monkeypatch):
    monkeypatch.setattr(
        "codemind_lab.config.available_memory_bytes",
        lambda: int(1.0 * (1024 ** 3)),
    )
    spec = ModelSpec("large", "ollama", "large", "http://localhost", estimated_ram_gb=1.0)
    try:
        check_memory_budget(spec, reserve_ram_gb=1.5)
    except MemoryError as exc:
        assert "Not enough currently available RAM" in str(exc)
    else:
        raise AssertionError("model should not consume the configured safety reserve")
