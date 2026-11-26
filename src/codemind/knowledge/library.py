"""Small disk-backed text knowledge library using only the Python standard library."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable


@dataclass(frozen=True)
class KnowledgeItem:
    item_id: str
    title: str
    source: str
    source_type: str
    tags: tuple[str, ...]
    content_hash: str
    created_at: float
    content_path: str


@dataclass(frozen=True)
class SearchResult:
    item: KnowledgeItem
    excerpt: str
    score: int


def default_home() -> Path:
    override = os.environ.get("CODEMIND_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codemind"


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-._")
    return cleaned[:72] or "document"


class KnowledgeLibrary:
    """Store source text on disk and lightweight metadata/search index in SQLite.

    The full document corpus is never loaded at startup. Search reads only metadata
    and matching files needed to make short excerpts.
    """

    def __init__(self, home: Path | None = None) -> None:
        self.home = (home or default_home()).expanduser().resolve()
        self.documents_dir = self.home / "documents"
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.home / "knowledge.sqlite3"
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge (
                    item_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    content_path TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
                USING fts5(item_id UNINDEXED, title, content, tags)
                """
            )

    def add_text(
        self,
        title: str,
        source: str,
        content: str,
        *,
        source_type: str = "user",
        tags: Iterable[str] = (),
    ) -> KnowledgeItem:
        text = content.strip()
        if not text:
            raise ValueError("Document content is empty.")
        if len(text.encode("utf-8")) > 5_000_000:
            raise ValueError("Document exceeds the 5 MB prototype limit.")

        clean_tags = tuple(sorted({tag.strip().lower() for tag in tags if tag.strip()}))
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        item_id = digest[:20]
        filename = f"{_safe_name(title)}-{item_id}.txt"
        destination = self.documents_dir / filename

        # Write the text before inserting metadata. A crash can leave an orphan file,
        # but cannot leave a database row pointing to a partially written document.
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(destination)

        item = KnowledgeItem(
            item_id=item_id,
            title=title.strip() or "Untitled",
            source=source,
            source_type=source_type,
            tags=clean_tags,
            content_hash=digest,
            created_at=time.time(),
            content_path=str(destination),
        )
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO knowledge
                (item_id, title, source, source_type, tags_json, content_hash, created_at, content_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    title=excluded.title, source=excluded.source,
                    source_type=excluded.source_type, tags_json=excluded.tags_json,
                    created_at=excluded.created_at, content_path=excluded.content_path
                """,
                (
                    item.item_id, item.title, item.source, item.source_type,
                    json.dumps(item.tags), item.content_hash, item.created_at, item.content_path,
                ),
            )
            db.execute("DELETE FROM knowledge_fts WHERE item_id = ?", (item.item_id,))
            db.execute(
                "INSERT INTO knowledge_fts(item_id, title, content, tags) VALUES (?, ?, ?, ?)",
                (item.item_id, item.title, text, " ".join(item.tags)),
            )
        return item

    def add_file(self, path: Path, *, tags: Iterable[str] = ()) -> KnowledgeItem:
        source_path = path.expanduser().resolve()
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        if source_path.stat().st_size > 5_000_000:
            raise ValueError("File exceeds the 5 MB prototype limit.")
        try:
            content = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Prototype currently supports UTF-8 text files only.") from exc
        return self.add_text(
            source_path.name, str(source_path), content, source_type="file", tags=tags
        )

    def search(self, query: str, *, limit: int = 5, excerpt_chars: int = 700) -> list[SearchResult]:
        terms = [term for term in re.findall(r"[\w.-]+", query.lower()) if len(term) > 1]
        if not terms:
            return []
        # FTS5's MATCH syntax has operators. Quote each user term to keep input as data.
        match_query = " OR ".join('"' + term.replace('"', '""') + '"' for term in terms)
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT k.*, bm25(knowledge_fts) AS rank
                FROM knowledge_fts
                JOIN knowledge k ON k.item_id = knowledge_fts.item_id
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (match_query, max(1, min(limit, 20))),
            ).fetchall()

        results: list[SearchResult] = []
        for row in rows:
            item = KnowledgeItem(
                item_id=row["item_id"],
                title=row["title"],
                source=row["source"],
                source_type=row["source_type"],
                tags=tuple(json.loads(row["tags_json"])),
                content_hash=row["content_hash"],
                created_at=row["created_at"],
                content_path=row["content_path"],
            )
            path = Path(item.content_path)
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8")
            excerpt = self._make_excerpt(content, terms, excerpt_chars)
            results.append(SearchResult(item=item, excerpt=excerpt, score=int(abs(row["rank"]) * 1000)))
        return results

    @staticmethod
    def _make_excerpt(content: str, terms: list[str], max_chars: int) -> str:
        lower = content.lower()
        positions = [lower.find(term) for term in terms if lower.find(term) >= 0]
        start = max(0, (min(positions) - max_chars // 4) if positions else 0)
        excerpt = content[start : start + max_chars].strip()
        if start:
            excerpt = "…" + excerpt
        if start + max_chars < len(content):
            excerpt += "…"
        return excerpt

    def list_items(self) -> list[KnowledgeItem]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM knowledge ORDER BY created_at DESC").fetchall()
        return [
            KnowledgeItem(
                item_id=row["item_id"], title=row["title"], source=row["source"],
                source_type=row["source_type"], tags=tuple(json.loads(row["tags_json"])),
                content_hash=row["content_hash"], created_at=row["created_at"],
                content_path=row["content_path"],
            )
            for row in rows
        ]