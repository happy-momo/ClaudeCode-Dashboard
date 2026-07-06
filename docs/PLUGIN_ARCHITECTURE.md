# Claude Dashboard Plugin Architecture

## Overview

Claude Dashboard is designed as a standard Claude Code plugin. This document explains the plugin structure, loading mechanism, and development workflow.

## Claude Code Plugin Mechanism

### Standard Plugin Directory Structure

```
claude-dashboard/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata (required)
├── hooks/
│   ├── hooks.json           # Hooks configuration (required)
│   ├── session_start.py     # Session registration hook
│   ├── user_prompt.py       # User prompt hook
│   └── post_tool.py         # Post tool-use hook
├── backend/                 # Backend service
├── frontend/                # Frontend UI
├── scripts/                 # Installation scripts
├── package.json             # npm/package metadata
└── README.md
```

### plugin.json Format

```json
{
  "name": "claude-dashboard",
  "version": "1.0.0",
  "description": "Claude Code management dashboard",
  "author": {
    "name": "Claude Dashboard Team"
  },
  "homepage": "https://github.com/your-org/claude-dashboard",
  "repository": "https://github.com/your-org/claude-dashboard",
  "license": "MIT",
  "keywords": ["dashboard", "management", "claude-code"],
  "hooks": "./hooks/hooks.json",
  "entry": "backend/main.py"
}
```

### hooks/hooks.json Format

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py",
            "timeout": 5000
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/user_prompt.py",
            "timeout": 5000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/post_tool.py",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `hooks` | object | Top-level must be `{"hooks": {...}}` |
| `EventType` | array | Event types: `SessionStart`, `UserPromptSubmit`, `PostToolUse` |
| `matcher` | string | Regex pattern, empty string `""` matches all events of this type |
| `hooks` | array | Each matcher contains a `hooks` array |
| `type` | string | Hook type, currently supports `"command"` |
| `command` | string | Command to execute |
| `timeout` | number | Optional, timeout in milliseconds |
| `async` | boolean | Optional, whether to execute asynchronously |

**Environment Variables:**
- `${CLAUDE_PLUGIN_ROOT}` - Plugin root directory
- `${CLAUDE_SESSION_ID}` - Current session ID
- `${HOME}` - User home directory

## Plugin Loading Mechanism

### Method 1: Marketplace Installation (Standard)

1. **Publish to Marketplace**
   - Publish plugin to GitHub repository
   - Register in marketplace

2. **User Installation**
   ```
   /plugins install claude-dashboard
   ```

3. **Auto-Discovery**
   - Claude Code automatically reads `hooks/hooks.json` from plugin directory
   - No manual configuration needed

### Method 2: Local Development Installation (Recommended for Development)

1. **Register Local Marketplace**
   ```bash
   python3 scripts/install.sh
   ```

2. **Install Plugin**
   ```
   /plugins install claude-dashboard-local
   ```

3. **Auto-Discover Hooks**
   - Claude Code reads `hooks/hooks.json` from local directory

## Development Workflow

### Initial Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/claude-dashboard.git
cd claude-dashboard

# 2. Run installation script
python3 scripts/install.sh

# 3. Restart Claude Code (if running)

# 4. Install the plugin
/plugins install claude-dashboard-local

# 5. Start Claude Code in any project
claude

# 6. Verify hooks are loaded
# You should see a dashboard link in the terminal
```

### Daily Development

```bash
# After modifying code, restart Claude Code
# Hooks are automatically reloaded from hooks/hooks.json
```

### Debugging

If hooks are not working:

1. **Check installed plugins**
   ```bash
   cat ~/.claude/plugins/installed_plugins.json | python3 -m json.tool
   ```

2. **Check hooks configuration**
   ```bash
   cat hooks/hooks.json
   ```

3. **Verify plugin is enabled**
   ```bash
   cat ~/.claude/settings.json | python3 -m json.tool | grep -A 5 enabledPlugins
   ```

## Installation Methods Comparison

| Feature | Plugin Method | settings.json Method |
|---------|--------------|---------------------|
| Config Location | `hooks/hooks.json` | `~/.claude/settings.json` |
| Auto-Discovery | ✅ Yes | ❌ No |
| Environment Variables | ✅ Supports `${CLAUDE_PLUGIN_ROOT}` | ❌ Requires absolute paths |
| Developer Friendly | ✅ Auto-reload on restart | ⚠️ Requires re-running script |
| Production Ready | ✅ Yes | ❌ No |
| Recommended For | Daily development, production | Quick testing, debugging |

## Script Reference

### scripts/install.sh

Registers the local directory as a marketplace and provides installation instructions. This is the recommended way to install the plugin for local development.

## Summary

**Recommended Development Workflow:**

1. Run `python3 scripts/install.sh` to register local marketplace
2. In Claude Code, run `/plugins install claude-dashboard-local`
3. Hooks are automatically loaded from `hooks/hooks.json`
4. After code changes, restart Claude Code to reload hooks

**Important Notes:**

- Hooks are loaded from `hooks/hooks.json` in the plugin directory
- Claude Code discovers hooks automatically through the plugin system
- No manual configuration of `~/.claude/settings.json` is needed for hooks
- The `install.sh` script only registers the marketplace, not hooks directly
