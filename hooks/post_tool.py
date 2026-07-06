#!/usr/bin/env python3
"""Hook: post_tool_use - Report tool input/output and calculate tool tokens"""

import json
import sys
import os
import urllib.request
import urllib.error


def _get_backend_port() -> int:
    """Get the backend server port."""
    return int(os.environ.get("CLAUDE_DASHBOARD_PORT", "18080"))


def main():
    try:
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}

        session_id = input_data.get("session_id", os.environ.get("CLAUDE_SESSION_ID", "unknown"))
        tool_input = input_data.get("tool_input", "")
        tool_output = input_data.get("tool_output", "")
        tool_name = input_data.get("tool_name", "")
        port = _get_backend_port()

        # Simple token estimation
        combined_text = str(tool_input) + str(tool_output)
        estimated_tokens = max(1, len(combined_text) // 4)

        payload = json.dumps({
            "session_id": session_id,
            "event_type": "post_tool",
            "tool_input": str(tool_input)[:10000],
            "tool_output": str(tool_output)[:10000],
            "tool_name": tool_name,
            "token_count": estimated_tokens,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }).encode("utf-8")

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/v1/stats/events",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                pass
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            pass

    except Exception:
        pass  # Never block the conversation

    # Always exit 0 — hooks must never block the session
    sys.exit(0)


if __name__ == "__main__":
    main()
