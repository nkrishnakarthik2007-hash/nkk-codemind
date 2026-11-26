"""Privacy-conscious local diagnostics for CodeMind.

Only operational metadata is recorded. Prompts, model output, source code, and file
contents are deliberately never passed to the logger by the CLI.
"""

from __future__ import annotations

import json
import logging
import platform
import re
import zipfile
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from .knowledge.library import default_home

LOGGER_NAME = "codemind"
LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "codemind.jsonl"
MAX_LOG_BYTES = 512 * 1024
BACKUP_COUNT = 3

_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)(\s*[=:]\s*)[^\s,;]+"),
    re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(gh[pousr]_[A-Za-z0-9]{20,})"),
    re.compile(r"(?i)(sk-[A-Za-z0-9_-]{16,})"),
)


def diagnostics_dir(home: Path | None = None) -> Path:
    """Return the local diagnostics directory, creating it when needed."""
    root = (home or default_home()).expanduser()
    directory = root / LOG_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def redact_text(value: str) -> str:
    """Remove common credentials from text before it reaches a log or bundle."""
    cleaned = value
    for pattern in _SECRET_PATTERNS:
        if pattern.groups == 1:
            cleaned = pattern.sub("[REDACTED]", cleaned)
        else:
            cleaned = pattern.sub(r"\1\2[REDACTED]", cleaned)
    return cleaned


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "event": redact_text(record.getMessage())[:500],
        }
        if hasattr(record, "event_data"):
            payload["data"] = record.event_data
        if record.exc_info:
            payload["error_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def configure_logging(home: Path | None = None) -> Path:
    """Configure rotating JSONL logs and return the active log path."""
    directory = diagnostics_dir(home)
    log_path = directory / LOG_FILE_NAME
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    target = str(log_path.resolve())
    for existing in list(logger.handlers):
        if isinstance(existing, RotatingFileHandler) and str(Path(existing.baseFilename).resolve()) != target:
            logger.removeHandler(existing)
            existing.close()
    if not any(
        isinstance(handler, RotatingFileHandler)
        and str(Path(handler.baseFilename).resolve()) == target
        for handler in logger.handlers
    ):
        handler = RotatingFileHandler(
            log_path, maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
    return log_path


def record_event(event: str, **data: Any) -> None:
    """Record a small operational event; callers must not supply prompts or code."""
    safe_data = {
        str(key)[:60]: redact_text(str(value))[:200]
        for key, value in data.items()
        if key.lower() not in {"prompt", "output", "content", "source", "code", "path"}
        and not any(marker in key.lower() for marker in ("key", "token", "password", "secret", "auth", "credential"))
    }
    logging.getLogger(LOGGER_NAME).info(
        redact_text(event)[:120], extra={"event_data": safe_data}
    )


def create_support_bundle(destination: Path, home: Path | None = None) -> Path:
    """Create a shareable ZIP containing only app metadata and rotated logs."""
    root = (home or default_home()).expanduser()
    log_dir = root / LOG_DIR_NAME
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "app": "NKK CodeMind",
        "diagnostics_format": 1,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": "Contains operational event metadata only; no prompts or project files are collected.",
    }
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        if log_dir.exists():
            for log_file in sorted(log_dir.glob(f"{LOG_FILE_NAME}*")):
                if log_file.is_file():
                    archive.write(log_file, arcname=f"logs/{log_file.name}")
    return destination
