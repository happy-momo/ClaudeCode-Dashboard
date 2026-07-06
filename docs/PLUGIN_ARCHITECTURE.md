# Claude Dashboard Plugin Architecture

## Overview

Claude Dashboard is designed as a standard Claude Code plugin. This document explains the plugin structure, loading mechanism, and development workflow.

## Claude Code Plugin Mechanism

### Standard Plugin Directory Structure

```
ClaudeCode-Dashboard/
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
  "homepage": "https://github.com/happy-momo/ClaudeCode-Dashboard",
  "repository": "https://github.com/happy-momo/ClaudeCode-Dashboard",
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

### Method 1: Marketplace Installation (Recommended)

This is the standard way to install the plugin from a GitHub repository:

```bash
# Step 1: Add the marketplace
claude plugin marketplace add https://github.com/happy-momo/ClaudeCode-Dashboard

# Step 2: Install the plugin
claude plugin install claude-dashboard
```

**Benefits:**
- No manual configuration needed
- Automatic discovery of hooks
- Easy to update from repository

### Method 2: Local Development Installation

For development or testing local modifications:

```bash
# Step 1: Clone the repository
git clone https://github.com/happy-momo/ClaudeCode-Dashboard.git
cd ClaudeCode-Dashboard

# Step 2: Build the frontend (if needed)
bash scripts/install.sh

# Step 3: Add as a local marketplace
claude plugin marketplace add file://$(pwd)/.claude-plugin

# Step 4: Install the plugin
claude plugin install claude-dashboard
```

**Benefits:**
- Can test local modifications
- No need to push changes to GitHub first
- Full development environment

## Development Workflow

### Initial Setup

```bash
# 1. Clone the repository
git clone https://github.com/happy-momo/ClaudeCode-Dashboard.git
cd ClaudeCode-Dashboard

# 2. Run installation script (builds frontend)
bash scripts/install.sh

# 3. Add as local marketplace
claude plugin marketplace add file://$(pwd)/.claude-plugin

# 4. Install the plugin
claude plugin install claude-dashboard

# 5. Start Claude Code in any project
claude

# 6. Verify hooks are loaded
# You should see a dashboard link in the terminal
```

### Daily Development

```bash
# After modifying code, reinstall the plugin
claude plugin uninstall claude-dashboard
claude plugin install claude-dashboard

# Or simply restart Claude Code
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

| Feature | Marketplace Method | Local Development |
|---------|-------------------|-------------------|
| Config Location | `hooks/hooks.json` | `hooks/hooks.json` |
| Auto-Discovery | ✅ Yes | ✅ Yes |
| Environment Variables | ✅ Supports `${CLAUDE_PLUGIN_ROOT}` | ✅ Supports `${CLAUDE_PLUGIN_ROOT}` |
| Developer Friendly | ✅ Auto-reload on restart | ✅ Auto-reload on restart |
| Production Ready | ✅ Yes | ✅ Yes |
| Recommended For | Production use | Development and testing |

## Script Reference

### scripts/install.sh

This script:
1. Validates prerequisites (Python 3.11+, Node.js 18+)
2. Creates Python virtual environment
3. Installs backend dependencies
4. Installs frontend dependencies
5. Builds frontend for production

After running this script, you need to:
1. Add the marketplace: `claude plugin marketplace add file://$(pwd)/.claude-plugin`
2. Install the plugin: `claude plugin install claude-dashboard`

## Summary

**Recommended Production Workflow:**

1. Add marketplace: `claude plugin marketplace add https://github.com/happy-momo/ClaudeCode-Dashboard`
2. Install plugin: `claude plugin install claude-dashboard`
3. Hooks are automatically loaded from `hooks/hooks.json`

**Recommended Development Workflow:**

1. Clone repository and run `bash scripts/install.sh`
2. Add local marketplace: `claude plugin marketplace add file://$(pwd)/.claude-plugin`
3. Install plugin: `claude plugin install claude-dashboard`
4. Hooks are automatically loaded from `hooks/hooks.json`
5. After code changes, reinstall plugin or restart Claude Code

**Important Notes:**

- Hooks are loaded from `hooks/hooks.json` in the plugin directory
- Claude Code discovers hooks automatically through the plugin system
- No manual configuration of `~/.claude/settings.json` is needed for hooks
- The `install.sh` script only builds the frontend, not register hooks directly