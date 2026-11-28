"""Safe, preview-first application of unified diffs to a selected workspace.

This module deliberately supports edits to existing UTF-8 text files only. It rejects
file creation/deletion, renames, binary patches, path traversal and symlinks.
"""

from __future__ import annotations

import difflib
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

MAX_PATCH_BYTES = 2 * 1024 * 1024
MAX_FILES_PER_PATCH = 20
MAX_FILE_BYTES = 1_000_000
BLOCKED_PATH_PARTS = {
    ".git", ".ssh", ".aws", ".azure", ".gnupg", ".kube",
    ".venv", "venv", "node_modules", "__pycache__",
}
BLOCKED_FILE_NAMES = {
    ".env", ".npmrc", ".pypirc", "credentials.json", "secrets.json",
    "id_rsa", "id_ed25519",
}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore"}
_HUNK_HEADER = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$"
)


class PatchError(ValueError):
    """Raised when a patch is unsafe, malformed, or does not match the workspace."""


@dataclass(frozen=True)
class FileChange:
    path: str
    original: str
    updated: str
    diff: str


@dataclass(frozen=True)
class PatchPreview:
    changes: tuple[FileChange, ...]

    @property
    def file_count(self) -> int:
        return len(self.changes)


def _safe_relative_path(raw: str) -> str:
    value = raw.strip().replace("\\", "/")
    if value.startswith(("a/", "b/")):
        value = value[2:]
    if not value or value == "/dev/null":
        raise PatchError("New and deleted files are not supported yet.")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise PatchError("Absolute paths are not allowed in patches.")
    path = PurePosixPath(value)
    if any(part in ("", ".", "..") for part in path.parts):
        raise PatchError("Patch paths must stay inside the selected workspace.")
    if not path.parts:
        raise PatchError("Patch contains an empty file path.")
    return path.as_posix()


def _parse_file_patches(patch_text: str) -> list[tuple[str, list[tuple[int, int, list[str], list[str]]]]]:
    if not patch_text.strip():
        raise PatchError("Patch is empty.")
    if "\x00" in patch_text:
        raise PatchError("Binary patches are not supported.")
    if len(patch_text.encode("utf-8")) > MAX_PATCH_BYTES:
        raise PatchError("Patch exceeds the 2 MB safety limit.")

    lines = patch_text.splitlines(keepends=True)
    files: list[tuple[str, list[tuple[int, int, list[str], list[str]]]]] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if line.startswith(("diff --git ", "index ", "new file mode ", "deleted file mode ")):
            if line.startswith(("new file mode ", "deleted file mode ")):
                raise PatchError("Creating or deleting files is not supported.")
            index += 1
            continue
        if not line.startswith("--- "):
            index += 1
            continue
        if index + 1 >= len(lines) or not lines[index + 1].startswith("+++ "):
            raise PatchError("Malformed patch: expected paired --- and +++ file headers.")

        old_path = _safe_relative_path(line[4:].rstrip("\r\n").split("\t", 1)[0])
        new_path = _safe_relative_path(lines[index + 1][4:].rstrip("\r\n").split("\t", 1)[0])
        if old_path != new_path:
            raise PatchError("File renames are not supported; old and new paths must match.")
        index += 2
        hunks: list[tuple[int, int, list[str], list[str]]] = []

        while index < len(lines) and not lines[index].startswith("--- "):
            header = lines[index].rstrip("\r\n")
            if header.startswith(("diff --git ", "new file mode ", "deleted file mode ")):
                break
            match = _HUNK_HEADER.match(header)
            if not match:
                if header.startswith("\\ No newline at end of file"):
                    raise PatchError("Patches without a final newline are not supported yet.")
                if header.startswith(("GIT binary patch", "Binary files ")):
                    raise PatchError("Binary patches are not supported.")
                index += 1
                continue

            old_start = int(match.group(1))
            old_count = int(match.group(2) or "1")
            new_count = int(match.group(4) or "1")
            index += 1
            old_lines: list[str] = []
            new_lines: list[str] = []
            consumed_old = consumed_new = 0

            while index < len(lines):
                hunk_line = lines[index]
                if hunk_line.startswith(("@@ ", "--- ")):
                    break
                if hunk_line.startswith("\\ No newline at end of file"):
                    raise PatchError("Patches without a final newline are not supported yet.")
                if not hunk_line or hunk_line[0] not in " +-":
                    break
                marker, body = hunk_line[0], hunk_line[1:].replace("\\r\\n", "\\n")
                if marker in " -":
                    old_lines.append(body)
                    consumed_old += 1
                if marker in " +":
                    new_lines.append(body)
                    consumed_new += 1
                index += 1
                if consumed_old == old_count and consumed_new == new_count:
                    break

            if consumed_old != old_count or consumed_new != new_count:
                raise PatchError("Malformed patch: hunk line counts do not match its header.")
            hunk_index = old_start if old_count == 0 else old_start - 1
            hunks.append((hunk_index, old_count, old_lines, new_lines))

        if not hunks:
            raise PatchError(f"Patch for {old_path} does not contain any valid hunks.")
        files.append((old_path, hunks))
        if len(files) > MAX_FILES_PER_PATCH:
            raise PatchError(f"A patch may change at most {MAX_FILES_PER_PATCH} files.")

    if not files:
        raise PatchError("No unified-diff file changes were found.")
    paths = [path for path, _ in files]
    if len(paths) != len(set(paths)):
        raise PatchError("A patch must not contain the same file more than once.")
    return files


def _resolve_workspace_file(root: Path, relative: str) -> Path:
    workspace = root.expanduser().resolve()
    if not workspace.is_dir():
        raise NotADirectoryError(workspace)

    candidate = workspace
    parts = PurePosixPath(relative).parts
    if any(part.lower() in BLOCKED_PATH_PARTS for part in parts):
        raise PatchError(f"Sensitive or generated directories cannot be patch targets: {relative}")
    filename = parts[-1].lower()
    if filename in BLOCKED_FILE_NAMES or filename.startswith(".env.") or Path(filename).suffix in BLOCKED_SUFFIXES:
        raise PatchError(f"Sensitive files cannot be patch targets: {relative}")
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise PatchError(f"Symlinks are not allowed in patch paths: {relative}")

    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(workspace)
    except (OSError, ValueError) as exc:
        raise PatchError(f"Patch path is missing or escapes the workspace: {relative}") from exc
    if not resolved.is_file():
        raise PatchError(f"Patch target is not a regular file: {relative}")
    if resolved.stat().st_size > MAX_FILE_BYTES:
        raise PatchError(f"Patch target exceeds the 1 MB safety limit: {relative}")
    return resolved


def _apply_hunks(original: str, hunks: list[tuple[int, int, list[str], list[str]]], path: str) -> str:
    source_lines = original.splitlines(keepends=True)
    result: list[str] = []
    cursor = 0

    for start, old_count, expected_old, replacement in hunks:
        if start < cursor or start > len(source_lines):
            raise PatchError(f"Overlapping or out-of-range hunk in {path}.")
        actual = source_lines[start : start + old_count]
        normalized_actual = [line.replace("\r\n", "\n") for line in actual]
        if normalized_actual != expected_old:
            raise PatchError(
                f"Patch context does not match {path} at line {start + 1}; "
                "the file may have changed since the patch was generated."
            )
        newline = "\r\n" if "\r\n" in original else "\n"
        normalized_replacement = [
            line.replace("\r\n", "\n").replace("\n", newline)
            for line in replacement
        ]
        result.extend(source_lines[cursor:start])
        result.extend(normalized_replacement)
        cursor = start + old_count

    result.extend(source_lines[cursor:])
    updated = "".join(result)
    if updated == original:
        raise PatchError(f"Patch makes no change to {path}.")
    return updated


def preview_patch(workspace: Path, patch_text: str) -> PatchPreview:
    """Validate a patch and return exact diffs without writing any files."""
    file_patches = _parse_file_patches(patch_text)
    changes: list[FileChange] = []

    for relative, hunks in file_patches:
        target = _resolve_workspace_file(workspace, relative)
        try:
            with target.open("r", encoding="utf-8", newline="") as handle:
                original = handle.read(MAX_FILE_BYTES + 1)
        except UnicodeDecodeError as exc:
            raise PatchError(f"Patch target is not UTF-8 text: {relative}") from exc
        if len(original.encode("utf-8")) > MAX_FILE_BYTES:
            raise PatchError(f"Patch target exceeds the 1 MB safety limit: {relative}")
        updated = _apply_hunks(original, hunks, relative)
        diff = "".join(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
        )
        changes.append(FileChange(relative, original, updated, diff))

    return PatchPreview(tuple(changes))


def apply_patch(workspace: Path, preview: PatchPreview) -> tuple[str, ...]:
    """Atomically replace each validated file; restore earlier files if a write fails."""
    root = workspace.expanduser().resolve()
    targets: list[tuple[Path, FileChange, int]] = []
    for change in preview.changes:
        target = _resolve_workspace_file(root, change.path)
        with target.open("r", encoding="utf-8", newline="") as handle:
            current = handle.read(MAX_FILE_BYTES + 1)
        if current != change.original:
            raise PatchError(
                f"{change.path} changed after preview. Generate a fresh preview before applying."
            )
        targets.append((target, change, stat.S_IMODE(target.stat().st_mode)))

    applied: list[tuple[Path, str, int]] = []
    try:
        for target, change, mode in targets:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".codemind-", suffix=".tmp", dir=target.parent
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
                    handle.write(change.updated)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(temporary, mode)
                os.replace(temporary, target)
                applied.append((target, change.original, mode))
            finally:
                if temporary.exists():
                    temporary.unlink()
    except OSError as exc:
        rollback_errors: list[str] = []
        for target, original, mode in reversed(applied):
            try:
                descriptor, temporary_name = tempfile.mkstemp(
                    prefix=".codemind-rollback-", suffix=".tmp", dir=target.parent
                )
                temporary = Path(temporary_name)
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
                    handle.write(original)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(temporary, mode)
                os.replace(temporary, target)
            except OSError as rollback_exc:
                rollback_errors.append(f"{target.name}: {rollback_exc}")
        if rollback_errors:
            raise RuntimeError(
                "Patch write failed and rollback was incomplete: " + "; ".join(rollback_errors)
            ) from exc
        raise RuntimeError(f"Patch could not be written; previous files were restored: {exc}") from exc

    return tuple(change.path for change in preview.changes)
