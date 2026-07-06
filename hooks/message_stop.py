#!/usr/bin/env python3.11
"""Hook: message_stop - Report output text and calculate output tokens"""

import json
import sys
import urllib.request
import os


def _get_backend_port() -> int:
    """Get the backend server port from environment."""
    return int(os.environ.get("CLAUDE_DASHBOARD_PORT", "18080"))


def main():
    try:
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}

        session_id = input_data.get("session_id", os.environ.get("CLAUDE_SESSION_ID", "unknown"))
        text = input_data.get("response", "")
        port = _get_backend_port()

        # Simple token estimation
        estimated_tokens = max(1, len(text) // 4)

        payload = json.dumps({
            "session_id": session_id,
            "event_type": "message_stop",
            "text": text[:10000],
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
        pass


if __name__ == "__main__":
    main()
