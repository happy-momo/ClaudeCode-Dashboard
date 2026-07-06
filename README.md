# Claude Dashboard

> 🚀 **A Production-Ready Management Dashboard for Claude Code** — Monitor sessions, manage configurations, track token usage, and browse conversation history with a beautiful, real-time interface.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Node: 18+](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org)
[![React: 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev)

<img width="1900" height="897" alt="image" src="https://github.com/user-attachments/assets/362250ab-2ed9-4b07-9750-d6572b71d523" />

<img width="1889" height="885" alt="image" src="https://github.com/user-attachments/assets/6ba2149d-17d7-478d-b9d5-be0f17a065de" />

<img width="1882" height="862" alt="image" src="https://github.com/user-attachments/assets/54e57a6e-e939-4e16-9157-ab8d405a6bed" />


---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [Development](#-development)
- [Testing](#-testing)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

Claude Dashboard is a **Claude Code plugin** that provides a comprehensive web-based interface for managing your Claude Code development workflow. It runs locally as part of the Claude Code plugin system, requiring no external servers or cloud services.

**Key Value Propositions:**

- 🔒 **100% Local** — All data stays on your machine
- ⚡ **Zero Configuration** — Automatic backend startup, no manual setup
- 📊 **Real-time Metrics** — Live token usage and context window monitoring
- 🎯 **Session-Aware** — Automatic session detection and isolation
- 🧩 **Plugin Architecture** — Extensible hooks and MCP server integration

---

## ✨ Features

### 📊 Token Statistics & Context Monitoring

Track your Claude Code usage with precision:

- **Real-time token tracking** — Input, output, and tool-use tokens
- **Context window visualization** — See remaining context capacity
- **Official Anthropic tokenizer** — Accurate token counts matching Claude's usage
- **Multi-dimensional stats** — Filter by session, date range, and conversation
- **Historical trends** — 14-day usage charts and patterns

### ⚙️ Configuration Management

Manage all Claude Code configurations from a single interface:

| Category | Capabilities |
|----------|--------------|
| **Skills** | CRUD operations, enable/disable, import/export, scope switching |
| **MCP Servers** | Add/remove servers, connectivity testing, conflict detection |
| **Plugins** | Install, uninstall, enable/disable, version management |
| **Scopes** | Toggle between project-level and global configurations |

### 💬 Conversation History

Browse and search your Claude Code conversations:

- **Full history access** — All conversations across all sessions
- **Smart search** — Filter by project, date, or content
- **Rich sorting** — By token count, turns, or timestamp
- **Export capability** — Download conversations for archival

### 🔗 Session-Based Architecture

Seamless multi-session support:

- **Automatic registration** — Each Claude Code window registers on startup
- **Direct link access** — `http://127.0.0.1:18080/?session_id=xxx`
- **Session isolation** — View data scoped to current session
- **No manual selection** — URL-based session routing

---

## 🚀 Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, Claude Code CLI

```bash
# 1. Add the marketplace to Claude Code
claude plugin marketplace add https://github.com/happy-momo/ClaudeCode-Dashboard

# 2. Install the plugin
claude plugin install claude-dashboard

# 3. Start Claude Code in any project
claude

# 4. Click the dashboard link shown in the terminal
# http://127.0.0.1:18080/?session_id=xxx
```

---

## 📦 Installation

### Quick Installation via Marketplace

The plugin can be installed directly from the GitHub repository:

```bash
# Step 1: Add the plugin marketplace
claude plugin marketplace add https://github.com/happy-momo/ClaudeCode-Dashboard

# Step 2: Install the plugin
claude plugin install claude-dashboard
```

### Verification

After installation, verify the plugin is installed:

```bash
# In Claude Code, run:
/plugins list

# You should see "claude-dashboard" in the list
```

### Development Installation

For development or local testing, you can install from a local directory:

```bash
# Clone the repository
git clone https://github.com/happy-momo/ClaudeCode-Dashboard.git
cd ClaudeCode-Dashboard

# Build the frontend
cd frontend && npm install && npm run build

# Add as a local marketplace
claude plugin marketplace add file://$(pwd)/.claude-plugin

# Install the plugin
claude plugin install claude-dashboard
```

---

## 💻 Usage

### Starting a Session

1. **Open a terminal** and navigate to your project directory
2. **Start Claude Code:**
   ```bash
   claude
   ```
3. **Observe the dashboard link** in the terminal output:
   ```
   ┌─────────────────────────────────────────┐
   │  Claude Dashboard Ready                 │
   │                                         │
   │  Open in your browser to view session:  │
   │    http://127.0.0.1:18080/?session_id=  │
   │                                         │
   │  Project: my-project                    │
   │  Session: abc12345...                   │
   └─────────────────────────────────────────┘
   ```
4. **Click the link** to open the dashboard in your browser

### Dashboard Pages

| Page | Description |
|------|-------------|
| **Metrics** | Real-time token usage, context window, 14-day trends |
| **Conversations** | Browse, search, and filter conversation history |
| **Management** | Configure Skills, MCP Servers, and Plugins |

### Multi-Session Workflow

When running multiple Claude Code windows:

- Each window gets its own `session_id`
- All sessions share the same backend (port 18080)
- Data is isolated per session
- Switch between sessions via browser tabs

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code CLI                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  session_start  │  │  user_prompt    │  │  post_tool  │  │
│  │     hook        │  │     hook        │  │    hook     │  │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘  │
│           │                    │                   │         │
└───────────┼────────────────────┼───────────────────┼─────────┘
            │                    │                   │
            ▼                    ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Backend (FastAPI)                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  API Routes: /api/v1/{sessions,skills,mcp,plugins,...}  ││
│  │  Session Registry (in-memory singleton)                 ││
│  │  Static Files (React SPA)                               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React 19)                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Pages: Metrics, Conversations, Management              ││
│  │  Components: Reusable UI library                        ││
│  │  State: TanStack Query + React Context                  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
claude-dashboard/
├── .claude-plugin/          # Plugin metadata
│   ├── plugin.json          # Name, version, repository
│   └── .mcp.json            # MCP server configuration
├── backend/                 # FastAPI Python backend
│   ├── api/                 # REST API endpoints
│   ├── core/                # Core utilities (errors, logging, paths)
│   ├── models/              # Pydantic data models
│   ├── modules/             # Business logic managers
│   ├── services/            # Service layer (CLI, MCP, plugins)
│   ├── static/              # Built frontend assets
│   ├── tests/               # Pytest test suite
│   ├── tokenizer/           # Token counting utilities
│   ├── utils/               # Utility modules
│   ├── config.py            # Configuration
│   ├── main.py              # FastAPI entry point
│   └── requirements.txt     # Python dependencies
├── frontend/                # React 19 + TypeScript frontend
│   ├── src/
│   │   ├── api/             # API client modules
│   │   ├── components/      # Reusable UI components
│   │   ├── features/        # Feature modules (Config, History, Metrics)
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # Utilities and context
│   │   ├── providers/       # React context providers
│   │   ├── types/           # TypeScript type definitions
│   │   ├── App.tsx          # Root component
│   │   └── main.tsx         # React entry point
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── hooks/                   # Claude Code hooks
│   ├── hooks.json           # Hook definitions
│   ├── session_start.py     # Session registration
│   ├── user_prompt.py       # User input tracking
│   ├── post_tool.py         # Tool usage tracking
│   ├── message_stop.py      # Response tracking
│   └── run-python.sh        # Cross-platform Python launcher
├── scripts/
│   └── install.sh           # Automated installation script
├── docs/                    # Additional documentation
├── package.json             # Root npm metadata
└── README.md                # This file
```

### Plugin Lifecycle

1. **Installation:** `claude plugin install` copies plugin metadata
2. **Session Start:** `session_start.py` hook fires:
   - Checks if backend is running
   - Starts backend if needed
   - Registers session with backend
   - Outputs dashboard URL
3. **During Session:** Hooks track token usage:
   - `user_prompt.py` — Input tokens
   - `post_tool.py` — Tool tokens
   - `message_stop.py` — Output tokens
4. **Session End:** Session expires after 1 hour of inactivity

---

## 🛠️ Development

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Claude Code CLI** (for plugin testing)

### Backend Development

```bash
cd backend

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
```

**Development server:** http://127.0.0.1:18080  
**API documentation:** http://127.0.0.1:18080/docs

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server with hot reload
npm run dev
```

**Dev server:** http://localhost:5173 (proxies API to backend)

### Running Both Servers

For full-stack development:

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Build Commands

| Command | Description |
|---------|-------------|
| `npm run build` | Build frontend for production |
| `npm run lint` | Run ESLint on frontend |
| `npm run test` | Run frontend tests |
| `pytest` | Run backend tests |
| `pytest --cov` | Run tests with coverage |

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov=modules --cov=services

# Run specific test file
pytest tests/test_api_skills.py -v

# Run tests matching pattern
pytest -k "test_mcp" -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm run test

# Run tests with coverage
npm run test -- --coverage

# Run specific test file
npm run test -- src/components/ui/Button.test.tsx
```

### Test Structure

```
backend/tests/
├── conftest.py              # Pytest fixtures
├── test_api_mcp.py          # MCP API tests
├── test_api_plugins.py      # Plugin API tests
├── test_api_skills.py       # Skill API tests
├── test_api_stats.py        # Stats API tests
├── test_api_system.py       # System API tests
├── test_atomic_file.py      # Atomic file operations
├── test_claude_cli_service.py # CLI service tests
├── test_mcp_service.py      # MCP service tests
├── test_operation_planner.py # Operation planner tests
├── test_paths.py            # Path resolution tests
├── test_security.py         # Security tests
└── test_skill_service.py    # Skill service tests

frontend/src/
├── api/client.test.ts       # API client tests
└── components/ui/
    ├── Button.test.tsx      # Button component tests
    ├── Card.test.tsx        # Card component tests
    └── Toggle.test.tsx      # Toggle component tests
```

---

## 📡 API Reference

### Base URL

```
http://127.0.0.1:18080/api/v1
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/status` | Health check |
| `GET` | `/sessions/list` | List active sessions |
| `POST` | `/sessions/register` | Register a session |
| `GET` | `/skills?scope=project\|global` | List skills |
| `POST` | `/skills?scope=project\|global` | Create skill |
| `PUT` | `/skills/{name}` | Update skill |
| `DELETE` | `/skills/{name}` | Delete skill |
| `GET` | `/mcp?scope=project\|global` | List MCP servers |
| `POST` | `/mcp?scope=project\|global` | Add MCP server |
| `DELETE` | `/mcp/{name}` | Remove MCP server |
| `GET` | `/plugins` | List plugins |
| `POST` | `/plugins/install` | Install plugin |
| `DELETE` | `/plugins/{id}` | Uninstall plugin |
| `GET` | `/stats/context` | Context window stats |
| `GET` | `/stats/usage?days=14` | Usage statistics |
| `GET` | `/conversations` | List conversations |
| `GET` | `/conversations/{session_id}` | Get conversation detail |

### Request Headers

| Header | Description |
|--------|-------------|
| `X-Claude-Session-Id` | Session identifier for scoping |

### Example Request

```bash
curl -X GET http://127.0.0.1:18080/api/v1/skills?scope=project \
  -H "X-Claude-Session-Id: abc123..."
```

---

## 🔧 Troubleshooting

### Backend Not Starting

**Symptom:** "Backend not responding" error

**Solution:**
```bash
# Check if port 18080 is in use
lsof -i :18080

# Kill existing process if needed
kill -9 $(lsof -t -i :18080)

# Manually start backend
cd backend && source venv/bin/activate && python main.py
```

### Frontend Build Fails

**Symptom:** `npm run build` fails

**Solution:**
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Plugin Not Loading

**Symptom:** Dashboard link not appearing in Claude Code

**Solution:**
```bash
# Reinstall plugin
claude plugin uninstall claude-dashboard
claude plugin install ./.claude-plugin

# Restart Claude Code
```

### Session Not Found

**Symptom:** "Session not found" error in dashboard

**Solution:**
1. Ensure Claude Code is still running
2. Check session hasn't expired (1 hour timeout)
3. Refresh the dashboard page
4. Restart Claude Code to get new session

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style

- **Python:** Follow PEP 8, use type hints
- **TypeScript:** Strict mode enabled
- **Components:** Functional components with hooks
- **Testing:** Add tests for new features

### Pull Request Requirements

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Passing CI checks

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Anthropic](https://www.anthropic.com/)** — Claude AI and Claude Code
- **[FastAPI](https://fastapi.tiangolo.com/)** — Modern Python web framework
- **[React](https://react.dev/)** — UI library
- **[TanStack Query](https://tanstack.com/query)** — Data fetching
- **[Tailwind CSS](https://tailwindcss.com/)** — Utility-first CSS

---

## 📮 Contact & Support

- **Issues:** [GitHub Issues](https://github.com/happy-momo/ClaudeCode-Dashboard/issues)
- **Discussions:** [GitHub Discussions](https://github.com/happy-momo/ClaudeCode-Dashboard/discussions)
- **Security:** Report vulnerabilities via GitHub Security Advisories

---

**Made with ❤️ by the Claude Dashboard Team**

*Last updated: July 2026*
