import json

from codemind.workspace import inspect_workspace, select_relevant_files


def test_inspect_detects_languages_and_frameworks(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"react": "^19.0.0", "vite": "^6.0.0"}}),
        encoding="utf-8",
    )
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.tsx").write_text("export const App = () => <div>Hello</div>;", encoding="utf-8")

    summary = inspect_workspace(tmp_path)

    assert "TypeScript" in summary.languages
    assert "JavaScript" in summary.languages
    assert "react" in summary.frameworks
    assert summary.file_count == 2


def test_select_relevant_files_ignores_dependency_folders(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "login.py").write_text(
        "def login_user(username, password):\n    return authenticate(username, password)\n",
        encoding="utf-8",
    )
    dependencies = tmp_path / "node_modules"
    dependencies.mkdir()
    (dependencies / "login.py").write_text("irrelevant dependency", encoding="utf-8")

    selected = select_relevant_files(tmp_path, "fix login_user authentication", max_files=2)

    assert len(selected) == 1
    assert selected[0].path == "src/login.py"


def test_workspace_context_skips_secret_files_and_redacts_tokens(tmp_path):
    (tmp_path / ".env").write_text("API_KEY=do-not-send-this-secret", encoding="utf-8")
    (tmp_path / "settings.py").write_text(
        'API_KEY = "do-not-send-this-secret"\\nprint("hello")', encoding="utf-8"
    )

    selected = select_relevant_files(tmp_path, "API_KEY settings")

    assert all(item.path != ".env" for item in selected)
    assert selected
    assert "do-not-send-this-secret" not in selected[0].content
    assert "[REDACTED]" in selected[0].content
