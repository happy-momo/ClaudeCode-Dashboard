# Claude Dashboard - Installation Guide

## Prerequisites

Before installing Claude Dashboard, ensure you have the following:

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Claude Code CLI** installed and configured

## Quick Installation

### Method 1: Install from GitHub Marketplace (Recommended)

The simplest way to install Claude Dashboard is directly from the GitHub repository:

```bash
# Step 1: Add the plugin marketplace
claude plugin marketplace add https://github.com/happy-momo/ClaudeCode-Dashboard

# Step 2: Install the plugin
claude plugin install claude-dashboard
```

### Method 2: Install from Local Directory (For Development)

If you want to modify the plugin or test locally:

```bash
# Step 1: Clone the repository
git clone https://github.com/happy-momo/ClaudeCode-Dashboard.git
cd ClaudeCode-Dashboard

# Step 2: Run the installation script (sets up environment and builds frontend)
bash scripts/install.sh

# Step 3: Add as a local marketplace
claude plugin marketplace add file://$(pwd)/.claude-plugin

# Step 4: Install the plugin
claude plugin install claude-dashboard
```

### Verification

After installation, verify the plugin is installed:

```bash
# In Claude Code, run:
/plugins list

# You should see "claude-dashboard" in the list
```

### Start Using

```bash
# Start Claude Code
claude
```

You should see a dashboard link in the terminal:

```
┌─────────────────────────────────────────┐
│  Claude Dashboard Ready                 │
│                                         │
│  Open in your browser:                  │
│  http://127.0.0.1:18080/?session_id=xxx │
│                                         │
│  Project: my-project                    │
│  Session: abc12345...                   │
└─────────────────────────────────────────┘
```

Click the link shown in the terminal to open the dashboard in your browser.

---

## Manual Installation

If the automated script fails, follow these manual steps:

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### Register Plugin

```bash
# Add the marketplace (from project root)
claude plugin marketplace add file://$(pwd)/.claude-plugin

# Install the plugin
claude plugin install claude-dashboard
```

---

## Troubleshooting

### Issue: Dashboard Link Not Showing

**Possible causes:**
- Plugin not properly installed
- Backend service failed to start

**Solutions:**
1. Verify plugin installation: `/plugins list`
2. Manually start backend: `cd backend && python main.py`
3. Restart Claude Code

### Issue: Cannot Access Dashboard

**Possible causes:**
- Backend not running
- Port already in use

**Solutions:**
1. Check if backend is running:
   ```bash
   curl http://127.0.0.1:18080/api/v1/system/status
   ```
2. Check port usage:
   ```bash
   lsof -i :18080
   ```
3. If port is occupied, set custom port:
   ```bash
   export CLAUDE_DASHBOARD_PORT=18081
   ```

### Issue: Hooks Not Executing

**Possible causes:**
- Invalid hooks.json format
- Plugin not loaded correctly

**Solutions:**
1. Validate hooks.json syntax
2. Check Claude Code startup logs
3. Reinstall plugin:
   ```bash
   claude plugin uninstall claude-dashboard
   claude plugin marketplace add https://github.com/happy-momo/ClaudeCode-Dashboard
   claude plugin install claude-dashboard
   ```

---

## Development Mode

### Backend Development

```bash
cd backend
source venv/bin/activate
python main.py
```

Server runs on: http://127.0.0.1:18080  
API docs: http://127.0.0.1:18080/docs

### Frontend Development

```bash
cd frontend
npm run dev
```

Dev server runs on: http://localhost:5173

### Running Both

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Frontend  
cd frontend && npm run dev
```

---

## Uninstallation

### Remove Plugin

```bash
claude plugin uninstall claude-dashboard
```

### Remove Marketplace

```bash
claude plugin marketplace remove claude-dashboard
```

### Remove Configuration

Edit `~/.claude/settings.json` and remove any `claude-dashboard` entries.

### Remove Virtual Environments

```bash
rm -rf backend/venv
rm -rf frontend/node_modules
```

---

## Next Steps

- [Plugin Architecture](./PLUGIN_ARCHITECTURE.md) - Learn about the plugin structure
- [Quick Start](./QUICKSTART.md) - Get started with the dashboard
- [API Documentation](http://localhost:18080/docs) - Explore the API endpoints
