# Claude Dashboard - Project Structure

## Standard Plugin Directory Structure

```
claude-dashboard/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata (required)
├── hooks/
│   ├── hooks.json           # Hooks configuration (required)
│   ├── session_start.py     # Session registration hook
│   ├── user_prompt.py       # User prompt hook
│   ├── post_tool.py         # Post tool-use hook
│   └── message_stop.py      # Message stop hook
├── backend/
│   ├── main.py              # FastAPI HTTP + MCP server entry point
│   ├── requirements.txt     # Python dependencies
│   ├── config.py            # Configuration
│   ├── api/                 # REST API endpoints
│   │   ├── router.py        # API router
│   │   ├── sessions.py      # Session management endpoints
│   │   ├── skills.py        # Skills endpoints
│   │   ├── mcp.py           # MCP server endpoints
│   │   ├── plugins.py       # Plugin endpoints
│   │   ├── stats.py         # Token statistics endpoints
│   │   ├── conversations.py # Conversation endpoints
│   │   └── ...
│   ├── modules/             # Business logic modules
│   │   ├── session_registry.py  # Session tracking singleton
│   │   ├── skill_manager.py
│   │   ├── mcp_manager.py
│   │   ├── plugin_manager.py
│   │   └── ...
│   ├── models/              # Pydantic data models
│   ├── services/            # Service layer
│   ├── tokenizer/           # Token calculation
│   ├── utils/               # Utility functions
│   ├── tests/               # Backend tests
│   └── static/              # Frontend build output
├── frontend/
│   ├── package.json         # npm dependencies
│   ├── vite.config.ts       # Vite configuration
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   ├── src/
│   │   ├── App.tsx          # Main application component
│   │   ├── main.tsx         # React entry point
│   │   ├── api/             # API client
│   │   ├── components/      # Reusable UI components
│   │   ├── features/        # Feature modules
│   │   ├── lib/             # Utilities and context
│   │   └── types/           # TypeScript types
│   └── index.html
├── scripts/
│   └── install.sh           # Installation script
├── docs/
│   └── PLUGIN_ARCHITECTURE.md  # Plugin architecture documentation
├── .gitignore
├── package.json             # npm/package metadata
└── README.md
```

## Key Files

### .claude-plugin/plugin.json

Plugin metadata that tells Claude Code about the plugin:

```json
{
  "name": "claude-dashboard",
  "version": "1.0.0",
  "description": "Claude Code management dashboard",
  "hooks": "./hooks/hooks.json",
  "entry": "backend/main.py"
}
```

### hooks/hooks.json

Hooks configuration that Claude Code loads automatically:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py"
          }
        ]
      }
    ]
  }
}
```

### scripts/install.sh

Installation script that registers the local marketplace:

```bash
python3 scripts/install.sh
```

## Installation

1. Run the installation script:
   ```bash
   python3 scripts/install.sh
   ```

2. Install the plugin in Claude Code:
   ```
   /plugins install claude-dashboard-local
   ```

3. Start Claude Code:
   ```bash
   claude
   ```

## How Hooks Work

1. When Claude Code starts, it loads all installed plugins
2. For each plugin, it reads `hooks/hooks.json`
3. When a `SessionStart` event occurs, Claude Code executes the configured hook
4. The hook script (`session_start.py`) registers the session and outputs the dashboard link

## Environment Variables

In `hooks/hooks.json`, you can use:
- `${CLAUDE_PLUGIN_ROOT}` - Plugin root directory (automatically resolved by Claude Code)
- `${CLAUDE_SESSION_ID}` - Current session ID
- `${HOME}` - User home directory
