"""Managed service — read-only access to organization-managed settings.

Managed settings are enforced by IT policy and cannot be modified by users.
Paths vary by platform:
  - macOS: /Library/Application Support/ClaudeCode/
  - Linux/WSL: /etc/claude-code/
  - Windows: C:\Program Files\ClaudeCode\
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Platform-specific paths
# ---------------------------------------------------------------------------

def _get_managed_base_dir() -> Optional[Path]:
    """Return the base directory for managed settings based on platform."""
    if sys.platform == "darwin":  # macOS
        base = Path("/Library/Application Support/ClaudeCode")
    elif sys.platform.startswith("linux"):
        base = Path("/etc/claude-code")
    elif sys.platform == "win32":
        base = Path(r"C:\Program Files\ClaudeCode")
    else:
        # WSL detection: if /etc/claude-code exists, use it
        linux_base = Path("/etc/claude-code")
        if linux_base.exists():
            base = linux_base
        else:
            return None

    if base.exists():
        return base
    return None


# ---------------------------------------------------------------------------
# Read managed settings
# ---------------------------------------------------------------------------

def get_managed_settings() -> Optional[Dict[str, Any]]:
    """Read managed-settings.json (read-only).

    Returns None if the file does not exist or cannot be read.
    """
    base = _get_managed_base_dir()
    if not base:
        return None

    settings_file = base / "managed-settings.json"
    if not settings_file.exists():
        return None

    try:
        return json.loads(settings_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read managed-settings.json: %s", exc)
        return None


def get_managed_mcp() -> Optional[Dict[str, Any]]:
    """Read managed-mcp.json (read-only).

    Returns None if the file does not exist or cannot be read.
    """
    base = _get_managed_base_dir()
    if not base:
        return None

    mcp_file = base / "managed-mcp.json"
    if not mcp_file.exists():
        return None

    try:
        return json.loads(mcp_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read managed-mcp.json: %s", exc)
        return None


def list_managed_settings_d() -> List[Dict[str, Any]]:
    """List additional managed settings from managed-settings.d/ directory.

    Each .json file in the directory is loaded and returned as a dict with
    '_source' key indicating the filename.
    """
    base = _get_managed_base_dir()
    if not base:
        return []

    settings_d = base / "managed-settings.d"
    if not settings_d.is_dir():
        return []

    result = []
    for entry in sorted(settings_d.iterdir()):
        if not entry.suffix == ".json":
            continue
        try:
            data = json.loads(entry.read_text(encoding="utf-8"))
            data["_source"] = entry.name
            result.append(data)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read %s: %s", entry, exc)

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_all_managed() -> Dict[str, Any]:
    """Aggregate all managed configuration (read-only).

    Returns a dict with:
      - settings: main managed settings
      - mcp: managed MCP servers
      - extra: list of additional settings from managed-settings.d/
      - editable: False (always read-only)
      - warnings: any issues encountered during loading
    """
    warnings = []

    settings = get_managed_settings()
    if settings is None:
        warnings.append("managed-settings.json not found or unreadable")
        settings = {}

    mcp = get_managed_mcp()
    if mcp is None:
        warnings.append("managed-mcp.json not found or unreadable")
        mcp = {}

    extra = list_managed_settings_d()

    return {
        "settings": settings,
        "mcp": mcp,
        "extra": extra,
        "editable": False,
        "source": "managed",
        "warnings": warnings,
    }
