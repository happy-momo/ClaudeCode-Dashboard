"""Conversation manager for reading Claude Code conversation records from ~/.claude/projects/"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiofiles

from config import get_global_config_path


def _get_local_datetime(timestamp: str) -> str:
    """Convert ISO timestamp to local datetime string.

    Converts UTC timestamp to local time for display.
    Format: YYYY-MM-DD HH:MM
    """
    try:
        # Parse UTC timestamp
        dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        # Convert to local time
        dt_local = dt_utc.astimezone()
        return dt_local.strftime("%Y-%m-%d %H:%M")
    except Exception:
        # Fallback to UTC date if conversion fails
        try:
            dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt_utc.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return timestamp[:16] if len(timestamp) >= 16 else timestamp


def get_projects_dir() -> Path:
    """Get the Claude projects directory (~/.claude/projects/)"""
    return get_global_config_path() / "projects"


def _project_name_to_dir(project_name: str) -> Path:
    """Convert project name to directory name (e.g., /home/user/project -> -home-user-project)"""
    return get_projects_dir() / project_name.replace("/", "-").lstrip("-")


def _get_all_project_dirs() -> List[Path]:
    """Get all project directories in ~/.claude/projects/"""
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        return []
    return [d for d in projects_dir.iterdir() if d.is_dir()]


def _extract_text_from_content(content: list) -> str:
    """Extract text from message content list."""
    texts = []
    for item in content:
        if isinstance(item, dict):
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif item.get("type") == "tool_use":
                tool_name = item.get("name", "unknown")
                texts.append(f"[Tool: {tool_name}]")
            elif item.get("type") == "tool_result":
                texts.append("[Tool Result]")
    return " ".join(texts)[:200]  # Truncate for display


def _get_display_title(user_message: dict) -> str:
    """Extract a display title from the first user message."""
    content = user_message.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content[:100]  # Truncate
    elif isinstance(content, list):
        return _extract_text_from_content(content)[:100]
    return "Untitled"


def _extract_project_folder(dir_name: str) -> str:
    """Extract the project folder name from the encoded directory name.

    Claude Code encodes project paths as directory names:
    - Windows: E:\\prj\\Claude-dashboard -> E--prj-Claude-dashboard
    - Linux: /home/user/my-project -> -home-user-my-project

    Strategy: remove the drive/root prefix, then strip the first path
    segment (parent directory like 'prj', 'home', 'Users'). The remaining
    string is the project path which may include parent dirs but gives
    a recognizable name for the user.

    Examples:
        E--prj-Claude-dashboard -> Claude-dashboard
        E--prj-wechat-game-wechat-word-memory -> wechat-game-wechat-word-memory
    """
    name = dir_name
    # Remove Windows drive prefix (e.g., "E--" from "E--prj-Claude-dashboard")
    name = re.sub(r'^[A-Za-z]--', '', name)
    # Remove leading dash (Linux absolute path encoding, e.g., "-home-...")
    name = name.lstrip('-')

    # Split by '-' — the first segment is a parent directory (prj, home, Users, etc.)
    # Everything after is the project path
    parts = name.split('-')
    if len(parts) > 1:
        return '-'.join(parts[1:])
    return name or dir_name


async def list_conversations() -> List[dict]:
    """List all conversations from all projects."""
    conversations = []

    for project_dir in _get_all_project_dirs():
        project_name = project_dir.name.replace("-", "/", 1).replace("-", "/", 1)
        # Try to reconstruct project path (rough approximation)

        # Find all session jsonl files
        for jsonl_file in project_dir.glob("*.jsonl"):
            try:
                session_id = jsonl_file.stem

                # Read the file to get more info
                first_user_msg = None
                last_timestamp = None
                total_tokens = {"input": 0, "output": 0}
                turn_count = 0

                async with aiofiles.open(jsonl_file, "r", encoding="utf-8") as f:
                    async for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_type = entry.get("type", "")

                            # Get timestamp
                            if "timestamp" in entry:
                                last_timestamp = entry["timestamp"]

                            # Count user messages for turns
                            if entry_type == "user" and not entry.get("isMeta"):
                                turn_count += 1
                                if first_user_msg is None:
                                    first_user_msg = entry

                            # Sum tokens from assistant messages
                            if entry_type == "assistant":
                                usage = entry.get("message", {}).get("usage", {})
                                total_tokens["input"] += usage.get("input_tokens", 0)
                                total_tokens["output"] += usage.get("output_tokens", 0)

                        except json.JSONDecodeError:
                            continue

                if first_user_msg:
                    title = _get_display_title(first_user_msg)
                else:
                    title = session_id[:8]

                # Parse timestamp to local time
                date_str = ""
                if last_timestamp:
                    date_str = _get_local_datetime(last_timestamp)

                conversations.append({
                    "id": session_id,
                    "title": title,
                    "date": date_str,
                    "tokens": total_tokens["input"] + total_tokens["output"],
                    "turns": turn_count,
                    "project": project_name,
                    "project_folder": _extract_project_folder(project_dir.name),
                    "file_path": str(jsonl_file),
                })

            except Exception:
                continue

    # Sort by date descending
    conversations.sort(key=lambda c: c["date"], reverse=True)
    return conversations


async def get_conversation(session_id: str) -> Optional[dict]:
    """Get full conversation detail for a session."""
    # Search for the session file in all projects
    for project_dir in _get_all_project_dirs():
        jsonl_file = project_dir / f"{session_id}.jsonl"
        if jsonl_file.exists():
            return await _parse_conversation_file(jsonl_file, session_id)
    return None


async def _parse_conversation_file(jsonl_file: Path, session_id: str) -> Optional[dict]:
    """Parse a conversation jsonl file."""
    messages = []
    total_tokens = {"input": 0, "output": 0}
    title = session_id
    first_user_msg = None
    last_timestamp = None

    async with aiofiles.open(jsonl_file, "r", encoding="utf-8") as f:
        async for line in f:
            try:
                entry = json.loads(line.strip())
                entry_type = entry.get("type", "")

                # Get timestamp
                if "timestamp" in entry:
                    last_timestamp = entry["timestamp"]

                # User messages
                if entry_type == "user" and not entry.get("isMeta"):
                    msg = entry.get("message", {})
                    content = msg.get("content", "")

                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list):
                        text = _extract_text_from_content(content)
                    else:
                        text = str(content)

                    # Convert timestamp to local time
                    raw_ts = entry.get("timestamp", "")
                    messages.append({
                        "role": "user",
                        "content": text,
                        "timestamp": _get_local_datetime(raw_ts) if raw_ts else "",
                        "tokens": 0,
                    })

                    if first_user_msg is None:
                        first_user_msg = entry

                # Assistant messages
                elif entry_type == "assistant":
                    msg = entry.get("message", {})
                    content = msg.get("content", [])
                    usage = msg.get("usage", {})

                    total_tokens["input"] += usage.get("input_tokens", 0)
                    total_tokens["output"] += usage.get("output_tokens", 0)

                    text = _extract_text_from_content(content) if isinstance(content, list) else str(content)

                    # Convert timestamp to local time
                    raw_ts = entry.get("timestamp", "")
                    messages.append({
                        "role": "assistant",
                        "content": text,
                        "timestamp": _get_local_datetime(raw_ts) if raw_ts else "",
                        "tokens": usage.get("output_tokens", 0),
                    })

            except json.JSONDecodeError:
                continue

    if first_user_msg:
        title = _get_display_title(first_user_msg)

    # Parse date to local time
    date_str = ""
    if last_timestamp:
        date_str = _get_local_datetime(last_timestamp)

    return {
        "id": session_id,
        "title": title,
        "date": date_str,
        "tokens": total_tokens["input"] + total_tokens["output"],
        "turns": len([m for m in messages if m["role"] == "user"]),
        "messages": messages,
    }


async def delete_conversation(session_id: str) -> bool:
    """Remove a conversation file. Returns True if deleted, False if not found."""
    for project_dir in _get_all_project_dirs():
        jsonl_file = project_dir / f"{session_id}.jsonl"
        if jsonl_file.exists():
            jsonl_file.unlink()
            return True
    return False


async def export_conversations(session_ids: List[str]) -> dict:
    """Package selected conversations as a JSON dict."""
    exported = {"conversations": [], "exported_at": datetime.now().isoformat()}

    if not session_ids:
        # Export all
        conv_list = await list_conversations()
        session_ids = [c["id"] for c in conv_list]

    for sid in session_ids:
        detail = await get_conversation(sid)
        if detail:
            exported["conversations"].append(detail)

    return exported


def get_current_session_transcript() -> Optional[Path]:
    """Get the transcript path for the current session from the sessions directory."""
    sessions_dir = get_global_config_path() / "sessions"
    if not sessions_dir.exists():
        return None

    # Find the current session (most recent or with matching PID)
    for session_file in sessions_dir.glob("*.json"):
        try:
            data = json.loads(session_file.read_text())
            session_id = data.get("sessionId")
            if session_id:
                # Find the corresponding jsonl in projects
                for project_dir in _get_all_project_dirs():
                    jsonl_file = project_dir / f"{session_id}.jsonl"
                    if jsonl_file.exists():
                        return jsonl_file
        except Exception:
            continue
    return None
