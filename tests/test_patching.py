from pathlib import Path

import pytest

from codemind.patching import PatchError, apply_patch, preview_patch

SIMPLE_PATCH = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
 def greet():
-    return "hi"
+    message = "hello"
+    return message
"""


def test_preview_does_not_modify_files(tmp_path: Path):
    source = tmp_path / "app.py"
    original = 'def greet():\n    return "hi"\n'
    source.write_text(original, encoding="utf-8")

    preview = preview_patch(tmp_path, SIMPLE_PATCH)

    assert preview.file_count == 1
    assert preview.changes[0].path == "app.py"
    assert '-    return "hi"' in preview.changes[0].diff
    assert '+    message = "hello"' in preview.changes[0].diff
    assert source.read_text(encoding="utf-8") == original


def test_apply_patch_updates_file_only_after_explicit_call(tmp_path: Path):
    source = tmp_path / "app.py"
    source.write_text('def greet():\n    return "hi"\n', encoding="utf-8")
    preview = preview_patch(tmp_path, SIMPLE_PATCH)

    changed = apply_patch(tmp_path, preview)

    assert changed == ("app.py",)
    assert source.read_text(encoding="utf-8") == (
        'def greet():\n    message = "hello"\n    return message\n'
    )


def test_rejects_path_traversal(tmp_path: Path):
    patch = """--- a/../outside.py
+++ b/../outside.py
@@ -1 +1 @@
-old
+new
"""
    with pytest.raises(PatchError, match="stay inside"):
        preview_patch(tmp_path, patch)


def test_rejects_new_files(tmp_path: Path):
    patch = """--- /dev/null
+++ b/new.py
@@ -0,0 +1 @@
+print("hello")
"""
    with pytest.raises(PatchError, match="New and deleted"):
        preview_patch(tmp_path, patch)


def test_rejects_symlink_targets(tmp_path: Path):
    real_file = tmp_path / "real.py"
    real_file.write_text("old\n", encoding="utf-8")
    link = tmp_path / "linked.py"
    try:
        link.symlink_to(real_file)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable on this platform")
    patch = """--- a/linked.py
+++ b/linked.py
@@ -1 +1 @@
-old
+new
"""
    with pytest.raises(PatchError, match="Symlinks"):
        preview_patch(tmp_path, patch)


def test_rejects_stale_patch_context(tmp_path: Path):
    (tmp_path / "app.py").write_text("something else\n", encoding="utf-8")
    with pytest.raises(PatchError, match="does not match"):
        preview_patch(tmp_path, SIMPLE_PATCH)


def test_apply_rechecks_file_after_preview(tmp_path: Path):
    source = tmp_path / "app.py"
    source.write_text('def greet():\n    return "hi"\n', encoding="utf-8")
    preview = preview_patch(tmp_path, SIMPLE_PATCH)
    source.write_text("changed by another process\n", encoding="utf-8")

    with pytest.raises(PatchError, match="changed after preview"):
        apply_patch(tmp_path, preview)


def test_rejects_duplicate_file_entries(tmp_path: Path):
    patch = SIMPLE_PATCH + SIMPLE_PATCH
    with pytest.raises(PatchError, match="same file more than once"):
        preview_patch(tmp_path, patch)



def test_cli_preview_is_read_only_by_default(tmp_path: Path, monkeypatch, capsys):
    from codemind.cli import main

    source = tmp_path / "app.py"
    original = 'def greet():\n    return "hi"\n'
    source.write_text(original, encoding="utf-8")
    patch_file = tmp_path / "change.patch"
    patch_file.write_text(SIMPLE_PATCH, encoding="utf-8")
    monkeypatch.setenv("CODEMIND_HOME", str(tmp_path / ".codemind"))

    exit_code = main([
        "apply-patch", str(patch_file), "--workspace", str(tmp_path)
    ])

    assert exit_code == 0
    assert source.read_text(encoding="utf-8") == original
    assert "Preview only: no files were changed" in capsys.readouterr().out


def test_cli_requires_apply_flag_to_write(tmp_path: Path, monkeypatch):
    from codemind.cli import main

    source = tmp_path / "app.py"
    source.write_text('def greet():\n    return "hi"\n', encoding="utf-8")
    patch_file = tmp_path / "change.patch"
    patch_file.write_text(SIMPLE_PATCH, encoding="utf-8")
    monkeypatch.setenv("CODEMIND_HOME", str(tmp_path / ".codemind"))

    exit_code = main([
        "apply-patch", str(patch_file), "--workspace", str(tmp_path), "--apply"
    ])

    assert exit_code == 0
    assert 'message = "hello"' in source.read_text(encoding="utf-8")


def test_rejects_secret_file_targets(tmp_path: Path):
    (tmp_path / ".env").write_text("TOKEN=not-for-patching\n", encoding="utf-8")
    patch = """--- a/.env
+++ b/.env
@@ -1 +1 @@
-TOKEN=not-for-patching
+TOKEN=changed
"""
    with pytest.raises(PatchError, match="Sensitive files"):
        preview_patch(tmp_path, patch)


def test_preserves_windows_crlf_line_endings(tmp_path: Path):
    source = tmp_path / "app.py"
    original = 'def greet():\\r\\n    return "hi"\\r\\n'
    source.write_bytes(original.encode("utf-8"))

    preview = preview_patch(tmp_path, SIMPLE_PATCH)
    apply_patch(tmp_path, preview)

    updated = source.read_bytes().decode("utf-8")
    assert updated == 'def greet():\\r\\n    message = "hello"\\r\\n    return message\\r\\n'
    assert "\\n" not in updated.replace("\\r\\n", "")
