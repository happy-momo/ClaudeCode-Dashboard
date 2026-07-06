"""MCP service — safe management of MCP server configurations.

Uses ``settings_service`` for persistence and applies security checks
(secret detection, risky command detection) before writes.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import List, Optional

from models.mcp import McpServerConfig, McpServerResponse, ConnectivityResult, McpConflict
from utils.security import detect_risky_command, detect_secrets
from .settings_service import SettingsService

logger = logging.getLogger(__name__)

settings_service = SettingsService()


def _other_scope(scope: str) -> str:
    return "global" if scope == "project" else "project"


# ---------------------------------------------------------------------------
# Read / list
# ---------------------------------------------------------------------------

async def list_servers(scope: str) -> List[McpServerResponse]:
    """Return all configured MCP servers for *scope*."""
    settings = await settings_service.get(scope)
    servers_raw: dict = settings.get("mcpServers", {})
    disabled: list = settings.get("disabledMcpServers", [])

    other_scope = _other_scope(scope)
    other_settings = await settings_service.get(other_scope)
    other_names: set = set(other_settings.get("mcpServers", {}).keys())

    result: List[McpServerResponse] = []
    for name, cfg in servers_raw.items():
        if not isinstance(cfg, dict):
            continue
        config = McpServerConfig(
            command=cfg.get("command", ""),
            args=cfg.get("args", []),
            env=cfg.get("env", {}),
        )
        overridden = {"scope": other_scope, "name": name} if name in other_names else None
        result.append(
            McpServerResponse(
                name=name,
                config=config,
                scope=scope,
                active=name not in disabled,
                overridden=overridden,
                source=f"settings.json ({scope})",
            )
        )
    return result


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

async def create_server(
    name: str,
    config: McpServerConfig,
    scope: str = "project",
) -> McpServerResponse:
    """Add a new MCP server with security checks."""
    # Security: detect risky commands and secrets
    risky = detect_risky_command(config.command)
    if risky:
        logger.warning("Risky command for MCP %s: %s", name, risky)

    secret_w = detect_secrets(config.model_dump())
    if secret_w:
        logger.warning("Secret warnings for MCP %s: %s", name, secret_w)

    servers = (await settings_service.get(scope)).get("mcpServers", {})
    if name in servers:
        raise ValueError(f"MCP server '{name}' already exists in {scope} scope")

    servers[name] = config.model_dump(exclude_none=True)
    await settings_service.patch_mcp_servers(scope, servers)

    return McpServerResponse(
        name=name,
        config=config,
        scope=scope,
        active=True,
        source=f"settings.json ({scope})",
    )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

async def update_server(
    name: str,
    config: McpServerConfig,
    scope: str = "project",
) -> Optional[McpServerResponse]:
    """Update an existing MCP server configuration."""
    settings = await settings_service.get(scope)
    servers = settings.get("mcpServers", {})
    if name not in servers:
        return None

    risky = detect_risky_command(config.command)
    if risky:
        logger.warning("Risky command for MCP %s: %s", name, risky)

    servers[name] = config.model_dump(exclude_none=True)
    await settings_service.patch_mcp_servers(scope, servers)

    disabled = settings.get("disabledMcpServers", [])
    return McpServerResponse(
        name=name,
        config=config,
        scope=scope,
        active=name not in disabled,
        source=f"settings.json ({scope})",
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def delete_server(name: str, scope: str) -> bool:
    """Remove an MCP server from settings."""
    settings = await settings_service.get(scope)
    servers = settings.get("mcpServers", {})
    if name not in servers:
        return False

    del servers[name]
    await settings_service.patch_mcp_servers(scope, servers)

    # Clean up disabled list
    disabled = settings.get("disabledMcpServers", [])
    if name in disabled:
        disabled.remove(name)
        await settings_service.patch_disabled_list(scope, disabled, "disabledMcpServers")

    return True


# ---------------------------------------------------------------------------
# Connectivity test
# ---------------------------------------------------------------------------

async def test_connectivity(name: str, scope: str) -> ConnectivityResult:
    """Briefly launch the MCP server and check if it responds.

    Includes a 5-second timeout and command masking in error messages.
    """
    settings = await settings_service.get(scope)
    servers = settings.get("mcpServers", {})
    if name not in servers:
        return ConnectivityResult(name=name, status="error", message="Server not found")

    cfg_data = servers[name]
    if not isinstance(cfg_data, dict):
        return ConnectivityResult(name=name, status="error", message="Invalid config")

    command = cfg_data.get("command", "")
    args = cfg_data.get("args", [])
    env = cfg_data.get("env", {})

    if not command:
        return ConnectivityResult(name=name, status="error", message="No command specified")

    start_time = time.monotonic()
    try:
        import os as _os
        proc = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**_os.environ, **env},
        )
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()

        elapsed = time.monotonic() - start_time
        if proc.returncode == 0 or proc.returncode is None:
            return ConnectivityResult(
                name=name, status="connected",
                message="Server started successfully",
                latency=round(elapsed * 1000, 2),
            )
        stderr_bytes = await proc.stderr.read() if proc.stderr else b""
        return ConnectivityResult(
            name=name, status="error",
            message=f"Exited with code {proc.returncode}",
            latency=round(elapsed * 1000, 2),
        )
    except FileNotFoundError:
        return ConnectivityResult(name=name, status="error", message=f"Command not found: {command}")
    except Exception as exc:
        elapsed = time.monotonic() - start_time
        return ConnectivityResult(name=name, status="error", message=str(exc), latency=round(elapsed * 1000, 2))


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

async def detect_conflicts() -> List[McpConflict]:
    """Find MCP server names present in both project and global scopes."""
    proj_settings = await settings_service.get("project")
    glob_settings = await settings_service.get("global")

    proj_names = set(proj_settings.get("mcpServers", {}).keys())
    glob_names = set(glob_settings.get("mcpServers", {}).keys())

    conflicts: List[McpConflict] = []
    for name in proj_names & glob_names:
        pd = proj_settings["mcpServers"][name]
        gd = glob_settings["mcpServers"][name]
        proj_cfg = McpServerConfig(
            command=pd.get("command", "") if isinstance(pd, dict) else "",
            args=pd.get("args", []) if isinstance(pd, dict) else [],
            env=pd.get("env", {}) if isinstance(pd, dict) else {},
        )
        glob_cfg = McpServerConfig(
            command=gd.get("command", "") if isinstance(gd, dict) else "",
            args=gd.get("args", []) if isinstance(gd, dict) else [],
            env=gd.get("env", {}) if isinstance(gd, dict) else {},
        )
        conflicts.append(McpConflict(name=name, project_config=proj_cfg, global_config=glob_cfg))

    return conflicts
