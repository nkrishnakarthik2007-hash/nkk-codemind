from pathlib import Path

from codemind.knowledge.library import KnowledgeLibrary


def test_add_and_search_text(tmp_path: Path) -> None:
    library = KnowledgeLibrary(tmp_path)
    item = library.add_text(
        "Python file guide",
        "user://python-guide",
        "Python can read a JSON file with the json module. Use json.load with a file handle.",
        tags=("python", "json"),
    )

    results = library.search("read JSON file", limit=3)

    assert item.item_id
    assert len(results) == 1
    assert results[0].item.title == "Python file guide"
    assert "json.load" in results[0].excerpt


def test_duplicate_content_does_not_duplicate_record(tmp_path: Path) -> None:
    library = KnowledgeLibrary(tmp_path)
    library.add_text("Guide", "source:a", "Reusable documentation text.")
    library.add_text("Guide updated title", "source:b", "Reusable documentation text.")

    assert len(library.list_items()) == 1


def test_add_file(tmp_path: Path) -> None:
    source = tmp_path / "notes.md"
    source.write_text("# Notes\nPython virtual environments isolate dependencies.", encoding="utf-8")

    library = KnowledgeLibrary(tmp_path / "library")
    library.add_file(source, tags=("python",))

    results = library.search("virtual environments")
    assert results
    assert results[0].item.source_type == "file"