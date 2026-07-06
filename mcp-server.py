#!/usr/bin/env python3
"""MCP Server Entry Point for Claude Dashboard.

This script is called by Claude Code when the plugin is loaded.
It starts both the HTTP backend server (for the web dashboard) and
the MCP stdio server (for Claude Code tool integration).

Architecture:
    ┌─────────────────────────────────────────────────────┐
    │  Claude Code (via .mcp.json)                        │
    │  starts this script as an MCP server via stdio      │
    └──────────────────────┬──────────────────────────────┘
                           │ stdio
    ┌──────────────────────▼──────────────────────────────┐
    │  mcp-server.py                                      │
    │  ┌─────────────────┐  ┌──────────────────────────┐  │
    │  │  HTTP Server    │  │  MCP Server (stdio)      │  │
    │  │  (subprocess)   │  │  (FastMCP)               │  │
    │  │  Port 18080     │  │  communicates via stdin/  │  │
    │  │                  │  │  stdout with Claude Code  │  │
    │  └─────────────────┘  └──────────────────────────┘  │
    └─────────────────────────────────────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────────────┐
    │  Browser (Frontend)                                 │
    │  http://127.0.0.1:18080/?session_id=xxx            │
    └─────────────────────────────────────────────────────┘

The HTTP server runs as a separate subprocess (python main.py) to avoid
event loop conflicts with the MCP stdio server. Both share the same
Python codebase but run in isolated processes.
"""

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Force UTF-8 for all Python IO (critical on Windows)
os.environ["PYTHONUTF8"] = "1"


def _find_available_port(start_port: int, host: str = "127.0.0.1") -> int:
    """Find an available port starting from start_port."""
    port = start_port
    while port < start_port + 100:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return port
        except OSError:
            port += 1
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + 100}")


def _start_http_subprocess(host: str, port: int) -> subprocess.Popen:
    """Start the HTTP server as a separate subprocess.

    Using a subprocess instead of a thread avoids asyncio event loop
    conflicts between uvicorn (HTTP) and MCP (stdio). The HTTP server
    gets its own process with its own event loop.
    """
    main_py = BACKEND_DIR / "main.py"
    cmd = [sys.executable, str(main_py), "--host", host, "--port", str(port)]

    # Start subprocess with output suppressed
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        # On Windows, create new process group so it doesn't die with parent
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    print(f"[Dashboard] HTTP server subprocess started (PID={proc.pid}) on http://{host}:{port}", file=sys.stderr)
    return proc


async def main():
    """Run the MCP server with HTTP backend.

    The HTTP server runs as a separate subprocess.
    The MCP server runs on the main process via stdio.
    """
    from config import DEFAULT_HOST, DEFAULT_PORT

    host = os.environ.get("CLAUDE_DASHBOARD_HOST", DEFAULT_HOST)
    preferred_port = int(os.environ.get("CLAUDE_DASHBOARD_PORT", str(DEFAULT_PORT)))

    # Find an available port
    port = _find_available_port(preferred_port, host)

    # Store the actual port so hooks and other components can discover it
    os.environ["CLAUDE_DASHBOARD_PORT"] = str(port)

    # Start HTTP server as a subprocess
    http_proc = _start_http_subprocess(host, port)

    # Wait for HTTP server to be ready
    import urllib.request
    import urllib.error
    for i in range(15):
        await asyncio.sleep(1)
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/v1/status",
                method="GET",
            )
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=2))
            print(f"[Dashboard] HTTP server ready after {i+1}s", file=sys.stderr)
            break
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            pass
    else:
        print("[Dashboard] Warning: HTTP server may not be ready yet", file=sys.stderr)

    # Start MCP server on stdio (this is the main loop)
    from mcp_tools.tools import mcp
    print("[Dashboard] MCP server starting on stdio", file=sys.stderr)

    try:
        await mcp.run_stdio_async()
    finally:
        # When MCP server stops (Claude Code exits), also stop the HTTP server
        print("[Dashboard] Shutting down HTTP server subprocess", file=sys.stderr)
        http_proc.terminate()
        try:
            http_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            http_proc.kill()


if __name__ == "__main__":
    asyncio.run(main())
