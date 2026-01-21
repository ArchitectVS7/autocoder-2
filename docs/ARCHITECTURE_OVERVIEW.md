# Architecture Overview

**High-level system design and technology stack**

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [System Overview](#system-overview)
- [Core Value Proposition](#core-value-proposition)
- [Architecture Layers](#architecture-layers)
  - [1. UI Layer (React)](#1-ui-layer-react)
  - [2. API Layer (FastAPI)](#2-api-layer-fastapi)
  - [3. Agent Core](#3-agent-core)
  - [4. State Management](#4-state-management)
  - [5. Orchestration](#5-orchestration)
- [Technology Stack](#technology-stack)
- [Two-Agent Pattern](#two-agent-pattern)
- [Security Model (Defense-in-Depth)](#security-model-defense-in-depth)
- [MCP Server Architecture](#mcp-server-architecture)
- [Prompt System](#prompt-system)
- [Data Flow](#data-flow)
- [Parallel Execution Architecture](#parallel-execution-architecture)
- [Database Design](#database-design)
- [Component Interaction Diagrams](#component-interaction-diagrams)
- [Design Patterns](#design-patterns)
- [Scalability Considerations](#scalability-considerations)

---

## Executive Summary

**Autocoder-2** is a long-running autonomous coding agent system that builds complete web applications from specifications over multiple sessions. Unlike traditional code generation tools that produce one-off snippets, this system:

1. **Maintains persistent state** across sessions via SQLite database
2. **Tracks progress** through a feature-based test system
3. **Handles blockers** gracefully with Skip Management
4. **Runs multiple agents concurrently** with dependency-aware scheduling
5. **Provides quality gates** via checkpoint agents (code review, security, performance)
6. **Offers real-time monitoring** through a React-based Web UI

**Key Architecture Principles:**
- **Separation of concerns**: Orchestration ↔ Agent ↔ State ↔ API ↔ UI
- **Defense-in-depth**: Three-layer security (sandbox, permissions, allowlist)
- **Observability**: Real-time WebSocket updates, debug logging, metrics
- **Resilience**: Timeout handling, process cleanup, atomic database operations
- **Extensibility**: MCP servers, persona system, checkpoint agents

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        React Web UI                         │
│  (Real-time dashboard, Kanban board, Dependency graph)      │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket + REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Server                           │
│  (Project mgmt, Agent control, Filesystem API, Webhooks)    │
└──────────────────────────┬──────────────────────────────────┘
                           │ Process spawning
┌──────────────────────────▼──────────────────────────────────┐
│                  Parallel Orchestrator                      │
│  (Dependency-aware scheduling, Process management)          │
└─────┬──────────┬──────────┬──────────┬──────────────────────┘
      │          │          │          │
  ┌───▼───┐  ┌──▼───┐  ┌──▼───┐  ┌──▼───┐
  │Coding │  │Coding│  │Coding│  │Testing│
  │Agent 1│  │Agent2│  │Agent3│  │Agent  │
  └───┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
      │         │         │         │
      │    Claude Agent SDK (MCP Servers)
      │         │         │         │
  ┌───▼─────────▼─────────▼─────────▼───┐
  │    Feature MCP     Playwright MCP    │
  └───────────┬─────────────────────┘
              │
  ┌───────────▼──────────────┐
  │    SQLite Database       │
  │  (features, dependencies)│
  └──────────────────────────┘
```

**Component Responsibilities:**

| Layer | Responsibility | Technology |
|-------|---------------|------------|
| **UI** | User interaction, visualization | React, TailwindCSS, TanStack Query |
| **API** | REST endpoints, WebSocket, project management | FastAPI, Uvicorn |
| **Orchestrator** | Agent lifecycle, dependency scheduling | Python async, psutil |
| **Agent** | Feature implementation, testing | Claude Agent SDK |
| **MCP Servers** | Tool exposure (database, browser) | FastMCP, Playwright |
| **Database** | Feature state, dependencies, metrics | SQLAlchemy, SQLite |

---

## Core Value Proposition

### What Makes This Different from Code Generation Tools?

**Traditional code generators:**
- Generate code snippets on demand
- No memory between requests
- No progress tracking
- No quality gates
- No parallel execution

**Autocoder-2:**
- **Long-running sessions**: Agent works until all features complete
- **Persistent state**: SQLite database tracks progress across sessions
- **Feature-based testing**: Each feature has verification steps
- **Quality checkpoints**: Code review, security audit, performance analysis
- **Parallel orchestration**: Up to 5 concurrent agents with dependency management
- **Skip Management**: Gracefully handles blockers (dependencies, human intervention, tech prerequisites)
- **Observability**: Real-time dashboard, WebSocket updates, debug logs, metrics

**Use Cases:**
1. **Rapid MVP Development**: Spec → working app in hours, not days
2. **Refactoring**: Systematic code improvements with regression testing
3. **Feature Addition**: Add capabilities to existing apps without breaking functionality
4. **Learning**: Generate reference implementations for study

---

## Architecture Layers

### 1. UI Layer (React)

**Location:** `ui/` directory

**Stack:**
- React 18 (functional components, hooks)
- TypeScript (strict type checking)
- TailwindCSS v4 (neobrutalism design system)
- TanStack Query (server state management)
- Radix UI (accessible primitives)
- dagre (graph layout for dependency visualization)

**Key Components:**

| Component | Purpose | File |
|-----------|---------|------|
| `App.tsx` | Main app shell, routing | `ui/src/App.tsx` |
| `ProjectSelector` | Project creation/selection | `ui/src/components/ProjectSelector.tsx` |
| `KanbanBoard` | Feature progress visualization | `ui/src/components/KanbanBoard.tsx` |
| `DependencyGraph` | Interactive dependency graph | `ui/src/components/DependencyGraph.tsx` |
| `AgentMissionControl` | Multi-agent dashboard | `ui/src/components/AgentMissionControl.tsx` |
| `Terminal` | Live agent output stream | `ui/src/components/Terminal.tsx` |
| `DebugPanel` | Advanced diagnostics | `ui/src/components/DebugPanel.tsx` |

**State Management:**

```typescript
// Server state (TanStack Query)
const { data: features } = useFeatures(projectName)
const { data: project } = useProject(projectName)

// WebSocket state (custom hook)
const { agentStatus, progress, agents } = useWebSocket(projectName)

// Local UI state (React hooks)
const [view, setView] = useState<'kanban' | 'graph'>('kanban')
```

**Design System:**

```css
/* globals.css */
@theme {
  --color-neo-pending: #fbbf24;    /* Yellow */
  --color-neo-progress: #06b6d4;   /* Cyan */
  --color-neo-done: #10b981;       /* Green */
  --border-neo: 3px solid black;
}
```

**Keyboard Shortcuts:**
- `D` - Toggle debug panel
- `G` - Toggle Kanban/Graph view
- `N` - Add new feature
- `A` - Toggle AI assistant
- `,` - Open settings
- `?` - Show help

### 2. API Layer (FastAPI)

**Location:** `server/` directory

**Stack:**
- FastAPI (async Python web framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)
- SQLAlchemy (ORM)
- WebSockets (real-time updates)

**Routers:**

| Router | Endpoint Prefix | Purpose | File |
|--------|----------------|---------|------|
| `projects` | `/api/projects` | CRUD operations | `server/routers/projects.py` |
| `features` | `/api/features` | Feature management | `server/routers/features.py` |
| `agent` | `/api/agent` | Start/stop/pause agents | `server/routers/agent.py` |
| `filesystem` | `/api/filesystem` | Browse directories | `server/routers/filesystem.py` |
| `terminal` | `/api/terminal` | Terminal emulation | `server/routers/terminal.py` |
| `spec_creation` | `/api/spec-creation` | Interactive spec builder | `server/routers/spec_creation.py` |

**WebSocket Protocol:**

```python
# Connection: ws://localhost:8000/ws/projects/{project_name}

# Message types sent to client:
{
  "type": "progress",
  "data": {"passing": 10, "in_progress": 2, "total": 30}
}

{
  "type": "agent_status",
  "data": {"status": "running" | "paused" | "stopped"}
}

{
  "type": "log",
  "data": {"line": "...", "featureId": 42, "agentIndex": 0}
}

{
  "type": "feature_update",
  "data": {"id": 42, "passes": true, "in_progress": false}
}

{
  "type": "agent_update",
  "data": {
    "agentIndex": 0,
    "state": "thinking" | "working" | "testing" | "success" | "error",
    "featureId": 42,
    "featureName": "User Authentication",
    "thought": "Implementing auth middleware..."
  }
}
```

**Authentication:**

Currently **not implemented** (all endpoints are open). Future versions will add:
- JWT-based authentication
- Project-level access control
- API key management

**CORS Configuration:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # UI dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Agent Core

**Location:** `agent.py`, `client.py`, `autonomous_agent_demo.py`

**ClaudeSDKClient Configuration:**

```python
client = ClaudeSDKClient(
    options=ClaudeAgentOptions(
        model="claude-sonnet-4",
        cli_path="/usr/local/bin/claude",  # System Claude CLI
        system_prompt="You are an expert full-stack developer...",
        setting_sources=["project"],  # Enable CLAUDE.md, skills, commands
        max_buffer_size=10 * 1024 * 1024,  # 10MB (for Playwright screenshots)
        allowed_tools=[...BUILTIN_TOOLS, ...FEATURE_MCP_TOOLS, ...PLAYWRIGHT_TOOLS],
        mcp_servers={
            "features": {...},      # Feature management MCP
            "playwright": {...},    # Browser automation MCP
        },
        hooks={
            "PreToolUse": [HookMatcher(matcher="Bash", hooks=[bash_security_hook])],
        },
        max_turns=1000,
        cwd=str(project_dir.resolve()),
        settings=str(settings_file.resolve()),  # .claude_settings.json
    )
)
```

**Agent Types:**

| Agent Type | Purpose | Prompt | Max Iterations |
|------------|---------|--------|----------------|
| **Initializer** | Create features from app_spec | `initializer_prompt.md` | 1 |
| **Coding** | Implement features | `coding_prompt.md` | 1 (orchestrator) / ∞ (standalone) |
| **Testing** | Regression testing | `testing_prompt.md` | 1 |

**Session Loop:**

```python
async with client:
    await client.query(prompt)

    async for msg in client.receive_response():
        # Handle AssistantMessage (text, tool use)
        # Handle UserMessage (tool results)

    # Session ends when agent stops using tools
```

**Auto-Continue:**

Between sessions, the agent pauses for 3 seconds:

```python
AUTO_CONTINUE_DELAY_SECONDS = 3

# After session completes:
await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)
# Start next session
```

### 4. State Management

**Location:** `api/database.py`, SQLite (`features.db`)

**SQLAlchemy Models:**

```python
class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True)
    priority = Column(Integer, nullable=False, index=True)
    category = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    steps = Column(JSON, nullable=False)  # list[str]
    passes = Column(Boolean, default=False, index=True)
    in_progress = Column(Boolean, default=False, index=True)
    skip_count = Column(Integer, default=0)
    dependencies = Column(JSON, default=list)  # list[int] - feature IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Additional Models:**

- `FeatureDependency` - Many-to-many relationship table
- `FeatureAssumption` - Assumptions made when building on skipped features
- `FeatureBlocker` - Blocker classification (ENV_CONFIG, EXTERNAL_SERVICE, etc.)
- `SkipImpact` - Impact analysis for skipped features

**Database Operations:**

```python
# Create engine and session maker
engine, session_maker = create_database(project_dir)

# Get a session
session = session_maker()

# Query features
features = session.query(Feature).filter(Feature.passes == False).all()

# Commit changes
session.commit()
session.close()

# Critical: Dispose engine after subprocess commits
engine.dispose()  # Refreshes connection pool to see new data
```

### 5. Orchestration

**Location:** `parallel_orchestrator.py`

**Key Responsibilities:**

1. **Initialization Phase**
   - Check if `features.db` exists
   - Spawn initializer agent if needed (timeout: 30 minutes)
   - Recreate database engine after initialization

2. **Feature Loop**
   - Poll for ready features every 5 seconds (`POLL_INTERVAL`)
   - Compute scheduling scores (dependency-aware)
   - Start coding agents up to `max_concurrency` limit
   - Spawn testing agents after coding success (based on `testing_agent_ratio`)
   - Clean up processes on completion

3. **Process Management**
   - Spawn agents as subprocesses (`subprocess.Popen`)
   - Stream stdout/stderr with threading
   - Kill entire process trees on shutdown (`_kill_process_tree` with psutil)
   - Track failure counts (max 3 retries per feature)

**Concurrency Limits:**

```python
MAX_PARALLEL_AGENTS = 5      # Concurrent coding agents
MAX_TOTAL_AGENTS = 10         # Total agents (coding + testing)
DEFAULT_CONCURRENCY = 3
POLL_INTERVAL = 5             # seconds
MAX_FEATURE_RETRIES = 3
INITIALIZER_TIMEOUT = 1800    # 30 minutes
```

**Process Lifecycle:**

```python
# 1. Spawn subprocess
proc = subprocess.Popen(
    [sys.executable, "-u", "autonomous_agent_demo.py",
     "--project-dir", str(project_dir),
     "--agent-type", "coding",
     "--feature-id", str(feature_id),
     "--max-iterations", "1"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

# 2. Stream output (thread)
threading.Thread(target=_read_output, args=(feature_id, proc, abort_event, "coding"), daemon=True).start()

# 3. On completion (_on_agent_complete)
#    - Clear in_progress in database
#    - Dispose engine (refresh connections)
#    - Track failure count
#    - Spawn testing agents if success

# 4. On shutdown (_kill_process_tree)
#    - Get all child processes (recursive)
#    - Terminate children (graceful)
#    - Wait with timeout
#    - Force kill remaining
#    - Terminate parent
```

---

## Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Core language |
| **Claude Agent SDK** | Latest | AI agent orchestration |
| **FastAPI** | 0.100+ | Web API framework |
| **SQLAlchemy** | 2.0+ | ORM |
| **SQLite** | 3.x | Database |
| **psutil** | 5.9+ | Process management |
| **Pydantic** | 2.0+ | Data validation |
| **Uvicorn** | Latest | ASGI server |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.x | UI framework |
| **TypeScript** | 5.x | Type safety |
| **TailwindCSS** | 4.x | Styling |
| **TanStack Query** | Latest | Server state |
| **Radix UI** | Latest | Accessible components |
| **dagre** | Latest | Graph layout |
| **Vite** | Latest | Build tool |

### MCP Servers

| Server | Technology | Purpose |
|--------|-----------|---------|
| **features** | FastMCP (Python) | Feature management |
| **playwright** | `@playwright/mcp` (Node) | Browser automation |

### Infrastructure

| Tool | Purpose |
|------|---------|
| **npm/pnpm** | Package management |
| **Docker** | PostgreSQL (optional) |
| **Git** | Version control |
| **pytest** | Testing |

---

## Two-Agent Pattern

The system uses a **two-agent pattern** to separate initialization from implementation:

### Initializer Agent

**Purpose:** Create features from application specification (first run only)

**Trigger:** `features.db` doesn't exist

**Process:**
1. Read `prompts/app_spec.txt` (XML format)
2. Parse `<project_specification>` into features
3. Call `feature_create_bulk` with all features
4. Create `features.db` with SQLite
5. Exit

**Timeout:** 30 minutes

**Prompt:** `initializer_prompt.md` (or `.claude/templates/initializer_prompt.template.md`)

**Example Output:**

```
Created 30 features in database:
  #1: User Authentication (priority: 1)
  #2: Database Models (priority: 2)
  #3: API Endpoints (priority: 3)
  ...
```

### Coding Agent

**Purpose:** Implement features one-by-one, mark as passing/failing

**Trigger:** Every run after initialization

**Process:**
1. Call `feature_get_next` or `feature_claim_next` (parallel mode)
2. Read feature details (description, steps, dependencies)
3. Implement code (write files, run commands)
4. Verify implementation (lint, type-check, browser tests)
5. Call `feature_mark_passing` or `feature_skip`
6. Commit changes
7. Repeat until all features pass

**Timeout:** Unlimited (exits after `--max-iterations` or no more features)

**Prompt:** `coding_prompt.md` (or `single_feature_prompt.md` for parallel mode)

**Parallelization:** Orchestrator spawns up to 5 concurrent coding agents

### Testing Agent

**Purpose:** Regression testing on passing features

**Trigger:** After a coding agent successfully completes (if `testing_agent_ratio > 0`)

**Process:**
1. Call `feature_get_for_regression` (limit: 3 random passing features)
2. Re-run verification steps
3. Call `feature_mark_failing` if regression detected
4. Exit after one session

**Prompt:** `testing_prompt.md`

---

## Security Model (Defense-in-Depth)

**Three-layer security** to prevent malicious/accidental damage:

### Layer 1: OS-Level Sandbox

```python
security_settings = {
    "sandbox": {
        "enabled": True,
        "autoAllowBashIfSandboxed": True
    }
}
```

- Bash commands run in isolated environment
- Prevents filesystem escape (access outside project directory)
- OS-enforced constraints

### Layer 2: Filesystem Permissions

```python
"permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
        "Read(./**)",
        "Write(./**)",
        "Edit(./**)",
        "Glob(./**)",
        "Grep(./**)",
        "Bash(*)",  # Validated by Layer 3
        "WebFetch",
        "WebSearch",
        ...FEATURE_MCP_TOOLS,
        ...PLAYWRIGHT_TOOLS,  # Standard mode only
    ]
}
```

- File operations restricted to `./**` (current project directory)
- `cwd` set to `project_dir` ensures relative paths stay within project
- Absolute paths outside project are blocked

### Layer 3: Bash Command Allowlist

```python
# security.py
ALLOWED_COMMANDS = {
    # File inspection
    "ls", "cat", "head", "tail", "wc", "grep",
    # File operations
    "cp", "mkdir", "chmod",
    # Node.js development
    "npm", "npx", "pnpm", "node",
    # Version control
    "git",
    # Docker (for PostgreSQL)
    "docker",
    # Process management
    "ps", "lsof", "sleep", "kill", "pkill",
    # Network/API testing
    "curl",
    # File operations
    "mv", "rm", "touch",
    # Shell scripts
    "sh", "bash",
    # Project-specific
    "init.sh",
}
```

**Pre-tool-use hook** validates every Bash command:

```python
@PreToolUse("Bash")
async def bash_security_hook(input_data, tool_use_id, context):
    command = input_data["tool_input"]["command"]
    commands = extract_commands(command)

    for cmd in commands:
        if cmd not in ALLOWED_COMMANDS:
            return {"decision": "block", "reason": f"Command '{cmd}' not allowed"}

    # Additional validation for sensitive commands
    if "pkill" in commands:
        validate_pkill_command(command)  # Only allow dev processes
    if "chmod" in commands:
        validate_chmod_command(command)  # Only allow +x

    return {}  # Allow
```

**Why three layers?**
- **Redundancy**: If one layer fails, others provide protection
- **Different threat models**: Sandbox stops exploits, permissions stop mistakes, allowlist stops misuse
- **Observability**: Each layer logs violations

---

## MCP Server Architecture

**Model Context Protocol (MCP)** servers expose tools to the agent.

### Feature MCP Server

**Location:** `mcp_server/feature_mcp.py`

**Purpose:** Feature management (database CRUD, dependencies, progress tracking)

**Implementation:** FastMCP (Python)

**Startup:**

```python
mcp_servers["features"] = {
    "command": sys.executable,  # Same Python as main process
    "args": ["-m", "mcp_server.feature_mcp"],
    "env": {
        "PROJECT_DIR": str(project_dir.resolve()),
        "PYTHONPATH": str(Path(__file__).parent.resolve()),
    }
}
```

**Exposed Tools:**

| Tool | Purpose | Critical For |
|------|---------|--------------|
| `feature_get_stats` | Progress statistics | Dashboard |
| `feature_get_next` | Get next feature (dependency-aware) | Single-agent mode |
| `feature_claim_next` | **Atomic get+claim** | Parallel mode |
| `feature_mark_passing` | Mark feature complete | Progress tracking |
| `feature_skip` | Defer feature | Skip Management |
| `feature_create_bulk` | Initialize features | Initializer agent |
| `feature_add_dependency` | Add dependency (with cycle detection) | Dependency management |
| `feature_remove_dependency` | Remove dependency | Blocker resolution |

**Atomic Claiming** (prevents race conditions):

```python
@mcp.tool()
def feature_claim_next() -> str:
    """Atomically claim next ready feature (for parallel execution)."""
    with _priority_lock:  # In-process safety
        candidate_id = select_highest_priority_ready_feature()

        # Atomic SQL operation (cross-process safety)
        result = session.execute(
            text("UPDATE features SET in_progress = 1 WHERE id = :id AND in_progress = 0"),
            {"id": candidate_id}
        )

        if result.rowcount == 0:
            # Another agent claimed it, retry
            return feature_claim_next_internal(attempt + 1)

        return json.dumps(feature.to_dict())
```

### Playwright MCP Server

**Location:** `@playwright/mcp` (npm package)

**Purpose:** Browser automation for testing

**Implementation:** Node.js, Playwright

**Startup:**

```python
mcp_servers["playwright"] = {
    "command": "npx",
    "args": ["@playwright/mcp@latest", "--viewport-size", "1280x720", "--isolated"],
}
```

**Exposed Tools:**

| Category | Tools |
|----------|-------|
| **Navigation** | `browser_navigate`, `browser_navigate_back`, `browser_take_screenshot` |
| **Interaction** | `browser_click`, `browser_type`, `browser_fill_form`, `browser_select_option` |
| **JavaScript** | `browser_evaluate`, `browser_console_messages` |
| **Management** | `browser_close`, `browser_resize`, `browser_wait_for` |

**Browser Isolation (Parallel Mode):**

```python
if agent_id:  # e.g., "feature-42"
    playwright_args.append("--isolated")
```

- Each agent gets ephemeral browser context
- No persistent state (cookies, localStorage) between agents
- Prevents tab conflicts

**YOLO Mode:**

Playwright MCP server is **disabled** in YOLO mode:

```python
if not yolo_mode:
    mcp_servers["playwright"] = {...}
```

---

## Prompt System

**Location:** `prompts.py`, `.claude/templates/`

**Fallback Chain:**

```
1. Project-specific: {project_dir}/prompts/{name}.md
2. Base template: .claude/templates/{name}.template.md
```

**Loading Logic:**

```python
def load_prompt(name: str, project_dir: Path | None = None) -> str:
    # Try project-specific first
    if project_dir:
        project_path = project_dir / "prompts" / f"{name}.md"
        if project_path.exists():
            return project_path.read_text()

    # Fallback to base template
    template_path = TEMPLATES_DIR / f"{name}.template.md"
    if template_path.exists():
        return template_path.read_text()

    raise FileNotFoundError(f"Prompt '{name}' not found")
```

**Available Prompts:**

| Prompt | Use Case | Template File |
|--------|----------|---------------|
| `initializer_prompt` | Feature creation | `initializer_prompt.template.md` |
| `coding_prompt` | Feature implementation | `coding_prompt.template.md` |
| `testing_prompt` | Regression testing | `testing_prompt.template.md` |
| `single_feature_prompt` | Parallel agent (specific feature) | Generated dynamically |

**Single-Feature Prompt (Parallel Mode):**

```python
def get_single_feature_prompt(feature_id: int, project_dir: Path, yolo_mode: bool) -> str:
    base_prompt = get_coding_prompt(project_dir)

    header = f"""## SINGLE FEATURE MODE

**CRITICAL: You are assigned to work on Feature #{feature_id} ONLY.**

You MUST:
1. Skip `feature_get_next` - Your feature is assigned: #{feature_id}
2. Immediately mark #{feature_id} as in-progress
3. Focus ONLY on implementing #{feature_id}
4. Do NOT work on other features (other agents are handling them)

---

"""
    return header + base_prompt
```

**Persona-Enhanced Prompts (Phase 0):**

```python
def get_coding_prompt_with_persona(feature: dict, project_dir: Path) -> str:
    base_prompt = get_coding_prompt(project_dir)
    feature_type = detect_feature_type(feature)  # security, ui_ux, api, data, etc.

    persona_addon = ""
    if feature_type == "security":
        persona_addon = SECURITY_PERSONA
    elif feature_type == "ui_ux":
        persona_addon = UX_PERSONA
    elif feature_type == "api":
        persona_addon = API_PERSONA
    elif feature_type == "data":
        persona_addon = DATA_PERSONA

    enhanced_prompt = base_prompt + "\n" + persona_addon + "\n" + CRAFTSMANSHIP_MINDSET
    return enhanced_prompt
```

---

## Data Flow

### 1. Initialization Flow

```
User → start.py
  → Creates project, registers in registry
  → Scaffolds prompts/ directory
  → User edits prompts/app_spec.txt

User → autonomous_agent_demo.py --project-dir my-app
  → Orchestrator checks: has_features(my-app)? NO
  → Spawns initializer agent subprocess
  → Initializer reads app_spec.txt
  → Initializer calls feature_create_bulk
  → Feature MCP writes to features.db
  → Initializer exits
  → Orchestrator recreates database engine
  → Proceeds to coding phase
```

### 2. Coding Flow (Single Agent)

```
Orchestrator → Spawns coding agent subprocess
  → Agent calls feature_get_next
  → Feature MCP queries features.db (dependency-aware)
  → Returns highest-priority ready feature

Agent → Reads feature details
  → Implements code (Write, Edit, Bash tools)
  → Runs verification (npm run lint, tsc --noEmit)
  → Optionally tests in browser (Playwright MCP)
  → Calls feature_mark_passing
  → Commits changes with git
  → Agent exits

Orchestrator → Detects agent completion
  → Disposes database engine
  → Spawns next coding agent
  → Repeat until all features pass
```

### 3. Coding Flow (Parallel Mode)

```
Orchestrator → Spawns 3 coding agents concurrently
  → Agent 1 calls feature_claim_next → Claims Feature #3
  → Agent 2 calls feature_claim_next → Claims Feature #7
  → Agent 3 calls feature_claim_next → Claims Feature #12

Each agent works independently:
  → Agent 1 implements Feature #3 in parallel with others
  → Agent 1 marks Feature #3 passing
  → Agent 1 exits

Orchestrator → Detects Agent 1 completion
  → Disposes database engine (refresh connections)
  → Spawns 1 testing agent (testing_agent_ratio=1)
  → Spawns new coding agent for next ready feature
```

### 4. Testing Flow

```
Orchestrator → Spawns testing agent after coding success
  → Testing agent calls feature_get_for_regression (limit: 3)
  → Feature MCP returns 3 random passing features

Testing agent → For each feature:
  → Re-run verification steps
  → If failure detected: feature_mark_failing
  → Testing agent exits

Orchestrator → Detects testing completion
  → Continues coding/testing cycle
```

### 5. WebSocket Flow

```
Orchestrator → Agent output reader thread
  → Calls on_output(feature_id, line)
  → WebSocket manager broadcasts:
      {"type": "log", "data": {"line": "...", "featureId": 42}}

Agent → feature_mark_passing tool use
  → Feature MCP updates features.db
  → Returns success
  → Agent continues
  → (WebSocket manager independently polls DB)

WebSocket manager → Polls features.db every 1 second
  → Detects feature.passes changed
  → Broadcasts:
      {"type": "feature_update", "data": {"id": 42, "passes": true}}
      {"type": "progress", "data": {"passing": 11, "total": 30}}

React UI → Receives WebSocket messages
  → Updates TanStack Query cache
  → Re-renders components
  → User sees real-time progress
```

---

## Parallel Execution Architecture

**See [PARALLEL_EXECUTION_GUIDE.md](PARALLEL_EXECUTION_GUIDE.md) for comprehensive details.**

**Key Components:**

1. **Orchestrator** (`parallel_orchestrator.py`)
   - Spawns up to 5 concurrent coding agents
   - Computes dependency-aware scheduling scores
   - Manages process lifecycle (spawn, monitor, cleanup)

2. **Atomic Feature Claiming** (`feature_claim_next`)
   - SQL UPDATE with WHERE condition (cross-process atomicity)
   - Thread lock for in-process safety
   - Retry logic (max 10 attempts)

3. **Dependency-Aware Scheduling** (`compute_scheduling_scores`)
   - Priority boost for features with dependents
   - Priority penalty for frequently skipped features
   - Only start features when dependencies satisfied

4. **Process Isolation**
   - Unique `agent_id` per agent (e.g., `feature-42`)
   - Isolated browser contexts (`--isolated` flag)
   - Separate stdout/stderr streams

5. **Database Connection Management**
   - Engine disposal after subprocess commits
   - Forces fresh connections that see new data
   - Prevents stale read issues

**Concurrency Model:**

```
MAX_PARALLEL_AGENTS = 5      # Hard limit (memory/stability)
MAX_TOTAL_AGENTS = 10         # Total (coding + testing)
DEFAULT_CONCURRENCY = 3
```

---

## Database Design

### Feature Table

```sql
CREATE TABLE features (
    id INTEGER PRIMARY KEY,
    priority INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    steps JSON NOT NULL,  -- list[str]
    passes BOOLEAN DEFAULT 0,
    in_progress BOOLEAN DEFAULT 0,
    skip_count INTEGER DEFAULT 0,
    dependencies JSON DEFAULT '[]',  -- list[int] - feature IDs
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_features_priority ON features(priority);
CREATE INDEX ix_features_passes ON features(passes);
CREATE INDEX ix_features_in_progress ON features(in_progress);
```

**Indexes:**
- `priority`: For sorting ready features
- `passes`: For filtering passing vs pending
- `in_progress`: For detecting claimed features

### Relationships

```python
# Many-to-many dependencies
feature.dependencies = [3, 7, 12]  # Depends on Features #3, #7, #12

# Self-referential (feature depends on other features)
Feature.id=5 → dependencies=[3, 4]  # Feature #5 depends on #3 and #4
```

**Cycle Detection:**

```python
def would_create_circular_dependency(feature_id: int, new_dependency_id: int, all_features: list[dict]) -> bool:
    """DFS to detect cycles."""
    # Build adjacency list
    graph = build_dependency_graph(all_features)

    # Add hypothetical edge
    graph[feature_id].append(new_dependency_id)

    # DFS from new_dependency_id
    visited = set()
    def dfs(node):
        if node == feature_id:
            return True  # Cycle detected!
        if node in visited:
            return False
        visited.add(node)
        for neighbor in graph[node]:
            if dfs(neighbor):
                return True
        return False

    return dfs(new_dependency_id)
```

---

## Component Interaction Diagrams

### 1. Initialization Sequence

```
User → start.py → Create project
     → Scaffold prompts/
     → Edit prompts/app_spec.txt

User → autonomous_agent_demo.py → Orchestrator
     → has_features()? → NO
     → Spawn initializer subprocess
         → Initializer agent
             → Read app_spec.txt
             → feature_create_bulk
                 → Feature MCP
                     → SQLAlchemy
                         → features.db
             → Exit
     → Orchestrator: Dispose engine
     → Orchestrator: Recreate engine
     → Proceed to coding loop
```

### 2. Parallel Coding Sequence

```
Orchestrator → run_loop()
  → get_ready_features() → [#3, #7, #12, #15, ...]
  → Spawn 3 coding agents:

    Agent 1 → feature_claim_next → Claim #3 → Implement → Mark passing → Exit
    Agent 2 → feature_claim_next → Claim #7 → Implement → Mark passing → Exit
    Agent 3 → feature_claim_next → Claim #12 → Implement → Mark passing → Exit

  → Agent 1 completes → _on_agent_complete
      → Dispose engine
      → Spawn testing agent (if testing_agent_ratio > 0)
      → Spawn new coding agent for #15

  → Loop continues until all features pass
```

### 3. WebSocket Update Sequence

```
Agent → feature_mark_passing(42) → Feature MCP
  → SQLAlchemy → features.db UPDATE

WebSocket Manager (polling every 1s)
  → Query features.db
  → Detect Feature #42: passes=true (changed)
  → Broadcast: {"type": "feature_update", ...}
  → Broadcast: {"type": "progress", "passing": 11, "total": 30}

React UI (connected to WebSocket)
  → Receives messages
  → Updates TanStack Query cache
  → Triggers re-render
  → KanbanBoard moves Feature #42 from "In Progress" to "Done"
  → CelebrationOverlay shows confetti
```

---

## Design Patterns

### 1. Orchestrator Pattern

**Centralized control** of agent lifecycle, dependency scheduling, and resource management.

**Benefits:**
- Single source of truth for orchestration logic
- Easy to add new agent types
- Scalable (spawn more agents)

**Files:** `parallel_orchestrator.py`, `autonomous_agent_demo.py`

### 2. MCP Server Pattern

**Tool exposure** via Model Context Protocol servers.

**Benefits:**
- Agent can use tools via familiar function calls
- Servers can be implemented in any language (Python, Node.js)
- Easy to add new tools

**Files:** `mcp_server/feature_mcp.py`, `@playwright/mcp`

### 3. Observer Pattern (WebSocket)

**Real-time updates** to UI via WebSocket broadcasts.

**Benefits:**
- Decouples agent from UI
- Multiple clients can subscribe
- Efficient (push vs poll)

**Files:** `server/websocket.py`, `ui/src/hooks/useWebSocket.ts`

### 4. Template Method Pattern (Prompts)

**Fallback chain** for prompt loading with project-specific overrides.

**Benefits:**
- Projects can customize prompts
- Fallback to sensible defaults
- Easy to add new prompt types

**Files:** `prompts.py`, `.claude/templates/`

### 5. Repository Pattern (Database)

**Abstraction layer** over SQLite via SQLAlchemy ORM.

**Benefits:**
- Database schema changes don't affect business logic
- Easy to swap SQLite for PostgreSQL
- Testable (mock session)

**Files:** `api/database.py`, `api/dependency_resolver.py`

---

## Scalability Considerations

### Current Limits

| Resource | Limit | Bottleneck |
|----------|-------|------------|
| **Concurrent coding agents** | 5 | Memory (450 MB/agent) |
| **Total agents** | 10 | Process management |
| **Database size** | ~100,000 features | SQLite performance |
| **WebSocket connections** | ~100 | Uvicorn default |

### Scaling Strategies

**1. Horizontal Scaling (Multiple Machines)**

Replace SQLite with PostgreSQL:

```python
# api/database.py
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@host/db")
engine = create_engine(DATABASE_URL)
```

Benefits:
- Multiple orchestrators on different machines
- Concurrent writes with row-level locking
- Handle millions of features

**2. Queue-Based Orchestration**

Replace polling with message queue (Celery, RQ):

```python
# Instead of polling loop:
while True:
    ready = get_ready_features()
    for feature in ready:
        start_feature(feature["id"])
    await asyncio.sleep(POLL_INTERVAL)

# Use queue:
@celery.task
def process_feature(feature_id):
    agent = spawn_coding_agent(feature_id)
    agent.run()
```

Benefits:
- Event-driven (no polling overhead)
- Work stealing (idle workers grab tasks)
- Fault tolerance (retry failed tasks)

**3. Distributed File System**

For large codebases (> 1 GB):

- Mount shared filesystem (NFS, S3FS)
- Each agent works on isolated branch
- Merge branches after completion

**4. Redis for Real-Time State**

For < 100ms WebSocket latency:

```python
# Replace database polling with Redis pub/sub
redis_client.publish("feature_updates", json.dumps({"id": 42, "passes": True}))

# WebSocket manager subscribes
async for message in redis_client.subscribe("feature_updates"):
    broadcast_to_clients(message)
```

---

## Summary

**Autocoder-2** is a production-grade autonomous coding system with:

✅ **Multi-layer architecture** (UI ↔ API ↔ Orchestrator ↔ Agent ↔ MCP ↔ Database)
✅ **Defense-in-depth security** (sandbox + permissions + allowlist)
✅ **Parallel execution** (up to 5 concurrent agents with dependency-aware scheduling)
✅ **Real-time monitoring** (WebSocket updates, debug logs, metrics)
✅ **Extensibility** (MCP servers, persona system, checkpoint agents)
✅ **Resilience** (timeout handling, process cleanup, atomic database ops)

**Key Differentiators:**
- **Persistent state** across sessions (SQLite)
- **Feature-based testing** (verification steps per feature)
- **Dependency management** (cycle detection, impact analysis)
- **Quality gates** (code review, security audit, performance analysis)

**Next Steps:**
- Read [PARALLEL_EXECUTION_GUIDE.md](PARALLEL_EXECUTION_GUIDE.md) for concurrency details
- Read [SKIP_MANAGEMENT_USER_GUIDE.md](SKIP_MANAGEMENT_USER_GUIDE.md) for blocker handling
- Read [TROUBLESHOOTING_MASTER.md](TROUBLESHOOTING_MASTER.md) for debugging guidance

---

**Document Version:** 1.0
**Last Updated:** 2026-01-21
**Maintained By:** Autocoder Team
