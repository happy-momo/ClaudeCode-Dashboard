"""Claude Dashboard Backend - Main Entry Point

Starts FastAPI HTTP server (for frontend panel + REST API) and can optionally
run alongside an MCP server for Claude Code integration.

Usage:
    python main.py              # Start HTTP server on default port
    python main.py --port 8080  # Start on custom port
    python main.py --mcp        # Start both HTTP and MCP servers
"""

import asyncio
import os
import socket
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import DEFAULT_HOST, DEFAULT_PORT, ensure_directories
from api.router import api_router


def find_available_port(start_port: int, host: str = "127.0.0.1") -> int:
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


# NOTE: Port is determined lazily at startup time, not at import time.
# This prevents port conflicts when main.py is imported by uvicorn
# (which happens when mcp-server.py starts the HTTP server).
# The actual port is stored in the app.state.port after startup.


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    # Register global exception handlers on startup
    from core.errors import register_exception_handlers
    register_exception_handlers(app)
    ensure_directories()

    # Determine the actual port from the running server
    port = getattr(app.state, 'port', DEFAULT_PORT)
    host = getattr(app.state, 'host', DEFAULT_HOST)
    print(f"Claude Dashboard backend starting on http://{host}:{port}")
    print(f"API docs available at http://{host}:{port}/docs")
    yield
    print("Claude Dashboard backend shutting down")


app = FastAPI(
    title="Claude Dashboard API",
    description="Management dashboard for Claude Code - config, stats, and history",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for development (frontend dev server on various ports)
# Use broad patterns since the exact port is determined at runtime
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:18080",
        "http://localhost:18080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes FIRST (so they take priority)
app.include_router(api_router)

# Settings router (new) — mount under api_router to keep consistent prefix
from api.settings import router as settings_router
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])

# Discovery router (read-only resource discovery)
from api.discovery import router as discovery_router
api_router.include_router(discovery_router, prefix="/discovery", tags=["discovery"])

# Managed router (read-only managed settings)
from api.managed import router as managed_router
api_router.include_router(managed_router, prefix="/managed", tags=["managed"])

# Claude CLI router (status and debug)
from api.claude_cli import router as claude_cli_router
api_router.include_router(claude_cli_router, prefix="/claude", tags=["claude_cli"])


# SPA fallback middleware for frontend static files
# This runs AFTER routing, so API routes are handled normally.
# Only unmatched routes fall through to this middleware.
static_dir = Path(__file__).parent / "static"


class SPAMiddleware(BaseHTTPMiddleware):
    """Middleware that serves the SPA for non-API routes."""

    # Map file extensions to MIME types (covers all frontend asset types)
    _MIME_TYPES = {
        ".html": "text/html",
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".css": "text/css",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".eot": "application/vnd.ms-fontobject",
        ".webp": "image/webp",
        ".webm": "video/webm",
        ".wasm": "application/wasm",
        ".map": "application/json",
    }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # If the route was handled (not 404), return the response as-is
        if response.status_code != 404:
            return response

        # Only serve SPA for GET requests
        if request.method != "GET":
            return response

        path = request.url.path

        # Don't serve SPA for API routes
        if path.startswith("/api/"):
            return response

        # Serve static files if they exist
        if static_dir.exists():
            file_path = static_dir / path.lstrip("/")
            if file_path.exists() and file_path.is_file():
                # Determine MIME type from file extension
                suffix = file_path.suffix.lower()
                media_type = self._MIME_TYPES.get(suffix, "application/octet-stream")
                return FileResponse(str(file_path), media_type=media_type)

            # SPA fallback: serve index.html for all other routes
            index_path = static_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path), media_type="text/html")

        return response


# Only add SPA middleware if static files exist
# All static files (including /assets/) are served by SPAMiddleware
# with correct MIME types. Do NOT use StaticFiles mount — it may
# return incorrect MIME types (e.g. text/plain for .js files).
if static_dir.exists() and any(f for f in static_dir.iterdir() if f.name != '.gitkeep'):
    app.add_middleware(SPAMiddleware)


async def run_mcp_server():
    """Run MCP server via stdio in the same process."""
    try:
        from mcp_tools.tools import mcp
        # Run the MCP server via stdio
        await mcp.run_stdio_async()
    except ImportError as e:
        print(f"Warning: MCP tools not available: {e}")
        print("MCP server will not start. HTTP server will continue running.")
    except Exception as e:
        print(f"MCP server error: {e}")


async def run_http_and_mcp(host: str, port: int):
    """Run both HTTP and MCP servers concurrently."""
    # Create tasks for both servers
    http_task = asyncio.create_task(
        asyncio.to_thread(
            uvicorn.run,
            "main:app",
            host=host,
            port=port,
            reload=False,
            log_level="info",
        )
    )

    mcp_task = asyncio.create_task(run_mcp_server())

    # Run both tasks concurrently
    await asyncio.gather(http_task, mcp_task)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Claude Dashboard Backend")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    parser.add_argument("--mcp", action="store_true", help="Start MCP server alongside HTTP server")
    args = parser.parse_args()

    port = args.port or find_available_port(DEFAULT_PORT, args.host)

    # Store port info for the lifespan handler
    app.state.port = port
    app.state.host = args.host

    if args.mcp:
        # Run both HTTP and MCP servers
        print("Starting HTTP + MCP dual-server mode...")
        asyncio.run(run_http_and_mcp(args.host, port))
    else:
        # Run only HTTP server (default mode)
        uvicorn.run(
            "main:app",
            host=args.host,
            port=port,
            reload=False,
            log_level="info",
        )
