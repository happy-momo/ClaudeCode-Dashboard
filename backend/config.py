"""Configuration module.

Delegates path resolution to core.paths when the package is importable,
but provides the same symbols directly when run as ``__main__``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend directory is on sys.path for absolute imports
_backend_dir = Path(__file__).parent.resolve()
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

try:
    # Package import (e.g. ``from backend.config import ...``)
    from .paths import (
        API_PREFIX,
        DEFAULT_HOST,
        DEFAULT_PORT,
        ensure_directories,
        get_config_path,
        get_mcp_config_path,
        get_conversations_dir,
        get_global_config_path,
        get_global_mcp_config_path,
        get_project_config_path,
        get_project_mcp_config_path,
        get_stats_dir,
    )
except ImportError:
    # Standalone import (e.g. running ``python config.py`` or when parent is not on path)
    from core.paths import (
        API_PREFIX,
        DEFAULT_HOST,
        DEFAULT_PORT,
        ensure_directories,
        get_config_path,
        get_mcp_config_path,
        get_conversations_dir,
        get_global_config_path,
        get_global_mcp_config_path,
        get_project_config_path,
        get_project_mcp_config_path,
        get_stats_dir,
    )

__all__ = [
    "API_PREFIX",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "ensure_directories",
    "get_config_path",
    "get_mcp_config_path",
    "get_conversations_dir",
    "get_global_config_path",
    "get_global_mcp_config_path",
    "get_project_config_path",
    "get_project_mcp_config_path",
    "get_stats_dir",
]
