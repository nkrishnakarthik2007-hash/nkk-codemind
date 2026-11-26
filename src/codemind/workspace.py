"""Lightweight workspace inventory and relevance-based file selection."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", "target", ".next", ".turbo",
    ".ssh", ".aws", ".azure", ".gnupg", ".kube",
}
TEXT_EXTENSIONS = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".html", ".css", ".scss", ".json", ".toml", ".md", ".rst",
    ".rs", ".go", ".java", ".cs", ".c", ".h", ".cpp", ".hpp",
    ".sql", ".yaml", ".yml", ".sh", ".ps1",
}
SECRET_FILE_NAMES = {".env", ".env.local", ".env.production", ".npmrc", ".pypirc", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}
SECRET_PATTERN = re.compile(r'(?i)(api[_-]?key|secret|password|access[_-]?token|refresh[_-]?token)(\s*[:=]\s*)(["\']?)[^"\'\s,;]{6,}')

LANGUAGE_BY_EXTENSION = {
    ".py": "Python", ".pyi": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".cjs": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".rs": "Rust", ".go": "Go", ".java": "Java", ".cs": "C#",
    ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++", ".sql": "SQL",
    ".sh": "Shell", ".ps1": "PowerShell",
}


@dataclass(frozen=True)
class WorkspaceFile:
    path: str
    language: str
    size_bytes: int


@dataclass(frozen=True)
class WorkspaceSummary:
    root: str
    file_count: int
    languages: tuple[str, ...]
    frameworks: tuple[str, ...]
    files: tuple[WorkspaceFile, ...]


@dataclass(frozen=True)
class SelectedFile:
    path: str
    content: str
    score: int


def _walk_files(root: Path, max_files: int = 3000):
    count = 0
    for current, directories, filenames in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in IGNORED_DIRS)
        for filename in sorted(filenames):
            path = Path(current) / filename
            if filename.lower() in SECRET_FILE_NAMES or filename.lower().startswith(".env."):
                continue
            if path.is_symlink():
                continue
            try:
                path.resolve().relative_to(root.resolve())
            except (OSError, ValueError):
                continue
            if path.suffix.lower() not in TEXT_EXTENSIONS and filename not in {
                "Dockerfile", "Makefile", "requirements.txt",
            }:
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size > 500_000:
                continue
            yield path, size
            count += 1
            if count >= max_files:
                return


def inspect_workspace(path: Path) -> WorkspaceSummary:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    entries = list(_walk_files(root))
    languages = {LANGUAGE_BY_EXTENSION[item.suffix.lower()] for item, _ in entries if item.suffix.lower() in LANGUAGE_BY_EXTENSION}
    frameworks: set[str] = set()
    package_json = root / "package.json"
    if package_json.is_file() and not package_json.is_symlink():
        languages.update({"JavaScript"})
        try:
            package = json.loads(package_json.read_text(encoding="utf-8"))
            dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
            for name in ("react", "next", "vue", "vite", "express", "electron", "tauri"):
                if name in dependencies:
                    frameworks.add(name)
            if "typescript" in dependencies:
                languages.add("TypeScript")
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        languages.add("Python")
    if (root / "Cargo.toml").exists():
        languages.add("Rust")
    if (root / "go.mod").exists():
        languages.add("Go")

    files = tuple(
        WorkspaceFile(str(item.relative_to(root)), LANGUAGE_BY_EXTENSION.get(item.suffix.lower(), "Text"), size)
        for item, size in entries
    )
    return WorkspaceSummary(
        root=str(root),
        file_count=len(files),
        languages=tuple(sorted(languages)),
        frameworks=tuple(sorted(frameworks)),
        files=files,
    )


def select_relevant_files(
    path: Path,
    query: str,
    *,
    max_files: int = 3,
    max_chars_per_file: int = 2500,
) -> list[SelectedFile]:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    terms = {term for term in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{1,}", query.lower())}
    candidates: list[SelectedFile] = []

    for file_path, _size in _walk_files(root):
        relative = str(file_path.relative_to(root))
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lower = text.lower()
        score = sum(lower.count(term) for term in terms)
        score += sum(3 for term in terms if term in relative.lower())
        if file_path.name.lower() in {"readme.md", "pyproject.toml", "package.json", "requirements.txt"}:
            score += 1
        if score:
            safe_text = SECRET_PATTERN.sub(r"\1\2[REDACTED]", text)
            candidates.append(SelectedFile(relative, safe_text[:max_chars_per_file], score))

    candidates.sort(key=lambda item: (-item.score, item.path))
    return candidates[:max(1, min(max_files, 10))]
