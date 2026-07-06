"""Operation Planner — decides *how* each operation should be performed.

Instead of letting routers hard-code CLI vs file vs read-only, every
operation goes through ``OperationPlanner.plan()`` which returns a structured
``OperationPlan`` describing the chosen mode, risks, and side-effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class OperationPlan:
    """Blueprint for executing an operation.

    Produced by :class:`OperationPlanner`.
    """
    operation: str                      # e.g. "create", "update", "install"
    resource_type: str                  # e.g. "skill", "mcp_server", "plugin"
    target: str                         # identifier or path
    mode: str                           # "cli" | "file" | "readonly" | "unsupported"
    reason: str
    risk_level: str = "low"             # "low" | "medium" | "high"
    requires_restart: bool = False
    requires_reload_plugins: bool = False
    commands: list[str] = field(default_factory=list)
    files_to_read: list[str] = field(default_factory=list)
    files_to_write: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confirmation_required: bool = False


# ---------------------------------------------------------------------------
# Decision table
# ---------------------------------------------------------------------------

# (resource_type, scope) -> (mode, reason, risk_level, extra)
_MODE_RULES: dict[tuple[str, str], tuple[str, str, str, dict[str, Any]]] = {
    # Skills — always file ops
    ("skill", "project"): ("file", "Project skills live in project/.claude/skills/", "low", {}),
    ("skill", "global"):  ("file", "User skills live in ~/.claude/skills/",       "low", {}),
    ("skill", "user"):    ("file", "User skills live in ~/.claude/skills/",       "low", {}),
    ("skill", "plugin"):  ("readonly", "Plugin skills are managed by the plugin system", "low", {}),

    # MCP
    ("mcp_server", "project"):      ("file", "Project MCP configs are in .mcp.json",          "medium", {}),
    ("mcp_server", "user"):         ("cli",  "User MCP servers must be managed via CLI",      "medium", {}),
    ("mcp_server", "managed"):      ("readonly", "Managed MCP is enforced by org policy",      "low", {}),

    # Settings
    ("settings", "project"):        ("file", "Project settings are in project/.claude/",       "low", {}),
    ("settings", "local"):          ("file", "Local project settings in .claude/settings.local.json", "low", {}),
    ("settings", "user"):           ("file", "User settings in ~/.claude/settings.json",       "low", {}),
    ("settings", "managed"):        ("readonly", "Managed settings are enforced by policy",     "low", {}),
    ("settings", "internal"):       ("unsupported", "~/.claude.json is internal Claude state",  "high", {}),

    # Plugins
    ("plugin", "install"):          ("cli",  "Plugin installation via CLI",                    "medium", {}),
    ("plugin", "uninstall"):        ("cli",  "Plugin uninstall via CLI",                       "medium", {}),
    ("plugin", "enable"):           ("cli",  "Plugin enable via CLI",                          "medium", {}),
    ("plugin", "disable"):          ("cli",  "Plugin disable via CLI",                         "medium", {}),
    ("plugin", "move_scope"):       ("cli",  "Plugin scope migration via CLI",                 "medium", {}),

    # Cache / managed
    ("plugin_cache", "*"): ("readonly", "Plugin cache must not be modified directly", "low", {}),
    ("managed", "*"): ("readonly", "Managed resources are read-only", "low", {}),
}


class OperationPlanner:
    """Decides how each operation should be executed."""

    @classmethod
    def plan(
        cls,
        operation: str,
        resource_type: str,
        target: str,
        scope: Optional[str] = None,
    ) -> OperationPlan:
        """Create an OperationPlan for the given parameters.

        If scope is ``None`` it defaults to ``"project"``.
        """
        if scope is None:
            scope = "project"

        key = (resource_type, scope)
        # Try exact match first
        entry = _MODE_RULES.get(key)
        if entry is None:
            # Try matching on (resource_type, operation) — e.g. ("plugin", "install")
            op_key = (resource_type, operation)
            entry = _MODE_RULES.get(op_key)
        if entry is None:
            # Wildcard on resource_type
            wildcard = _MODE_RULES.get((resource_type, "*"))
            if wildcard:
                entry = wildcard
            else:
                entry = ("unsupported", f"No rule for {resource_type} in scope {scope}", "high", {})

        mode, reason, risk, extras = entry

        return OperationPlan(
            operation=operation,
            resource_type=resource_type,
            target=target,
            mode=mode,
            reason=reason,
            risk_level=risk,
            **extras,
        )
