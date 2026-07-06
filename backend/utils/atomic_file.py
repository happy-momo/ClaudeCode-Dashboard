"""Safe atomic file operations for Claude Code configuration files.

All write operations use a write-then-replace strategy so that a crash mid-write
never corrupts the live configuration file.  Backup and JSON-patching utilities
are also provided.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level atomic write
# ---------------------------------------------------------------------------

def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write *content* to *path* atomically via temp file + rename.

    1. Creates a temporary file in the *same* directory as *path*.
    2. Writes *content* and flushes / fsyncs.
    3. Atomically renames (os.replace).
    4. Cleans up the temp file on failure.
    """
    path = Path(path)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)

    tmp_path = None
    try:
        # Same-dir temp file so os.replace is atomic on POSIX.
        fd, tmp_path = tempfile.mkstemp(dir=parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, str(path))
        except Exception:
            # If writing the fd fails, os.fdopen already closed it.
            raise
    except Exception:
        logger.exception("atomic_write_text failed for %s", path)
        # Cleanup temp file on failure.
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def atomic_write_json(path: Path, data: Any, indent: int = 2) -> None:
    """Write *data* as JSON to *path* atomically."""
    content = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    atomic_write_text(path, content)


# ---------------------------------------------------------------------------
# Safe read
# ---------------------------------------------------------------------------

def read_json_file(path: Path, default: Any = None) -> Any:
    """Read and parse a JSON file.

    Returns *default* (None) if the file does not exist, is empty, or is
    malformed JSON.
    """
    path = Path(path)
    if not path.exists():
        return default
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return default
        return json.loads(text)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("read_json_file failed for %s: %s", path, exc)
        return default


def read_text_file(path: Path, default: str = "") -> str:
    """Read a text file, returning *default* on failure."""
    path = Path(path)
    if not path.exists():
        return default
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return default


# ---------------------------------------------------------------------------
# JSON patch (keeps unknown fields)
# ---------------------------------------------------------------------------

def patch_json_file(
    path: Path,
    patch_func: Callable[[dict], dict],
    default_factory: Optional[Callable[[], dict]] = None,
) -> dict:
    """Atomically patch a JSON file.

    1. Reads the current content (or *default_factory*).
    2. Passes it to *patch_func* which must return the full updated dict.
    3. Writes atomically.

    This preserves fields not mentioned in the patch.
    """
    path = Path(path)
    existing = read_json_file(path, default=default_factory() if default_factory else None)
    if not isinstance(existing, dict):
        existing = default_factory() if default_factory else {}
    updated = patch_func(existing)
    atomic_write_json(path, updated)
    return updated


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

def create_backup(path: Path, suffix: Optional[str] = None) -> Path:
    """Create a timestamped backup of *path*.

    Returns the backup path.  Returns ``path`` if the source doesn't exist.
    """
    path = Path(path)
    if not path.exists():
        return path

    if suffix is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        suffix = f".backup.{ts}"

    backup = Path(f"{path}{suffix}")
    shutil.copy2(str(path), str(backup))
    logger.debug("Backed up %s -> %s", path, backup)
    return backup


# ---------------------------------------------------------------------------
# Markdown write (for SKILL.md)
# ---------------------------------------------------------------------------

def write_markdown(path: Path, content: str) -> None:
    """Write Markdown content to *path* atomically."""
    atomic_write_text(path, content, encoding="utf-8")
