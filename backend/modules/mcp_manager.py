"""MCP server manager for CRUD operations on MCP server configurations"""

import asyncio
import time
from typing import List, Optional

from models.mcp import McpServerConfig, McpServerResponse, ConnectivityResult, McpConflict
from modules.config_manager import (
    get_mcp_servers,
    set_mcp_servers,
    get_disabled_list,
    set_disabled_list,
)


def _other_scope(scope: str) -> str:
    """Get the opposite scope."""
    return "global" if scope == "project" else "project"


async def list_mcp_servers(scope: str) -> List[McpServerResponse]:
    """Get mcpServers from settings.json. Return list of McpServer objects.
    Check if disabled in settings. Mark items overridden by the other scope."""
    servers_raw = await get_mcp_servers(scope)
    disabled = await get_disabled_list(scope, "disabledMcpServers")
    other_scope = _other_scope(scope)
    other_servers_raw = await get_mcp_servers(other_scope)
    other_names = set(other_servers_raw.keys())

    result: List[McpServerResponse] = []
    for name, config_data in servers_raw.items():
        if isinstance(config_data, dict):
            config = McpServerConfig(
                command=config_data.get("command", ""),
                args=config_data.get("args", []),
                env=config_data.get("env", {}),
            )
        else:
            continue

        overridden = None
        if name in other_names:
            overridden = {"scope": other_scope, "name": name}

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


async def add_mcp_server(
    name: str, command: str, args: Optional[list] = None, env: Optional[dict] = None, scope: str = "project"
) -> McpServerResponse:
    """Add a new MCP server to settings.json."""
    servers = await get_mcp_servers(scope)
    if name in servers:
        raise ValueError(f"MCP server '{name}' already exists in {scope} scope")

    config = McpServerConfig(command=command, args=args or [], env=env or {})
    servers[name] = config.model_dump(exclude_none=True)
    await set_mcp_servers(scope, servers)

    return McpServerResponse(
        name=name,
        config=config,
        scope=scope,
        active=True,
        source=f"settings.json ({scope})",
    )


async def remove_mcp_server(name: str, scope: str) -> bool:
    """Remove an MCP server from settings.json. Returns True if removed."""
    servers = await get_mcp_servers(scope)
    if name not in servers:
        return False

    del servers[name]
    await set_mcp_servers(scope, servers)

    # Also remove from disabled list if present
    disabled = await get_disabled_list(scope, "disabledMcpServers")
    if name in disabled:
        disabled.remove(name)
        await set_disabled_list(scope, disabled, "disabledMcpServers")

    return True


async def test_connectivity(name: str, scope: str) -> ConnectivityResult:
    """Try to run the server command briefly, check if it responds.
    Returns ConnectivityResult with status and latency."""
    servers = await get_mcp_servers(scope)
    if name not in servers:
        return ConnectivityResult(name=name, status="error", message=f"Server '{name}' not found")

    config_data = servers[name]
    if not isinstance(config_data, dict):
        return ConnectivityResult(name=name, status="error", message="Invalid server config")

    command = config_data.get("command", "")
    args = config_data.get("args", [])
    env = config_data.get("env", {})

    if not command:
        return ConnectivityResult(name=name, status="error", message="No command specified")

    start_time = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**__import__("os").environ, **env},
        )

        # Give the server 5 seconds to start
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            # Process is still running, which is good for a server
            proc.kill()
            await proc.wait()

        elapsed = time.monotonic() - start_time

        if proc.returncode == 0 or proc.returncode is None:
            return ConnectivityResult(
                name=name,
                status="connected",
                message="Server started successfully",
                latency=round(elapsed * 1000, 2),
            )
        else:
            stderr = ""
            if proc.stderr:
                stderr_bytes = await proc.stderr.read()
                stderr = stderr_bytes.decode("utf-8", errors="replace")[:200]
            return ConnectivityResult(
                name=name,
                status="error",
                message=f"Server exited with code {proc.returncode}: {stderr}",
                latency=round(elapsed * 1000, 2),
            )
    except FileNotFoundError:
        return ConnectivityResult(
            name=name, status="error", message=f"Command not found: {command}"
        )
    except Exception as e:
        elapsed = time.monotonic() - start_time
        return ConnectivityResult(
            name=name,
            status="error",
            message=str(e),
            latency=round(elapsed * 1000, 2),
        )


async def detect_conflicts() -> List[McpConflict]:
    """Find MCP server names that exist in both project and global scope."""
    project_servers = await get_mcp_servers("project")
    global_servers = await get_mcp_servers("global")

    conflicts: List[McpConflict] = []
    for name in set(project_servers.keys()) & set(global_servers.keys()):
        proj_data = project_servers[name]
        glob_data = global_servers[name]

        proj_config = McpServerConfig(
            command=proj_data.get("command", "") if isinstance(proj_data, dict) else "",
            args=proj_data.get("args", []) if isinstance(proj_data, dict) else [],
            env=proj_data.get("env", {}) if isinstance(proj_data, dict) else {},
        )
        glob_config = McpServerConfig(
            command=glob_data.get("command", "") if isinstance(glob_data, dict) else "",
            args=glob_data.get("args", []) if isinstance(glob_data, dict) else [],
            env=glob_data.get("env", {}) if isinstance(glob_data, dict) else {},
        )

        conflicts.append(
            McpConflict(name=name, project_config=proj_config, global_config=glob_config)
        )

    return conflicts
