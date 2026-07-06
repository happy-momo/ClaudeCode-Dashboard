"""Session Registry - Manage all active Claude Code sessions.

This module provides a singleton registry that tracks all active Claude Code
sessions, allowing the dashboard to serve the correct project data based on
the session_id from the URL.
"""

import asyncio
import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List


@dataclass
class SessionInfo:
    """Information about an active Claude Code session."""
    session_id: str
    project_dir: str
    last_seen: float
    pid: Optional[int] = None


class SessionRegistry:
    """Singleton registry for managing active Claude Code sessions.

    Sessions are registered when a Claude Code CLI starts (via hook) and
    automatically expire after 5 minutes of inactivity.
    """

    _instance: Optional['SessionRegistry'] = None
    _initialized: bool = False

    def __new__(cls) -> 'SessionRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions: Dict[str, SessionInfo] = {}
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True

    async def register(
        self,
        session_id: str,
        project_dir: str,
        pid: Optional[int] = None
    ) -> None:
        """Register or update a session.

        Args:
            session_id: The Claude Code session ID
            project_dir: The project directory path
            pid: Optional process ID of the Claude Code process
        """
        async with self._lock:
            self._sessions[session_id] = SessionInfo(
                session_id=session_id,
                project_dir=project_dir,
                last_seen=time.time(),
                pid=pid
            )

    async def unregister(self, session_id: str) -> None:
        """Remove a session from the registry."""
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session info by session_id."""
        async with self._lock:
            self._cleanup_expired()
            return self._sessions.get(session_id)

    async def list_sessions(self) -> List[SessionInfo]:
        """List all active sessions."""
        async with self._lock:
            self._cleanup_expired()
            return list(self._sessions.values())

    async def get_session_by_project(self, project_dir: str) -> Optional[SessionInfo]:
        """Find a session by project directory."""
        async with self._lock:
            self._cleanup_expired()
            for info in self._sessions.values():
                if info.project_dir == project_dir:
                    return info
            return None

    def _cleanup_expired(self, timeout: float = 3600) -> None:
        """Remove sessions that haven't been seen in timeout seconds.

        Args:
            timeout: Seconds of inactivity before considering a session expired
                     Default: 3600 (1 hour) - increased from 300s to prevent
                     sessions from expiring during normal usage
        """
        now = time.time()
        expired = [
            sid for sid, info in self._sessions.items()
            if now - info.last_seen > timeout
        ]
        for sid in expired:
            del self._sessions[sid]


# Global singleton instance
registry = SessionRegistry()
