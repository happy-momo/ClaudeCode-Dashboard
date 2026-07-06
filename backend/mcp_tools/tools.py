"""MCP tool definitions for Claude Code integration.

These tools wrap the same business logic used by the HTTP API,
allowing Claude to manage the dashboard via natural language.
"""

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules import skill_manager, mcp_manager, stats_manager, conversation_manager, system_manager
from config import DEFAULT_PORT

mcp = FastMCP(
    name="claude-dashboard",
)


@mcp.tool()
async def list_skills(scope: str = "project") -> str:
    """List skills in the given scope (project or global).

    Args:
        scope: The scope to list skills from - 'project' or 'global'
    """
    skills = await skill_manager.list_skills(scope)
    if not skills:
        return f"No skills found in {scope} scope."

    lines = [f"Skills ({scope} scope):"]
    for s in skills:
        status = "active" if s.active else "disabled"
        override = f" (overridden by {s.overridden['scope']})" if s.overridden else ""
        lines.append(f"  - {s.name}: {s.description} [{status}]{override}")
    return "\n".join(lines)


@mcp.tool()
async def get_skill(name: str, scope: str = "project") -> str:
    """Get the content of a specific skill.

    Args:
        name: The skill name
        scope: The scope - 'project' or 'global'
    """
    skill = await skill_manager.get_skill(name, scope)
    if skill is None:
        return f"Skill '{name}' not found in {scope} scope."
    return f"# {skill.name}\nScope: {skill.scope}\nActive: {skill.active}\n\n{skill.content}"


@mcp.tool()
async def list_mcp_servers(scope: str = "project") -> str:
    """List configured MCP servers in the given scope.

    Args:
        scope: The scope - 'project' or 'global'
    """
    servers = await mcp_manager.list_mcp_servers(scope)
    if not servers:
        return f"No MCP servers found in {scope} scope."

    lines = [f"MCP Servers ({scope} scope):"]
    for s in servers:
        status = "active" if s.active else "disabled"
        override = f" (overridden by {s.overridden['scope']})" if s.overridden else ""
        cmd = s.config.command
        args = " ".join(s.config.args) if s.config.args else ""
        lines.append(f"  - {s.name}: {cmd} {args} [{status}]{override}")
    return "\n".join(lines)


@mcp.tool()
async def add_mcp_server(name: str, command: str, args: str = "", scope: str = "project") -> str:
    """Add a new MCP server configuration.

    Args:
        name: Server name (unique identifier)
        command: The command to run the server
        args: Space-separated arguments (optional)
        scope: The scope - 'project' or 'global'
    """
    arg_list = args.split() if args.strip() else []
    try:
        server = await mcp_manager.add_mcp_server(name, command, arg_list, {}, scope)
        return f"MCP server '{name}' added to {scope} scope. Command: {command}"
    except ValueError as e:
        return str(e)


@mcp.tool()
async def remove_mcp_server(name: str, scope: str = "project") -> str:
    """Remove an MCP server configuration.

    Args:
        name: Server name to remove
        scope: The scope - 'project' or 'global'
    """
    removed = await mcp_manager.remove_mcp_server(name, scope)
    if removed:
        return f"MCP server '{name}' removed from {scope} scope."
    return f"MCP server '{name}' not found in {scope} scope."


@mcp.tool()
async def detect_mcp_conflicts() -> str:
    """Detect MCP server name conflicts between project and global scope."""
    conflicts = await mcp_manager.detect_conflicts()
    if not conflicts:
        return "No MCP server conflicts detected."
    lines = ["MCP Server Conflicts:"]
    for c in conflicts:
        lines.append(f"  - '{c.name}' exists in both project and global scope")
    return "\n".join(lines)


@mcp.tool()
async def get_current_token_usage(session_id: str = "default") -> str:
    """Get current token usage statistics.

    Args:
        session_id: The session ID (default: 'default')
    """
    context = await stats_manager.get_context_window(session_id)
    aggregate = await stats_manager.get_usage_aggregate()

    lines = [
        f"Token Usage Statistics:",
        f"  Current Context: {context['used']:,} / {context['max_context']:,} tokens ({context['used']/context['max_context']*100:.1f}%)",
        f"  Remaining: {context['remaining']:,} tokens",
        f"",
        f"  Total Aggregate:",
        f"    Input:  {aggregate['total_input']:,}",
        f"    Output: {aggregate['total_output']:,}",
        f"    Tools:  {aggregate['total_tools']:,}",
        f"    Total:  {aggregate['total_tokens']:,}",
    ]
    return "\n".join(lines)


@mcp.tool()
async def get_context_window(session_id: str = "default") -> str:
    """Get context window occupancy details.

    Args:
        session_id: The session ID (default: 'default')
    """
    context = await stats_manager.get_context_window(session_id)

    lines = [
        f"Context Window (session: {session_id}):",
        f"  Used: {context['used']:,} / {context['max_context']:,} tokens ({context['used']/context['max_context']*100:.1f}%)",
        f"  Remaining: {context['remaining']:,} tokens",
        f"  Segments:",
    ]
    for seg in context.get("segments", []):
        lines.append(f"    - {seg['label']}: {seg['value']:,} ({seg['percentage']:.1f}%)")
    return "\n".join(lines)


@mcp.tool()
async def list_conversations() -> str:
    """List conversation history."""
    conversations = await conversation_manager.list_conversations()
    if not conversations:
        return "No conversations found."

    lines = ["Conversations:"]
    for c in conversations:
        lines.append(f"  - [{c['id']}] {c['title']} ({c['date']}, {c['turns']} turns, {c['tokens']:,} tokens)")
    return "\n".join(lines)


@mcp.tool()
async def get_conversation(session_id: str) -> str:
    """Get details of a specific conversation.

    Args:
        session_id: The session ID
    """
    conversation = await conversation_manager.get_conversation(session_id)
    if conversation is None:
        return f"Conversation '{session_id}' not found."

    lines = [
        f"Conversation: {conversation['title']}",
        f"  ID: {conversation['id']}",
        f"  Date: {conversation['date']}",
        f"  Turns: {conversation['turns']}",
        f"  Tokens: {conversation['tokens']:,}",
    ]
    for msg in conversation.get("messages", []):
        lines.append(f"  [{msg['role']}] {msg['content'][:100]}...")
    return "\n".join(lines)


@mcp.tool()
async def get_service_status() -> str:
    """Get the current service status of the dashboard backend."""
    status = system_manager.get_service_status(DEFAULT_PORT)
    return (
        f"Dashboard Status: {status['status']}\n"
        f"  URL: http://{status['host']}:{status['port']}\n"
        f"  Uptime: {status['uptime_seconds']}s\n"
        f"  MCP Connected: {status['mcp_connected']}"
    )


@mcp.tool()
async def open_dashboard() -> str:
    """Get the dashboard URL to open in a browser."""
    url = system_manager.get_dashboard_url(DEFAULT_PORT)
    return f"Dashboard available at: {url}"
