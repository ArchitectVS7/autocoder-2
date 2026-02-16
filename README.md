# AutoCoder 2 - Enterprise-Grade Autonomous Coding Agent

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/leonvanzyl)

A production-ready autonomous coding system that builds complete applications over multiple sessions. Features enterprise-grade quality gates, human-in-the-loop controls, parallel execution, and comprehensive design iteration workflows.

## 🎥 Video Tutorial

[![Watch the tutorial](https://img.youtube.com/vi/lGWFlpffWk4/hqdefault.jpg)](https://youtu.be/lGWFlpffWk4)

> **[Watch the setup and usage guide →](https://youtu.be/lGWFlpffWk4)**

---

## ✨ What Makes AutoCoder 2 Different

### **Human-in-the-Loop Intelligence**
- **Human Input Gates** - Agents request credentials, API keys, and design decisions when genuinely needed
- **Supervisory Agent Mode** - Optional AI supervisor handles all human input requests for full automation
- **Pause/Drain Mode** - Graceful pause that lets running agents finish their current work (better than Ctrl+C)

### **Enterprise Quality Gates**
- **Checkpoint System** - Automated code review every N features (code quality, security, performance)
- **Design Iteration** - Multi-persona UX review (visual designer, UX researcher, accessibility expert)
- **Skip Management** - Smart handling of blocked features with dependency tracking
- **Metrics Dashboard** - Real-time performance tracking with ROI analysis

### **Parallel Execution**
- Run 1-5 concurrent agents with dependency-aware scheduling
- Isolated browser contexts per agent
- Automatic regression testing with configurable agent ratios
- Mission control dashboard with agent mascots (Spark, Fizz, Octo, Hoot, Buzz)

### **Production-Ready Architecture**
- React UI with Tailwind CSS v4 (neobrutalism design)
- FastAPI backend with WebSocket real-time updates
- SQLite with proper migrations and cross-platform support
- Defense-in-depth security (sandbox, filesystem restrictions, command allowlist)
- Playwright CLI for reliable browser automation

---

## 🚀 Quick Start

### Prerequisites

**1. Claude Code CLI (Required)**

macOS / Linux:
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Windows (PowerShell):
```powershell
irm https://claude.ai/install.ps1 | iex
```

**2. Authentication**

Choose one:
- **Claude Pro/Max** - Run `claude login` (recommended)
- **Anthropic API Key** - Pay-per-use from https://console.anthropic.com/

### Launch the Web UI (Recommended)

**Windows:**
```cmd
start_ui.bat
```

**macOS / Linux:**
```bash
./start_ui.sh
```

Opens at `http://localhost:5173` with:
- 📊 Kanban board with drag & drop
- 🎯 Real-time agent output streaming
- 🔄 Start/pause/stop controls
- 📈 Progress tracking and metrics
- 🎨 Dependency graph visualization

### Alternative: CLI Mode

**Windows:**
```cmd
start.bat
```

**macOS / Linux:**
```bash
./start.sh
```

The CLI menu provides:
- Create new project with `/create-spec` command
- Continue existing projects
- Automatic environment setup
- Authentication verification

---

## 📋 Core Workflow

### 1. Two-Agent Pattern

**Initializer Agent (First Session)**
- Reads your app specification (XML format)
- Generates feature test cases with priorities
- Sets up project structure and git
- Creates `features.db` with all test cases

**Coding Agent (Subsequent Sessions)**
- Implements features one by one
- Verifies via browser automation (Playwright CLI)
- Runs regression tests on passing features
- Auto-continues with 3-second delay between sessions

### 2. Feature Management (MCP Tools)

The agent interacts with features through an MCP server:

**Core Operations:**
- `feature_get_next` - Get highest-priority pending feature
- `feature_claim_next` - Atomically claim feature (parallel mode)
- `feature_mark_passing` - Mark feature complete
- `feature_skip` - Move feature to end of queue
- `feature_get_for_regression` - Random passing features for testing

**Human Input (NEW!):**
- `feature_request_human_input` - Request structured input from humans
- `ask_user` - Ask questions with selectable options

**Dependency Management:**
- `feature_add_dependency` - Add dependency (with cycle detection)
- `feature_get_ready` - Get features with satisfied dependencies
- `feature_get_blocked` - Get features blocked by dependencies
- `feature_get_graph` - Dependency graph for visualization

### 3. Browser Automation (Playwright CLI)

Instead of MCP server complexity, agents use simple bash commands:

```bash
# Open browser and navigate
playwright-cli open http://localhost:3000

# Take snapshot to see element refs
playwright-cli snapshot

# Interact with elements
playwright-cli click e15
playwright-cli type "search query"
playwright-cli fill e3 "user@example.com"

# Verify visually
playwright-cli screenshot

# Check for errors
playwright-cli console

# Close when done
playwright-cli close
```

**Benefits:**
- Simpler than MCP server (fewer moving parts)
- Snapshots save to `.playwright-cli/` (token-efficient)
- Direct bash invocation (no subprocess overhead)
- Easier debugging via logs

---

## 🎛️ Advanced Features

### Human Input System

**When agents need credentials or design decisions:**

```python
# Agent requests OAuth credentials
feature_request_human_input(
    feature_id=1,
    prompt="Need OAuth credentials for Google API",
    fields=[
        {
            "id": "client_id",
            "label": "OAuth Client ID",
            "type": "text",
            "required": True
        },
        {
            "id": "client_secret",
            "label": "OAuth Client Secret",
            "type": "text",
            "required": True
        }
    ]
)
```

**Response via UI or API:**

```bash
curl -X POST http://localhost:8000/api/projects/my-app/features/1/human-input \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "123456.apps.googleusercontent.com",
    "client_secret": "GOCSPX-secret-123"
  }'
```

**Supervisory Agent Mode** (Full Automation):

```bash
export ENABLE_SUPERVISORY_AGENT=true
python autonomous_agent_demo.py --project-dir my-app --supervisory-agent
```

AI supervisor automatically provides mock credentials for development.

### Pause/Drain Mode

**Graceful pause** that drains running agents (better than Ctrl+C):

```bash
# Via API
curl -X POST http://localhost:8000/api/projects/my-app/agent/pause

# Via UI
Click "Pause" button → agents drain → enters paused state

# Resume
curl -X POST http://localhost:8000/api/projects/my-app/agent/resume
```

**How it works:**
1. Creates `.autocoder/.pause_drain` signal file
2. Orchestrator stops spawning new agents
3. Running agents complete their current features
4. Enters paused state until signal file removed
5. Resume deletes signal file and continues

### Checkpoint System

Automated quality gates every N features:

```bash
# Configure checkpoints
{
  "checkpoint_interval": 10,  # Review every 10 features
  "agents": {
    "code_review": true,      # Code quality analysis
    "security": true,         # OWASP Top 10 audit
    "performance": true       # Performance analysis
  },
  "pause_on_critical": true   # Auto-pause on critical issues
}
```

**Checkpoint Agents:**
- **Code Review** - Linting, type safety, maintainability
- **Security Audit** - XSS, SQL injection, CSRF, auth issues
- **Performance** - Bundle size, render performance, optimization

Reports saved to `checkpoints/checkpoint_N.md`

### Design Iteration System

Multi-persona UX review workflow:

```bash
python design/review.py --project-dir my-app --iteration 1
```

**Personas:**
- **Visual Designer** - Color theory, typography, layout
- **UX Researcher** - User flows, accessibility, usability
- **Accessibility Expert** - WCAG compliance, screen readers
- **Brand Strategist** - Consistency, messaging, tone

Each persona provides feedback → agent iterates → repeat until approved.

### Parallel Execution

Run multiple agents concurrently:

```bash
python autonomous_agent_demo.py \
  --project-dir my-app \
  --parallel \
  --max-concurrency 3 \
  --testing-agent-ratio 1
```

**Features:**
- Dependency-aware scheduling (blocked features skipped)
- Isolated browser contexts per agent
- Atomic feature claiming (no race conditions)
- Configurable testing agent ratio (0-3 per coding agent)
- Mission Control UI with agent status tracking

### Metrics & Performance

Real-time dashboard and ROI analysis:

```bash
python metrics/dashboard.py --project-dir my-app
```

**Metrics tracked:**
- Features per hour
- Average feature duration
- Regression test coverage
- Blocker resolution time
- Token usage and cost
- ROI calculation (dev time saved)

Reports: `metrics/performance_report.md`

---

## 📁 Project Structure

```
autocoder-2/
├── start.bat / start.sh          # CLI launcher
├── start_ui.bat / start_ui.sh    # Web UI launcher
├── start.py                      # CLI menu with project management
├── start_ui.py                   # FastAPI server launcher
├── autonomous_agent_demo.py      # Agent entry point
├── agent.py                      # Session loop (Claude Agent SDK)
├── client.py                     # ClaudeSDKClient with security hooks
├── security.py                   # Bash allowlist validation
├── prompts.py                    # Prompt template loading
├── progress.py                   # Progress tracking & webhooks
├── registry.py                   # Project registry (SQLite)
├── paths.py                      # Runtime file path resolution
│
├── api/
│   ├── database.py               # SQLAlchemy models (Feature, Checkpoint, etc.)
│   └── dependency_resolver.py   # Cycle detection (Kahn's + DFS)
│
├── mcp_server/
│   └── feature_mcp.py            # MCP server with 15+ tools
│
├── checkpoint/
│   ├── orchestrator.py           # Checkpoint execution engine
│   ├── agent_code_review.py     # Code quality agent
│   ├── agent_security.py        # Security audit agent
│   ├── agent_performance.py     # Performance agent
│   └── autofix.py                # Auto-create fix features
│
├── design/
│   ├── persona_system.py         # Persona loading & management
│   ├── iteration.py              # Design iteration workflow
│   └── review.py                 # CLI tool for design review
│
├── metrics/
│   ├── collector.py              # Performance metrics collection
│   ├── dashboard.py              # Real-time CLI dashboard
│   └── report_generator.py      # ROI analysis reports
│
├── parallel_orchestrator.py     # Concurrent agent execution
│
├── server/
│   ├── main.py                   # FastAPI REST API
│   ├── websocket.py              # Real-time WebSocket updates
│   ├── routers/                  # API endpoints
│   │   ├── agent.py              # Agent control (start/stop/pause)
│   │   ├── features.py           # Feature CRUD + human input
│   │   ├── projects.py           # Project management
│   │   └── filesystem.py         # Folder browser
│   └── services/
│       └── process_manager.py    # Agent subprocess management
│
├── ui/                           # React 18 + TypeScript
│   ├── src/
│   │   ├── App.tsx               # Main app
│   │   ├── components/           # UI components
│   │   │   ├── AgentMissionControl.tsx
│   │   │   ├── DependencyGraph.tsx
│   │   │   └── CelebrationOverlay.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts   # Real-time updates
│   │   │   └── useProjects.ts    # React Query hooks
│   │   └── lib/
│   │       ├── api.ts            # REST client
│   │       └── types.ts          # TypeScript types
│   └── tailwind.config.ts        # Neobrutalism theme
│
├── .claude/
│   ├── commands/
│   │   └── create-spec.md        # /create-spec slash command
│   ├── skills/
│   │   ├── playwright-cli/       # Browser automation skill
│   │   └── frontend-design/      # Distinctive UI design skill
│   └── templates/                # Prompt templates
│
├── tests/
│   ├── test_human_input_system.py
│   ├── test_pause_drain_mode.py
│   └── test_phase*.py            # Integration tests
│
├── docs/
│   ├── DEVELOPER_GUIDE.md
│   ├── TROUBLESHOOTING.md
│   ├── UAT_HUMAN_INPUT_AND_PAUSE.md
│   └── requirements/             # PRD documents
│
└── requirements.txt              # Python dependencies
```

---

## 🔒 Security Model

**Defense-in-depth** approach (see `security.py` and `client.py`):

### Layer 1: OS-level Sandbox
Bash commands run in isolated environment (prevents filesystem escape)

### Layer 2: Filesystem Restrictions
File operations restricted to project directory only (`Read(./**)`, `Write(./**)`)

### Layer 3: Command Allowlist
Only whitelisted commands permitted:

```python
ALLOWED_COMMANDS = {
    # File inspection
    "ls", "cat", "head", "tail", "wc", "grep",
    # File operations
    "cp", "mkdir", "chmod", "mv", "rm", "touch",
    # Node.js development
    "npm", "npx", "pnpm", "node",
    # Version control
    "git",
    # Browser automation
    "playwright-cli",
    # Process management
    "ps", "lsof", "sleep", "kill", "pkill",
    # Other
    "curl", "docker", "sh", "bash"
}
```

Commands not in allowlist are **blocked** by the security hook.

### Layer 4: Additional Validation
Special validation for sensitive commands:
- `pkill` - Only dev server processes
- `chmod` - No dangerous permissions
- `init.sh` - Environment setup only

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# N8N webhook for progress notifications (optional)
PROGRESS_N8N_WEBHOOK_URL=https://n8n.example.com/webhook/abc123

# Alternative API provider (optional)
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_AUTH_TOKEN=your-api-key
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.7

# Supervisory agent mode (optional)
ENABLE_SUPERVISORY_AGENT=true
SUPERVISORY_AGENT_MODEL=claude-sonnet-4-5

# Playwright settings (optional)
PLAYWRIGHT_HEADLESS=false  # Show browser for monitoring
```

### Using GLM Models (Zhipu AI)

To use GLM models instead of Claude:

```bash
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-key
API_TIMEOUT_MS=3000000
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.7
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.7
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
```

Get API key: https://z.ai/subscribe

**Note:** This only affects AutoCoder. Your global Claude Code settings remain unchanged.

### Project Registry

Projects can be stored anywhere on disk. The registry maps names to paths:

```bash
# Registry location (cross-platform)
~/.autocoder/registry.db

# View registered projects
python start.py  # Shows list in CLI menu
```

Registry uses SQLite with POSIX paths for cross-platform compatibility.

---

## 🎨 UI Development

### Development Mode

```bash
cd ui
npm install
npm run dev      # Hot reload at http://localhost:5173
```

### Production Build

```bash
cd ui
npm run build    # Builds to ui/dist/
```

**Note:** `start_ui.bat`/`start_ui.sh` serve the pre-built UI. Run `npm run build` after UI changes.

### Tech Stack

- **React 18** with TypeScript
- **TanStack Query** for data fetching
- **Tailwind CSS v4** with custom theme (`@theme` directive)
- **Radix UI** components (accessible by default)
- **dagre** for dependency graph layout
- **WebSocket** for real-time updates

### Real-time Updates

WebSocket endpoint: `/ws/projects/{project_name}`

**Message Types:**
```typescript
type WSMessage =
  | { type: "progress"; data: { passing: number; total: number } }
  | { type: "agent_status"; data: "running" | "paused" | "stopped" | "crashed" }
  | { type: "log"; data: string; featureId?: number; agentIndex?: number }
  | { type: "feature_update"; data: Feature }
  | { type: "agent_update"; data: AgentState[] }
```

### Neobrutalism Design

Custom design system with bold borders and vibrant colors:

```css
/* globals.css - @theme directive */
@theme {
  --color-neo-pending: #fbbf24;  /* yellow-400 */
  --color-neo-progress: #06b6d4; /* cyan-500 */
  --color-neo-done: #10b981;     /* green-500 */

  --animate-slide-in: slide-in 0.3s ease-out;
  --animate-pulse-neo: pulse-neo 2s ease-in-out infinite;
}
```

---

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=api --cov=parallel_orchestrator --cov=paths --cov-report=term-missing

# Run specific test files
python -m pytest tests/test_human_input_system.py -v
python -m pytest tests/test_pause_drain_mode.py -v
```

### Test Coverage

Current coverage: **31% overall** (81% for new features)

- `api/database.py`: **81%** - Human input system, migrations
- `paths.py`: **82%** - Pause/drain infrastructure
- `parallel_orchestrator.py`: 14% - Core logic tested (full integration pending)

### UAT Script

Comprehensive user acceptance testing guide:

```bash
cat UAT_HUMAN_INPUT_AND_PAUSE.md
```

**Includes:**
- 5 complete test scenarios (human mode + supervisory agent)
- Configuration instructions
- Test data and expected results
- Success criteria (18 checkpoints)
- Troubleshooting guide
- API reference with examples

---

## ⏱️ Timing Expectations

> **Building complete applications takes time!**

| Phase | Duration | Notes |
|-------|----------|-------|
| **First session (initialization)** | 10-20+ minutes | Generates feature test cases (appears to hang - normal) |
| **Single feature** | 5-15 minutes | Depends on complexity |
| **Full application** | Many hours | Across multiple sessions |
| **Checkpoint review** | 2-5 minutes | Per checkpoint (every N features) |
| **Design iteration** | 5-10 minutes | Per persona review |

**Optimization Tips:**
- Reduce feature count in spec for faster demos (20-50 features)
- Use YOLO mode to skip regression testing (`--yolo`)
- Increase parallel agents for independent features (`--max-concurrency 5`)
- Enable supervisory agent to eliminate human input waits

---

## 🎯 Example Workflows

### Standard Workflow (Human Gates)

```bash
# 1. Create project with human input gates
python start.py
> Create new project
> Name: oauth-demo
> Use /create-spec to define app

# 2. Start agent (will pause for human input)
python autonomous_agent_demo.py --project-dir oauth-demo

# 3. Agent requests OAuth credentials
# Provide via UI: http://localhost:5173

# 4. Agent continues with credentials
# Checkpoint runs every 10 features
# Human reviews checkpoint report before continuing
```

### Full Automation (Supervisory Agent)

```bash
# 1. Enable supervisory agent
export ENABLE_SUPERVISORY_AGENT=true

# 2. Start with YOLO mode + parallel execution
python autonomous_agent_demo.py \
  --project-dir oauth-demo \
  --yolo \
  --parallel \
  --max-concurrency 3 \
  --supervisory-agent

# 3. Fully automated (no human intervention)
# - Supervisory agent provides mock credentials
# - YOLO mode skips regression tests
# - Parallel execution maximizes speed
# - Checkpoints still run (can auto-continue)
```

### Quality-First Workflow

```bash
# 1. Standard mode with checkpoints
python autonomous_agent_demo.py --project-dir my-app

# 2. Checkpoint review every 10 features
# Reports in: checkpoints/checkpoint_N.md

# 3. Design iteration after major milestones
python design/review.py --project-dir my-app --iteration 1

# 4. Metrics dashboard
python metrics/dashboard.py --project-dir my-app

# 5. Final performance report
python metrics/report_generator.py --project-dir my-app
```

---

## 🐛 Troubleshooting

### Common Issues

**"Claude CLI not found"**
```bash
# Install Claude CLI
curl -fsSL https://claude.ai/install.sh | bash  # macOS/Linux
irm https://claude.ai/install.ps1 | iex         # Windows
```

**"Not authenticated with Claude"**
```bash
claude login
```

**"Appears to hang on first run"**
- Normal! Initializer generates detailed test cases (10-20 minutes)
- Watch for `[Tool: ...]` output to confirm agent is working
- Check `agent_output.log` for progress

**"Command blocked by security hook"**
- Agent tried to run command not in allowlist
- Security system working as intended
- Add to `ALLOWED_COMMANDS` in `security.py` if needed

**"Feature awaiting human input - agent stuck"**
```bash
# Check which features need input
curl http://localhost:8000/api/projects/my-app/features/human-input

# Provide response
curl -X POST http://localhost:8000/api/projects/my-app/features/1/human-input \
  -H "Content-Type: application/json" \
  -d '{"field_id": "value"}'

# Or use supervisory agent mode
export ENABLE_SUPERVISORY_AGENT=true
```

**"Pause not working - agents still running"**
```bash
# Check pause signal file
ls -la <project-dir>/.autocoder/.pause_drain

# Check orchestrator logs
tail -f agent_output.log | grep -i drain

# Verify process manager
curl http://localhost:8000/api/projects/my-app/agent/status
```

**"Playwright CLI commands failing"**
```bash
# Install Playwright browsers
npx playwright install

# Check playwright-cli is in PATH
which playwright-cli  # macOS/Linux
where playwright-cli  # Windows

# Verify in security allowlist
grep playwright-cli security.py
```

**"Database locked errors"**
- Multiple processes accessing `features.db`
- Stop agent before running manual queries
- Check for stale `.agent.lock` file

**"UI not showing latest features"**
```bash
# Rebuild UI
cd ui && npm run build

# Or use dev mode
cd ui && npm run dev
```

### Debug Logging

```bash
# Enable debug output
export DEBUG=1

# Check logs
tail -f agent_output.log
tail -f .autocoder/debug.log

# WebSocket debugging (browser console)
# Enable: localStorage.debug = 'socket.io-client:*'
```

### Getting Help

1. Check `docs/TROUBLESHOOTING.md`
2. Review test files in `tests/` for examples
3. Read UAT script: `UAT_HUMAN_INPUT_AND_PAUSE.md`
4. Check GitHub issues
5. Review prompt templates in `.claude/templates/`

---

## 📚 Documentation

Comprehensive docs in `docs/`:

- **[DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** - Contributing guide
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues & fixes
- **[SKIP_MANAGEMENT_USER_GUIDE.md](docs/SKIP_MANAGEMENT_USER_GUIDE.md)** - Skip management
- **[UAT_HUMAN_INPUT_AND_PAUSE.md](UAT_HUMAN_INPUT_AND_PAUSE.md)** - UAT for new features
- **[PRD_TO_IMPLEMENTATION_MAPPING.md](docs/PRD_TO_IMPLEMENTATION_MAPPING.md)** - Feature tracking

---

## 🗺️ Roadmap

### Completed Features
- ✅ Human input system with supervisory agent mode
- ✅ Pause/drain mode for graceful shutdown
- ✅ Playwright CLI integration (simpler than MCP)
- ✅ Checkpoint system with auto-fix
- ✅ Design iteration with multi-persona review
- ✅ Parallel execution with dependency resolution
- ✅ Metrics dashboard and ROI analysis
- ✅ Skip management with blocker classification
- ✅ React UI with real-time WebSocket updates

### Future Enhancements
- 🔄 UI for human input requests (modal/form)
- 🔄 UI for checkpoint review and approval
- 🔄 Design iteration UI with persona feedback
- 🔄 Enhanced supervisory agent with learning
- 🔄 Multi-project batch processing
- 🔄 Cloud deployment (Docker + Kubernetes)
- 🔄 Team collaboration features
- 🔄 Advanced scheduling (time-based runs)

---

## 📜 License

This project is licensed under the **GNU Affero General Public License v3.0**.

See [LICENSE.md](LICENSE.md) for full details.

**Copyright (C) 2026 Leon van Zyl**
https://leonvanzyl.com

---

## 🙏 Attribution

This project builds upon the original autonomous coding agent by Leon van Zyl, enhanced with enterprise-grade features including:

- Human-in-the-loop controls (human input gates + supervisory agents)
- Graceful pause/drain mode
- Checkpoint system for automated quality review
- Design iteration workflow with multi-persona review
- Parallel execution with dependency-aware scheduling
- Comprehensive metrics and performance tracking
- Playwright CLI integration (replacing MCP server)
- Production-ready security and testing

**Original Project:** https://github.com/leonvanzyl/autonomous-coding
**Created by:** Leon van Zyl (https://leonvanzyl.com)

**Enhanced Fork:** https://github.com/ArchitectVS7/autocoder-2

Special thanks to the open-source community and the Anthropic team for the Claude Agent SDK.

---

**Built with ❤️ for developers who ship production-quality code faster.**
