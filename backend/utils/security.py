"""Security helpers for Claude Code configuration operations.

Provides path-traversal detection, secret-in-data detection, risky-command
detection, and input sanitization.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from core.errors import PathTraversalError, InvalidResourceNameError, InvalidProjectRootError


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------

# Patterns that indicate path traversal or injection.
_TRAVERSAL_PATTERNS = [
    re.compile(r"\.\./"),          # ../
    re.compile(r"/\.\."),           # /..
    re.compile(r"^/"),              # absolute path
]

# Windows-style drive paths like C:\ or C:/
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[/\\]")


def validate_path_traversal(path: str) -> None:
    """Raise ``PathTraversalError`` if *path* tries to escape its base.

    Checks for:
      - ``../``  segments
      - Absolute paths
      - Windows drive-style paths
    """
    for pat in _TRAVERSAL_PATTERNS:
        if pat.search(path):
            raise PathTraversalError(
                details={"input": path, "pattern": pat.pattern},
                warnings=["Path traversal detected in input"],
            )
    if _WINDOWS_DRIVE_RE.search(path):
        raise PathTraversalError(
            details={"input": path},
            warnings=["Windows drive path detected"],
        )


def sanitize_skill_name(name: str) -> str:
    """Sanitize a skill / resource name.

    Strips dangerous characters and normalizes the name to a safe filesystem
    identifier.  Raises ``InvalidResourceNameError`` on unresolvable names.
    """
    # Remove path traversal sequences
    name = name.replace("..", "").replace("/", "").replace("\\", "")

    # Only allow alphanumeric, hyphens, underscores, dots
    name = re.sub(r"[^a-zA-Z0-9_.\-]", "_", name)
    name = name.strip(" _")

    if not name:
        raise InvalidResourceNameError(details={"input": name})

    return name[:128]  # reasonable max length


# ---------------------------------------------------------------------------
# Project root validation
# ---------------------------------------------------------------------------

def validate_project_root(path: str) -> Path:
    """Validate that *path* exists and is a directory.

    Raises ``InvalidProjectRootError`` otherwise.
    """
    p = Path(path).resolve()
    if not p.is_dir():
        raise InvalidProjectRootError(
            details={"path": str(p)},
            warnings=["projectRoot must be an existing directory"],
        )
    return p


# ---------------------------------------------------------------------------
# Secrets detection
# ---------------------------------------------------------------------------

# Keywords and prefixes that likely indicate a secret value.
_SECRET_PATTERNS = [
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"api_key", re.IGNORECASE),
    re.compile(r"apikey", re.IGNORECASE),
    re.compile(r"bearer", re.IGNORECASE),
    re.compile(r"^ghp_"),               # GitHub personal access token
    re.compile(r"^sk-"),                 # OpenAI / similar API key prefix
    re.compile(r"^xoxb-"),              # Slack bot token
]


def detect_secrets(data: Any) -> list[str]:
    """Scan *data* (dict or string) for suspected secrets.

    Returns a list of warning strings.  Empty list means no suspects found.
    """
    warnings: list[str] = []

    if isinstance(data, str):
        return _scan_string_for_secrets(data)

    if isinstance(data, dict):
        for key, value in data.items():
            # Flag keys that look like secret names
            for pat in _SECRET_PATTERNS:
                if pat.search(key):
                    warnings.append(
                        f"Key '{key}' looks like a secret — consider using "
                        f"an environment variable such as ${{{key.upper()}}}"
                    )
                    break
            # Flag string values that match known prefixes
            if isinstance(value, str) and value:
                for prefix in ("ghp_", "sk-", "xoxb-"):
                    if value.startswith(prefix):
                        warnings.append(
                            f"Value for key '{key}' starts with '{prefix}' — "
                            f"consider using an environment variable"
                        )
                        break

    return warnings


def _scan_string_for_secrets(text: str) -> list[str]:
    """Check if a raw string value looks like a secret prefix."""
    warnings: list[str] = []
    for prefix in ("ghp_", "sk-", "xoxb-"):
        if text.startswith(prefix):
            warnings.append(
                f"Value starts with '{prefix}' — consider using an "
                f"environment variable"
            )
            break
    return warnings


# ---------------------------------------------------------------------------
# Risky command detection
# ---------------------------------------------------------------------------

# Patterns that indicate a high-risk shell command.
_RISKY_PATTERNS = [
    re.compile(r"\brm\b.*\s+-[rf]", re.IGNORECASE),   # rm -rf, rm -f
    re.compile(r"\bsudo\b"),                           # sudo
    re.compile(r"\bcurl\s+.*\|\s*sh", re.IGNORECASE), # curl | sh
    re.compile(r"\bwget\s+.*\|\s*sh", re.IGNORECASE), # wget | sh
    re.compile(r"\bpowershell\s+-EncodedCommand", re.IGNORECASE),
    re.compile(r"\bcmd\s*/c\b", re.IGNORECASE),
    re.compile(r"\bbash\s+-c\b", re.IGNORECASE),
    re.compile(r"\bsh\s+-c\b", re.IGNORECASE),
    re.compile(r"\bfdisk\b"),
    re.compile(r"\bchmod\b.*\s+[0-7]{3,4}\b"),
    re.compile(r"\bchown\b"),
]


def detect_risky_command(command: str) -> list[str]:
    """Detect high-risk patterns in a shell *command* string.

    Returns a list of warning strings.  Empty means no risks detected.
    """
    warnings: list[str] = []
    for pat in _RISKY_PATTERNS:
        if pat.search(command):
            warnings.append(f"Risky command pattern detected: '{pat.pattern}'")
    return warnings
