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
