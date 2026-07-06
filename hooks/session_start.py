#!/usr/bin/env python3
"""Hook: session_start - Register session and output Dashboard link.

This hook is triggered when a Claude Code session starts. It:
1. Checks if the backend HTTP server is running
2. If not running, starts it as a background subprocess
3. Waits for the backend to be ready
4. Registers the current session with the backend
5. Outputs a dashboard link as a structured JSON hook response

The backend HTTP server can be started by:
- This hook (if not already running)
- mcp-server.py (MCP server defined in .mcp.json)

This hook will start the backend if needed, then wait for it to be ready.
"""

import json
import sys
import os
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path


def _find_project_root() -> str:
    """Find the project root directory."""
    current = Path.cwd()

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return project_dir

    for parent in [current] + list(current.parents):
        if (parent / "CLAUDE.md").exists() or (parent / ".claude").is_dir():
            if parent.name == "backend":
                return str(parent.parent)
            return str(parent)

    return str(current)


def _get_backend_port() -> int:
    """Get the backend server port."""
    return int(os.environ.get("CLAUDE_DASHBOARD_PORT", "18080"))


def _get_plugin_root() -> Path:
    """Get the plugin root directory."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        return Path(plugin_root)
    # Fallback: use current directory
    return Path.cwd()


def _start_backend(port: int) -> bool:
    """Start the backend HTTP server as a background subprocess.

    Returns True if started successfully, False otherwise.
    """
    try:
        plugin_root = _get_plugin_root()
        main_py = plugin_root / "backend" / "main.py"

        if not main_py.exists():
            print(f"[Dashboard] main.py not found at {main_py}", file=sys.stderr)
            return False

        # Log file for debugging
        log_file = plugin_root / "backend-startup.log"

        # Find Python 3.11 interpreter (required for backend)
        # Try python3.11 first, then fall back to python3
        python_cmd = "python3.11"
        try:
            subprocess.run([python_cmd, "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            python_cmd = sys.executable  # Fall back to hook's Python

        # Start backend as background process
        # Use subprocess.Popen without waiting
        with open(log_file, "w") as log:
            subprocess.Popen(
                [python_cmd, str(main_py), "--port", str(port)],
                stdout=log,
                stderr=log,
                start_new_session=True,  # Detach from parent process
            )
        print(f"[Dashboard] Started backend server on port {port} (using {python_cmd})", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[Dashboard] Failed to start backend: {e}", file=sys.stderr)
        return False


def _check_backend(port: int) -> bool:
    """Quick check if backend is running (single attempt, 1s timeout)."""
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/v1/system/status",
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=1) as resp:
            return resp.status == 200
    except:
        return False


def _register_session(session_id: str, project_dir: str, port: int) -> bool:
    """Register the session with the backend (1s timeout)."""
    payload = json.dumps({
        "session_id": session_id,
        "project_dir": project_dir,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/v1/sessions/register",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=1) as resp:
            return resp.status == 200
    except:
        return False


def main():
    """Main hook entry point.

    Strategy:
    1. Check if backend is already running
    2. If not, start it as a background subprocess
    3. Wait for backend to be ready (up to 10 retries, 0.5s each)
    4. Register session and output dashboard link
    """
    try:
        # Read hook input from stdin
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}

        # Get session ID and project directory
        session_id = input_data.get("session_id", os.environ.get("CLAUDE_SESSION_ID", "unknown"))
        project_dir = _find_project_root()
        port = _get_backend_port()

        # Check if backend is already running
        backend_running = _check_backend(port)

        # If not running, start it
        if not backend_running:
            print(f"[Dashboard] Backend not running on port {port}, starting...", file=sys.stderr)
            _start_backend(port)

        # Wait for backend to be ready
        # 10 retries × 0.5s = 5s max wait time
        # Backend typically starts in 2-3s
        for i in range(10):
            if _check_backend(port):
                backend_running = True
                print(f"[Dashboard] Backend ready after {i+1} checks", file=sys.stderr)
                break
            time.sleep(0.5)

        # Register session (if backend is available)
        if backend_running:
            _register_session(session_id, project_dir, port)

        # Generate dashboard URL
        dashboard_url = f"http://127.0.0.1:{port}/?session_id={session_id}"

        # Truncate long paths for display
        display_project = project_dir
        if len(project_dir) > 55:
            display_project = "..." + project_dir[-52:]

        # Build the message shown to the user in the CLI
        context_lines = [
            "Claude Dashboard Ready",
            "",
            f"Open in your browser to view session data:",
            f"  {dashboard_url}",
            "",
            f"Project: {display_project}",
            f"Session: {session_id[:8]}...",
        ]

        context_message = "\n".join(context_lines)

        # Output structured JSON hook response
        # - additionalContext: injected into model context (shown to both model and user)
        # - systemMessage: also injected as system-level message
        # Use ensure_ascii=False to avoid surrogate pair issues with emoji
        response = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context_message,
            },
            "systemMessage": context_message,
        }
        print(json.dumps(response, ensure_ascii=False), flush=True)

    except Exception as e:
        # Never block the conversation - output error as structured JSON
        try:
            error_msg = f"[Dashboard Hook] Error: {e}"
            error_response = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": error_msg,
                },
                "systemMessage": error_msg,
            }
            print(json.dumps(error_response, ensure_ascii=False), flush=True)
        except:
            pass

    # Always exit 0 — hooks must never block the session
    sys.exit(0)


if __name__ == "__main__":
    main()
