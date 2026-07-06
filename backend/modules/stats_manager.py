"""Stats manager for token usage tracking - reads from Claude Code session files

Token Consumption Calculation:
==============================
Claude API charges for each request based on:
  input_tokens + output_tokens

For a conversation with N turns:
- Each request sends the ENTIRE conversation history (as input_tokens)
- Plus new user message
- Model generates output_tokens

So total consumption = Σ (input_tokens + output_tokens) for each request

This means conversation history IS counted multiple times, which is correct
because that's how Claude billing works - you pay to re-send context each time.

Deduplication Logic:
====================
When multiple Claude Code windows are open and /resume is used to restore conversations,
it may create duplicate records with the same message content. To prevent double-counting:

1. Scan all project jsonl files
2. Parse lines - keep only 'assistant' type records with usage data
3. Convert timestamps to local time for daily aggregation
4. Deduplicate by composite key: (message.id, uuid, sessionId)
5. Aggregate usage fields (input_tokens, output_tokens, tool_calls)
6. For tool_use: deduplicate by (tool_use.id, assistant_record_key)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Set, Tuple, Dict, Any

import aiofiles

from config import get_global_config_path
from models.stats import (
    ContextSegment,
    ContextWindow,
    UsageTimeSeriesPoint,
)


def get_projects_dir() -> Path:
    """Get the Claude projects directory (~/.claude/projects/)"""
    return get_global_config_path() / "projects"


def _get_all_project_dirs() -> List[Path]:
    """Get all project directories in ~/.claude/projects/"""
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        return []
    return [d for d in projects_dir.iterdir() if d.is_dir()]


async def _get_current_session_id() -> Optional[str]:
    """Get the current active session ID from sessions directory."""
    sessions_dir = get_global_config_path() / "sessions"
    if not sessions_dir.exists():
        return None

    for session_file in sessions_dir.glob("*.json"):
        try:
            data = json.loads(session_file.read_text())
            session_id = data.get("sessionId")
            if session_id:
                return session_id
        except Exception:
            continue
    return None


def _get_local_date_str(timestamp: str) -> str:
    """Convert ISO timestamp to local date string (YYYY-MM-DD)."""
    try:
        # Parse UTC timestamp
        dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        # Convert to local time
        dt_local = dt_utc.astimezone()
        return dt_local.strftime("%Y-%m-%d")
    except Exception:
        # Fallback to UTC date if conversion fails
        try:
            dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt_utc.strftime("%Y-%m-%d")
        except Exception:
            return None


def _extract_tool_uses(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract tool_use entries from an assistant message.

    Returns list of tool_use records with id and content.
    """
    tool_uses = []
    message = entry.get("message", {})
    content = message.get("content", [])

    if not isinstance(content, list):
        return tool_uses

    for item in content:
        if isinstance(item, dict) and item.get("type") == "tool_use":
            tool_uses.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "input": item.get("input"),
            })

    return tool_uses


async def _read_session_stats(session_file: Path) -> Dict[str, Any]:
    """Read token usage from a session jsonl file with deduplication.

    Returns stats based on ACTUAL API consumption:
    - total_input_tokens: Sum of all input_tokens (what was billed as input)
    - total_output_tokens: Sum of all output_tokens (what was billed as output)
    - tool_calls: Number of tool_use calls
    - last_request_input: The last input_tokens (current context size)

    Deduplication:
    - Records are deduplicated by (message.id, uuid, sessionId) composite key
    - This prevents double-counting when /resume creates duplicate entries
    - Tool uses are deduplicated by (tool_use.id, assistant_uuid)
    """
    stats = {
        "total_input_tokens": 0,  # Billed input consumption
        "total_output_tokens": 0,  # Billed output consumption
        "tool_calls": 0,
        "first_timestamp": None,
        "last_timestamp": None,
        "daily_stats": {},
        "last_request_input": 0,
        "request_count": 0,
    }

    # Track seen records for deduplication
    # Key: (message_id, uuid, session_id) - unique per assistant response
    seen_messages: Set[Tuple[str, str, str]] = set()

    # Track tool uses for deduplication
    # Key: (tool_use_id, assistant_uuid) - unique per tool invocation
    seen_tool_uses: Set[Tuple[str, str]] = set()

    # Extract session ID from filename
    session_id = session_file.stem

    try:
        async with aiofiles.open(session_file, "r", encoding="utf-8") as f:
            async for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_type = entry.get("type", "")

                    ts = entry.get("timestamp")
                    if ts:
                        if stats["first_timestamp"] is None:
                            stats["first_timestamp"] = ts
                        stats["last_timestamp"] = ts

                    if entry_type == "assistant":
                        msg = entry.get("message", {})
                        message_id = msg.get("id", "")
                        record_uuid = entry.get("uuid", "")

                        # Create composite key for deduplication
                        dedup_key = (message_id, record_uuid, session_id)

                        # Skip if we've already processed this exact record
                        if dedup_key in seen_messages:
                            continue
                        seen_messages.add(dedup_key)

                        usage = msg.get("usage", {})
                        input_tokens = usage.get("input_tokens", 0)
                        output_tokens = usage.get("output_tokens", 0)

                        if input_tokens > 0 or output_tokens > 0:
                            # Billable consumption: input + output
                            stats["total_input_tokens"] += input_tokens
                            stats["total_output_tokens"] += output_tokens
                            stats["request_count"] += 1

                        if input_tokens > 0:
                            stats["last_request_input"] = input_tokens

                        # Count and deduplicate tool uses
                        tool_uses = _extract_tool_uses(entry)
                        unique_tool_count = 0
                        for tool_use in tool_uses:
                            tool_use_id = tool_use.get("id")
                            if tool_use_id:
                                tool_dedup_key = (tool_use_id, record_uuid)
                                if tool_dedup_key not in seen_tool_uses:
                                    seen_tool_uses.add(tool_dedup_key)
                                    unique_tool_count += 1
                        stats["tool_calls"] += unique_tool_count

                        # Daily stats with local time conversion
                        if ts and (input_tokens > 0 or output_tokens > 0):
                            date_str = _get_local_date_str(ts)
                            if date_str:
                                if date_str not in stats["daily_stats"]:
                                    stats["daily_stats"][date_str] = {
                                        "input_tokens": 0,
                                        "output_tokens": 0,
                                        "tool_calls": 0,
                                    }
                                stats["daily_stats"][date_str]["input_tokens"] += input_tokens
                                stats["daily_stats"][date_str]["output_tokens"] += output_tokens
                                stats["daily_stats"][date_str]["tool_calls"] += unique_tool_count

                except json.JSONDecodeError:
                    continue

    except OSError:
        pass

    return stats


async def _get_all_session_stats() -> List[Dict[str, Any]]:
    """Get stats from all session files."""
    all_stats = []

    for project_dir in _get_all_project_dirs():
        for jsonl_file in project_dir.glob("*.jsonl"):
            stats = await _read_session_stats(jsonl_file)
            stats["session_id"] = jsonl_file.stem
            stats["project"] = project_dir.name
            stats["file_path"] = str(jsonl_file)
            all_stats.append(stats)

    return all_stats


async def get_context_window(session_id: str = "default") -> ContextWindow:
    """Get context window usage for a specific session.

    Returns BILLABLE token consumption:
    - used: current context size (last input_tokens)
    - input_tokens: total billed input tokens across all requests
    - output_tokens: total billed output tokens across all requests
    - tool_calls: total tool use calls
    - session_id: the actual session ID being monitored
    """
    original_session_id = session_id

    if session_id == "default":
        current_session = await _get_current_session_id()
        if current_session:
            session_id = current_session

    for project_dir in _get_all_project_dirs():
        session_file = project_dir / f"{session_id}.jsonl"
        if session_file.exists():
            stats = await _read_session_stats(session_file)

            max_context = 200000
            context_used = stats["last_request_input"]
            remaining = max(0, max_context - context_used)

            total_input = stats["total_input_tokens"]
            total_output = stats["total_output_tokens"]
            total_tools = stats["tool_calls"]

            segments = [
                ContextSegment(
                    label="Input",
                    value=context_used,
                    color="#4A90D9",
                    percentage=round(context_used / max_context * 100, 2) if max_context else 0,
                ),
                ContextSegment(
                    label="Output",
                    value=total_output,
                    color="#7B68EE",
                    percentage=round(total_output / max_context * 100, 2) if max_context else 0,
                ),
                ContextSegment(
                    label="Tool Use",
                    value=total_tools,
                    color="#50C878",
                    percentage=round(total_tools / max_context * 100, 2) if max_context else 0,
                ),
            ]

            return ContextWindow(
                total=max_context,
                used=context_used,
                remaining=remaining,
                max_context=max_context,
                segments=segments,
                input_tokens=total_input,
                output_tokens=total_output,
                tool_calls=total_tools,
                session_id=session_id if session_id != "default" else (original_session_id or "default"),
            )

    max_context = 200000
    return ContextWindow(
        total=max_context,
        used=0,
        remaining=max_context,
        max_context=max_context,
        segments=[
            ContextSegment(label="Input", value=0, color="#4A90D9", percentage=0),
            ContextSegment(label="Output", value=0, color="#7B68EE", percentage=0),
            ContextSegment(label="Tool Use", value=0, color="#50C878", percentage=0),
        ],
        input_tokens=0,
        output_tokens=0,
        tool_calls=0,
        session_id=session_id,
    )


async def get_usage_aggregate() -> dict:
    """Get aggregate token usage statistics across all sessions.

    Returns total input, output, tool calls, and combined token counts.
    """
    all_stats = await _get_all_session_stats()

    total_input = 0
    total_output = 0
    total_tools = 0

    for stats in all_stats:
        total_input += stats.get("total_input_tokens", 0)
        total_output += stats.get("total_output_tokens", 0)
        total_tools += stats.get("tool_calls", 0)

    return {
        "total_input": total_input,
        "total_output": total_output,
        "total_tools": total_tools,
        "total_tokens": total_input + total_output,
    }


async def get_usage_time_series(days: int = 14) -> List[UsageTimeSeriesPoint]:
    """Aggregate token usage by day for the last N days.

    All values represent BILLABLE token consumption.
    Dates are converted to local time for accurate daily aggregation.
    """
    all_stats = await _get_all_session_stats()

    # Build date map using local time
    now = datetime.now().astimezone()  # Local time now
    date_map: Dict[str, Dict[str, int]] = {}
    for i in range(days):
        d = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        date_map[d] = {"input_tokens": 0, "output_tokens": 0, "tool_calls": 0}

    for stats in all_stats:
        for date_str, daily_data in stats.get("daily_stats", {}).items():
            if date_str in date_map:
                date_map[date_str]["input_tokens"] += daily_data["input_tokens"]
                date_map[date_str]["output_tokens"] += daily_data["output_tokens"]
                date_map[date_str]["tool_calls"] += daily_data["tool_calls"]

    result: List[UsageTimeSeriesPoint] = []
    for date_str in sorted(date_map.keys()):
        data = date_map[date_str]
        input_tokens = data["input_tokens"]
        output_tokens = data["output_tokens"]
        tool_calls = data["tool_calls"]
        total_tokens = input_tokens + output_tokens

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        display_date = dt.strftime("%m-%d")

        result.append(
            UsageTimeSeriesPoint(
                date=display_date,
                input=input_tokens,
                output=output_tokens,
                tools=tool_calls,
                total=total_tokens,
            )
        )

    return result
