from codemind import cli
from codemind.providers.ollama import GenerationResult


class FakeProvider:
    captured = None

    def __init__(self, host=None):
        self.host = host

    def generate(self, model, prompt, **kwargs):
        FakeProvider.captured = {"model": model, "prompt": prompt, **kwargs}
        return GenerationResult("Use json.load(file_handle).", model, 12, 9, 1_000_000_000)


def test_ask_includes_relevant_saved_knowledge(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CODEMIND_HOME", str(tmp_path / "codemind-data"))
    monkeypatch.setattr(cli, "OllamaProvider", FakeProvider)

    library = cli.KnowledgeLibrary()
    library.add_text(
        "Python JSON documentation",
        "https://docs.python.org/json",
        "Use json.load(file_object) to deserialize JSON from an open file.",
        tags=("python", "json"),
    )

    exit_code = cli.main([
        "ask", "How do I load JSON from a file?",
        "--model", "test-model",
    ])

    output = capsys.readouterr()
    assert exit_code == 0
    assert "Use json.load" in output.out
    assert "Using 1 saved knowledge excerpt" in output.err
    assert "docs.python.org/json" in FakeProvider.captured["system"]
    assert FakeProvider.captured["keep_alive"] == 0


def test_ask_works_without_saved_knowledge(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CODEMIND_HOME", str(tmp_path / "empty-library"))
    monkeypatch.setattr(cli, "OllamaProvider", FakeProvider)

    exit_code = cli.main(["ask", "Explain a Python list", "--model", "test-model"])
    output = capsys.readouterr()

    assert exit_code == 0
    assert "No matching saved knowledge" in output.err
    assert FakeProvider.captured["prompt"] == "Explain a Python list"
