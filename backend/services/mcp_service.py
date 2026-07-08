"""MCP service — safe management of MCP server configurations.

Uses ``settings_service`` for persistence and applies security checks
(secret detection, risky command detection) before writes.

MCP servers are stored in:
- Global: ~/.claude.json (mcpServers key)
- Project: <project>/.mcp.json (mcpServers key)
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


def _serialize_mcp_config(config: McpServerConfig) -> dict:
    """Serialize MCP config to dict, excluding empty/None values.

    For HTTP/SSE MCPs: only include url and type
    For STDIO MCPs: include command, args, env
    """
    result = {}

    # HTTP/SSE transport - use 'type' field
    if config.transport in ("http", "sse") and config.url:
        result["type"] = config.transport
        result["url"] = config.url
        return result

    # STDIO transport
    if config.command:
        result["command"] = config.command
        if config.args:
            result["args"] = config.args
        if config.env:
            result["env"] = config.env
        return result

    # Fallback: include url with type if available
    if config.url:
        result["url"] = config.url
        if config.transport:
            result["type"] = config.transport
    elif config.command:
        result["command"] = config.command
        if config.args:
            result["args"] = config.args
        if config.env:
            result["env"] = config.env

    return result


# ---------------------------------------------------------------------------
# Read / list
# ---------------------------------------------------------------------------

async def list_servers(scope: str) -> List[McpServerResponse]:
    """Return all configured MCP servers for *scope*."""
    # Read from MCP-specific config files
    settings = await settings_service.get_mcp_settings(scope)
    servers_raw: dict = settings.get("mcpServers", {})

    other_scope = _other_scope(scope)
    other_settings = await settings_service.get_mcp_settings(other_scope)
    other_names: set = set(other_settings.get("mcpServers", {}).keys())

    result: List[McpServerResponse] = []
    for name, cfg in servers_raw.items():
        if not isinstance(cfg, dict):
            continue
        # Support both 'transport' and 'type' fields
        transport = cfg.get("transport") or cfg.get("type")
        config = McpServerConfig(
            command=cfg.get("command", ""),
            args=cfg.get("args", []),
            env=cfg.get("env", {}),
            url=cfg.get("url"),
            transport=transport,
        )
        overridden = {"scope": other_scope, "name": name} if name in other_names else None
        source = ".mcp.json" if scope == "project" else "~/.claude.json"
        result.append(
            McpServerResponse(
                name=name,
                config=config,
                scope=scope,
                active=True,
                overridden=overridden,
                source=source,
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
    # Security: detect risky commands and secrets (only for stdio)
    if config.command:
        risky = detect_risky_command(config.command)
        if risky:
            logger.warning("Risky command for MCP %s: %s", name, risky)

    secret_w = detect_secrets(_serialize_mcp_config(config))
    if secret_w:
        logger.warning("Secret warnings for MCP %s: %s", name, secret_w)

    # Read from MCP-specific config files
    settings = await settings_service.get_mcp_settings(scope)
    servers: dict = settings.get("mcpServers", {})
    if name in servers:
        raise ValueError(f"MCP server '{name}' already exists in {scope} scope")

    servers[name] = _serialize_mcp_config(config)
    await settings_service.patch_mcp_servers(scope, servers)

    source = ".mcp.json" if scope == "project" else "~/.claude.json"
    return McpServerResponse(
        name=name,
        config=config,
        scope=scope,
        active=True,
        source=source,
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
    settings = await settings_service.get_mcp_settings(scope)
    servers = settings.get("mcpServers", {})
    if name not in servers:
        return None

    if config.command:
        risky = detect_risky_command(config.command)
        if risky:
            logger.warning("Risky command for MCP %s: %s", name, risky)

    servers[name] = _serialize_mcp_config(config)
    await settings_service.patch_mcp_servers(scope, servers)

    source = ".mcp.json" if scope == "project" else "~/.claude.json"
    return McpServerResponse(
        name=name,
        config=config,
        scope=scope,
        active=True,
        source=source,
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def delete_server(name: str, scope: str) -> bool:
    """Remove an MCP server from settings."""
    settings = await settings_service.get_mcp_settings(scope)
    servers = settings.get("mcpServers", {})
    if name not in servers:
        return False

    del servers[name]
    await settings_service.patch_mcp_servers(scope, servers)

    return True


# ---------------------------------------------------------------------------
# Connectivity test
# ---------------------------------------------------------------------------

async def test_connectivity(name: str, scope: str) -> ConnectivityResult:
    """Test MCP server connectivity.

    For HTTP/SSE: send a simple HTTP request to the URL
    For STDIO: briefly launch the server and check if it responds
    """
    settings = await settings_service.get_mcp_settings(scope)
    servers = settings.get("mcpServers", {})
    if name not in servers:
        return ConnectivityResult(name=name, status="error", message="Server not found")

    cfg_data = servers[name]
    if not isinstance(cfg_data, dict):
        return ConnectivityResult(name=name, status="error", message="Invalid config")

    # Check transport type
    transport = cfg_data.get("transport") or cfg_data.get("type")
    url = cfg_data.get("url")

    # HTTP/SSE MCP - test via HTTP request
    if transport in ("http", "sse") and url:
        return await _test_http_mcp(name, url)

    # STDIO MCP - test by launching process
    command = cfg_data.get("command", "")
    if not command:
        return ConnectivityResult(name=name, status="error", message="No command specified")

    args = cfg_data.get("args", [])
    env = cfg_data.get("env", {})

    return await _test_stdio_mcp(name, command, args, env)


async def _test_http_mcp(name: str, url: str) -> ConnectivityResult:
    """Test HTTP MCP server by sending a request."""
    start_time = time.monotonic()
    try:
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            # Try to connect to the MCP endpoint
            async with session.get(url) as resp:
                elapsed = time.monotonic() - start_time
                if resp.status == 200:
                    return ConnectivityResult(
                        name=name,
                        status="connected",
                        message="HTTP server responded successfully",
                        latency=round(elapsed * 1000, 2),
                    )
                else:
                    return ConnectivityResult(
                        name=name,
                        status="error",
                        message=f"HTTP server returned status {resp.status}",
                        latency=round(elapsed * 1000, 2),
                    )
    except ImportError:
        # Fallback to basic socket check if aiohttp not available
        import socket
        try:
            # Parse URL to get host and port
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 80

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            elapsed = time.monotonic() - start_time
            sock.close()

            if result == 0:
                return ConnectivityResult(
                    name=name,
                    status="connected",
                    message="HTTP server port is open",
                    latency=round(elapsed * 1000, 2),
                )
            else:
                return ConnectivityResult(
                    name=name,
                    status="error",
                    message=f"Cannot connect to {host}:{port}",
                    latency=round(elapsed * 1000, 2),
                )
        except Exception as exc:
            elapsed = time.monotonic() - start_time
            return ConnectivityResult(
                name=name,
                status="error",
                message=str(exc),
                latency=round(elapsed * 1000, 2),
            )
    except Exception as exc:
        elapsed = time.monotonic() - start_time
        return ConnectivityResult(
            name=name,
            status="error",
            message=str(exc),
            latency=round(elapsed * 1000, 2),
        )


async def _test_stdio_mcp(name: str, command: str, args: list, env: dict) -> ConnectivityResult:
    """Test STDIO MCP server by launching it briefly."""
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
        stderr_msg = stderr_bytes.decode("utf-8", errors="replace").strip()[:500]
        error_msg = f"Exited with code {proc.returncode}"
        if stderr_msg:
            error_msg = f"{error_msg}: {stderr_msg}"
        return ConnectivityResult(
            name=name, status="error",
            message=error_msg,
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
    proj_settings = await settings_service.get_mcp_settings("project")
    glob_settings = await settings_service.get_mcp_settings("global")

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