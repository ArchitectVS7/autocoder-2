# Parallel Execution Guide

**Comprehensive guide to running multiple concurrent coding agents**

---

## Table of Contents

- [Overview](#overview)
  - [What is Parallel Execution?](#what-is-parallel-execution)
  - [When to Use Parallel Mode](#when-to-use-parallel-mode)
  - [Key Benefits](#key-benefits)
- [Core Concepts](#core-concepts)
  - [Unified Orchestrator](#unified-orchestrator)
  - [Coding Agents](#coding-agents)
  - [Testing Agents](#testing-agents)
  - [Dependency-Aware Scheduling](#dependency-aware-scheduling)
  - [Atomic Feature Claiming](#atomic-feature-claiming)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
  - [Basic Usage](#basic-usage)
  - [Configuration Flags](#configuration-flags)
  - [Examples](#examples)
- [Configuration Options](#configuration-options)
  - [Concurrency Settings](#concurrency-settings)
  - [Testing Agent Configuration](#testing-agent-configuration)
  - [YOLO Mode](#yolo-mode)
  - [Model Selection](#model-selection)
- [Dashboard and Monitoring](#dashboard-and-monitoring)
  - [Mission Control Panel](#mission-control-panel)
  - [Agent Mascots](#agent-mascots)
  - [Activity Feed](#activity-feed)
  - [Debug Logs](#debug-logs)
- [How It Works](#how-it-works)
  - [Initialization Phase](#initialization-phase)
  - [Feature Loop](#feature-loop)
  - [Scheduling Algorithm](#scheduling-algorithm)
  - [Process Management](#process-management)
- [Best Practices](#best-practices)
  - [Choosing Concurrency Level](#choosing-concurrency-level)
  - [Cost vs Speed Tradeoffs](#cost-vs-speed-tradeoffs)
  - [When to Use Testing Agents](#when-to-use-testing-agents)
  - [Dependency Management](#dependency-management)
- [Common Pitfalls](#common-pitfalls)
- [Performance Considerations](#performance-considerations)
- [Troubleshooting](#troubleshooting)
  - [Quick Diagnostics](#quick-diagnostics)
  - [Agent Process Hangs](#agent-process-hangs)
  - [Process Tree Cleanup Failures](#process-tree-cleanup-failures)
  - [Deadlocks in Feature Claiming](#deadlocks-in-feature-claiming)
  - [Features Stuck in in_progress](#features-stuck-in-in_progress)
  - [Dependency Deadlock](#dependency-deadlock)
  - [Testing Agents Not Spawning](#testing-agents-not-spawning)
- [Advanced Topics](#advanced-topics)
  - [Process Isolation](#process-isolation)
  - [Database Connection Pooling](#database-connection-pooling)
  - [Debug Logging](#debug-logging)
  - [Timeout Configuration](#timeout-configuration)

---

## Overview

### What is Parallel Execution?

Parallel execution allows you to run **multiple Claude coding agents simultaneously**, each working on different features of your application. Instead of implementing features one-by-one in sequence, the orchestrator spawns up to **5 concurrent coding agents** that work in parallel, dramatically reducing time-to-completion.

**Architecture:**
```
Unified Orchestrator
  │
  ├─► Initialization Agent (if needed)
  │   └─► Creates features.db from app_spec.txt
  │
  ├─► Coding Agent #1 (Feature #3: User Authentication)
  ├─► Coding Agent #2 (Feature #7: Database Models)
  ├─► Coding Agent #3 (Feature #12: API Endpoints)
  │
  └─► Testing Agents (optional)
      ├─► Testing Agent #1 (Regression testing Feature #1)
      └─► Testing Agent #2 (Regression testing Feature #5)
```

### When to Use Parallel Mode

✅ **Use parallel execution when:**
- You have **10+ features** to implement
- Features are **largely independent** (minimal dependencies)
- You want to **reduce time-to-MVP** (hours instead of days)
- You're **willing to pay higher API costs** for speed
- You have a **spec with clear, well-defined features**

❌ **Avoid parallel execution when:**
- You have **< 5 features** (overhead not worth it)
- Features are **highly interdependent** (creates dependency deadlock)
- You're **cost-sensitive** (parallel = 3-5x API cost)
- You're **prototyping/exploring** (use YOLO mode instead)
- Your spec is **vague or incomplete** (leads to rework)

### Key Benefits

| Benefit | Description | Measurement |
|---------|-------------|-------------|
| **Speed** | 3-5x faster completion | Time to MVP: 6 hours → 1.5 hours |
| **Parallelism** | Multiple features at once | 5 agents × 1 feature/hr = 5 features/hr |
| **Regression Testing** | Continuous validation | Testing agents catch regressions immediately |
| **Dependency Handling** | Smart scheduling | Blocked features wait until dependencies pass |
| **Resource Management** | Automatic cleanup | Process trees killed properly on Windows/Unix |

**Cost-Benefit Example:**
- **Single agent**: 30 features × 20 minutes/feature = **10 hours**
- **3 concurrent agents**: 30 features ÷ 3 = **3.5 hours** (accounting for dependency delays)
- **API cost**: 3x higher, but **3x faster delivery**

---

## Core Concepts

### Unified Orchestrator

The **ParallelOrchestrator** is the brain of the system. It handles:

1. **Lifecycle Management**
   - Spawns initializer agent if `features.db` doesn't exist
   - Spawns coding agents up to `--concurrency` limit
   - Spawns testing agents based on `--testing-ratio`
   - Cleans up all processes on shutdown

2. **Dependency-Aware Scheduling**
   - Computes "scheduling scores" for each pending feature
   - Only starts features when dependencies are satisfied
   - Skips features blocked by unmet dependencies

3. **Process Management**
   - Uses `psutil` to kill entire process trees (Windows + Unix)
   - Handles timeouts (30 minutes for initializer, unlimited for coding)
   - Tracks failure counts (max 3 retries per feature)

4. **Database Coordination**
   - Atomic feature claiming via SQL UPDATE with WHERE conditions
   - Engine disposal after agent completion (refreshes stale connections)
   - Thread-safe access with locks

**Key Files:**
- `parallel_orchestrator.py` (1,124 lines) - Orchestrator implementation
- `autonomous_agent_demo.py` (244 lines) - Entry point
- `agent.py` (369 lines) - Agent session loop

### Coding Agents

Each coding agent is a **subprocess** running `autonomous_agent_demo.py` with:

```bash
python autonomous_agent_demo.py \
  --project-dir /path/to/project \
  --agent-type coding \
  --feature-id 42 \
  --max-iterations 1
```

**What coding agents do:**
1. **Claim a feature** via `feature_claim_next` (atomic)
2. **Read feature details** (description, steps, dependencies)
3. **Implement the feature** (write code, run lints, type-check)
4. **Mark as passing** via `feature_mark_passing`
5. **Exit** (orchestrator spawns next agent)

**Isolation:**
- Each agent has a unique `agent_id` (e.g., `feature-42`)
- Browser contexts isolated (Playwright uses `--isolated` flag)
- Database writes are atomic (SQLite handles concurrency)

### Testing Agents

Testing agents perform **regression testing** on passing features to catch bugs introduced by new code.

```bash
python autonomous_agent_demo.py \
  --project-dir /path/to/project \
  --agent-type testing \
  --max-iterations 1
```

**What testing agents do:**
1. **Get random passing features** via `feature_get_for_regression` (limit: 3)
2. **Re-run verification steps** (check code still works)
3. **Mark as failing** if regression detected via `feature_mark_failing`
4. **Exit** (orchestrator spawns next testing agent)

**Configuration:**
- `--testing-ratio N`: Spawn N testing agents per completed coding agent (0-3, default: 1)
- `--count-testing`: Count testing agents toward concurrency limit (default: false)
- `--yolo`: Disable testing agents entirely

**Spawn Trigger:**
Testing agents are spawned **after a coding agent successfully completes**, ensuring there are passing features to test.

### Dependency-Aware Scheduling

Features can declare dependencies using `feature_add_dependency`:

```json
{
  "id": 5,
  "name": "Login API Endpoint",
  "dependencies": [3, 4]  // Blocked until Features #3 and #4 pass
}
```

**Scheduling Algorithm:**

1. **Compute Scheduling Scores** (`api/dependency_resolver.py:compute_scheduling_scores`)
   ```python
   score = base_priority + (100 * num_dependent_features) - (10 * skip_count)
   ```
   - Higher score = implemented first
   - Features that block many others get priority boost
   - Frequently skipped features get priority penalty

2. **Filter Ready Features**
   - `passes = false AND in_progress = false`
   - All dependency IDs exist in database (orphaned deps ignored)
   - All dependencies have `passes = true`

3. **Sort by Score** (descending), then priority, then ID

**Example:**
```
Feature #3 (score: 250) → Has 5 dependent features, implement first
Feature #7 (score: 100) → No dependents, lower priority
Feature #12 (score: 50) → Skipped 2 times, lowest priority
```

**Cycle Detection:**
Adding a dependency that creates a cycle is **blocked** by `would_create_circular_dependency` using depth-first search.

### Atomic Feature Claiming

When multiple agents run concurrently, they must **atomically claim** features to avoid collisions.

**Problem:**
```
Agent A: Read feature #3 (not claimed)
Agent B: Read feature #3 (not claimed)  ← Race condition!
Agent A: Mark feature #3 in_progress
Agent B: Mark feature #3 in_progress  ← Both agents work on same feature!
```

**Solution: `feature_claim_next`** (used only in parallel mode)

```python
# mcp_server/feature_mcp.py:300-318
result = session.execute(
    text("""
        UPDATE features
        SET in_progress = 1
        WHERE id = :feature_id
          AND passes = 0
          AND in_progress = 0
    """),
    {"feature_id": candidate_id}
)

if result.rowcount == 0:
    # Feature was claimed by another agent, retry
    return _feature_claim_next_internal(attempt + 1)
```

**How it works:**
1. Agent selects a candidate feature ID (with `_priority_lock` for in-process safety)
2. Agent executes `UPDATE ... WHERE in_progress = 0` (atomic SQL operation)
3. If `rowcount == 0`, another agent claimed it → retry with next candidate
4. If `rowcount == 1`, claim successful → return feature details

**Retry Logic:**
- Max retries: 10 attempts
- If max retries exceeded: return error "High contention detected"
- Typical retries: 0-2 (unless 5+ agents with few features)

---

## Quick Start

### 1. Standard Parallel Execution (3 agents)

```bash
# Windows
python autonomous_agent_demo.py --project-dir my-app --concurrency 3

# Or using registered project name
python autonomous_agent_demo.py --project-dir my-app -c 3
```

**What happens:**
1. Orchestrator checks if `features.db` exists
2. If not, runs initializer agent (10-20 minutes)
3. Spawns 3 concurrent coding agents
4. Each coding agent claims a feature, implements it, marks passing
5. After each success, spawns 1 testing agent (default ratio: 1)
6. Continues until all features pass or fail permanently

### 2. Maximum Concurrency (5 agents)

```bash
python autonomous_agent_demo.py --project-dir my-app --concurrency 5
```

**Limits:**
- Hard limit: 5 coding agents (memory/stability)
- Total agents: 10 max (5 coding + 5 testing)

### 3. Rapid Prototyping (No Testing Agents)

```bash
python autonomous_agent_demo.py --project-dir my-app -c 3 --yolo
```

YOLO mode disables:
- Testing agents (no regression testing)
- Browser automation (Playwright MCP server)

Still runs:
- Lint checks (`npm run lint`)
- Type checks (`npm run type-check`)

### 4. Custom Testing Agent Ratio

```bash
# 2 testing agents per coding agent completion
python autonomous_agent_demo.py --project-dir my-app -c 3 --testing-ratio 2

# Disable testing agents (but keep verification)
python autonomous_agent_demo.py --project-dir my-app -c 3 --testing-ratio 0
```

---

## CLI Reference

### Basic Usage

```bash
python autonomous_agent_demo.py --project-dir <path> [OPTIONS]
```

### Configuration Flags

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--project-dir` | - | string | **required** | Project directory (absolute path or registered name) |
| `--concurrency` | `-c` | int | `1` | Concurrent coding agents (1-5) |
| `--parallel` | `-p` | int | `3` | **DEPRECATED**: Use `--concurrency` |
| `--testing-ratio` | - | int | `1` | Testing agents per coding agent (0-3) |
| `--count-testing` | - | flag | `false` | Count testing agents toward concurrency limit |
| `--yolo` | - | flag | `false` | Disable testing agents (rapid prototyping) |
| `--model` | - | string | `claude-sonnet-4` | Claude model (sonnet/opus/haiku) |
| `--max-iterations` | - | int | `None` | Max iterations (used by orchestrator for subprocesses) |
| `--agent-type` | - | string | `None` | Agent type (initializer/coding/testing, used internally) |
| `--feature-id` | - | int | `None` | Specific feature ID (used by orchestrator for coding agents) |

### Examples

**Minimal (single agent, default):**
```bash
python autonomous_agent_demo.py --project-dir my-app
```
Equivalent to:
```bash
python autonomous_agent_demo.py --project-dir my-app --concurrency 1 --testing-ratio 1
```

**Production (3 coding agents, 1 testing agent per completion):**
```bash
python autonomous_agent_demo.py --project-dir my-app -c 3
```

**Speed-optimized (5 coding agents, no testing):**
```bash
python autonomous_agent_demo.py --project-dir my-app -c 5 --testing-ratio 0
```

**Quality-focused (3 coding agents, 2 testing agents per completion):**
```bash
python autonomous_agent_demo.py --project-dir my-app -c 3 --testing-ratio 2
```

**Resource-limited (testing agents count toward limit):**
```bash
# Max 3 total agents (coding + testing combined)
python autonomous_agent_demo.py --project-dir my-app -c 3 --count-testing
```

**Registered project:**
```bash
# Register project first
python start.py  # Choose "2. Register existing project"

# Then use short name
python autonomous_agent_demo.py --project-dir my-app -c 3
```

---

## Configuration Options

### Concurrency Settings

**`--concurrency N` (1-5, default: 1)**

Controls the maximum number of **coding agents** running simultaneously.

**Guidelines:**

| Concurrency | Use Case | Time Reduction | Cost Multiplier | Recommended For |
|-------------|----------|----------------|-----------------|-----------------|
| 1 | Single agent | Baseline | 1x | Small projects (< 10 features) |
| 2 | Light parallelism | ~40% faster | 1.8x | Medium projects (10-20 features) |
| 3 | **Recommended** | ~60% faster | 2.5x | Large projects (20-50 features) |
| 4 | High parallelism | ~70% faster | 3.5x | Very large projects (50+ features) |
| 5 | Maximum | ~75% faster | 4.5x | Massive projects (100+ features) |

**Why diminishing returns?**
- Dependency blocking increases with more agents
- Database contention increases
- Feature claiming retries increase
- Some features must run sequentially

**Hard Limits:**
```python
MAX_PARALLEL_AGENTS = 5      # Concurrent coding agents
MAX_TOTAL_AGENTS = 10         # Total agents (coding + testing)
```

**Auto-clamping:**
```bash
# Requested 10 agents → clamped to 5
python autonomous_agent_demo.py --project-dir my-app -c 10
# Output: "Clamping concurrency to valid range: 5"
```

### Testing Agent Configuration

**`--testing-ratio N` (0-3, default: 1)**

Controls how many testing agents spawn after **each coding agent success**.

**Ratios Explained:**

| Ratio | Behavior | Use Case |
|-------|----------|----------|
| 0 | No testing agents | Rapid prototyping, YOLO mode |
| 1 | **1 testing agent per success** | Balanced (default) |
| 2 | 2 testing agents per success | High-quality projects |
| 3 | 3 testing agents per success | Mission-critical code |

**Example with `--concurrency 3 --testing-ratio 2`:**

```
[Session Start]
  Coding Agent #1 → Working on Feature #3
  Coding Agent #2 → Working on Feature #7
  Coding Agent #3 → Working on Feature #12

[Coding Agent #1 completes Feature #3]
  Testing Agent #1 → Regression test Feature #1
  Testing Agent #2 → Regression test Feature #5
  Coding Agent #1 → Claims Feature #15 (new work)

[Coding Agent #2 completes Feature #7]
  Testing Agent #3 → Regression test Feature #2
  Testing Agent #4 → Regression test Feature #9
  Coding Agent #2 → Claims Feature #18 (new work)
```

**`--count-testing` (flag, default: false)**

If enabled, testing agents **count toward the concurrency limit**.

**Without flag (default):**
```
--concurrency 3
→ Max 3 coding agents + unlimited testing agents (up to MAX_TOTAL_AGENTS=10)
```

**With flag:**
```
--concurrency 3 --count-testing
→ Max 3 total agents (coding + testing combined)
→ If 2 testing agents running, only 1 coding agent can run
```

**When to use:**
- Limited memory/CPU (e.g., running on laptop)
- High API rate limits concerns
- Want strict resource control

### YOLO Mode

**`--yolo` (flag)**

Enables **rapid prototyping mode** with minimal verification.

**What's disabled:**
- Testing agents (no regression testing)
- Playwright MCP server (no browser automation)
- `feature_get_for_regression` tool

**What's still enabled:**
- Lint checks (`npm run lint`)
- Type checks (`tsc --noEmit`)
- Feature completion tracking

**Use YOLO when:**
- Scaffolding a prototype quickly
- Exploring design alternatives
- Cost is a major concern
- You'll manually test later

**Don't use YOLO for:**
- Production code
- Complex interactions (need browser testing)
- Refactoring (need regression tests)
- Mission-critical features

**Example:**
```bash
python autonomous_agent_demo.py --project-dir my-app -c 5 --yolo
# → 5 agents, no testing, maximum speed
```

### Model Selection

**`--model <model>` (default: claude-sonnet-4)**

Available models:
- `claude-sonnet-4` (default) - Balanced cost/quality
- `claude-opus-4.5` - Highest quality, 5x cost
- `claude-haiku-3.5` - Fastest, lowest cost, lower quality

**Model is passed to all subprocesses** (initializer, coding, testing).

---

## Dashboard and Monitoring

### Mission Control Panel

The Web UI displays a **Mission Control** panel when agents are active:

```
┌─────────────────────────────────────────────────┐
│ 🚀 MISSION CONTROL              3 agents active │
├─────────────────────────────────────────────────┤
│ ┌──────┐  ┌──────┐  ┌──────┐                   │
│ │ ⚡   │  │ 🐙   │  │ 🦉   │                   │
│ │Spark │  │ Octo │  │ Hoot │                   │
│ │#3    │  │#7    │  │#12   │                   │
│ │●●●   │  │●●○   │  │●○○   │                   │
│ └──────┘  └──────┘  └──────┘                   │
│                                                  │
│ Recent Activity                           (12)  │
│ • Spark: Implementing auth middleware           │
│ • Octo: Writing database migrations             │
│ • Hoot: Creating API endpoints                  │
└─────────────────────────────────────────────────┘
```

**Elements:**
- **Agent Cards**: One per active coding agent
- **Mascots**: Spark ⚡, Fizz 💧, Octo 🐙, Hoot 🦉, Buzz 🐝
- **Feature ID**: The feature being worked on
- **Progress Dots**: Visual progress indicator
- **Activity Feed**: Latest agent thoughts/actions

### Agent Mascots

Each coding agent gets a unique mascot:

| Mascot | Index | Emoji | Color |
|--------|-------|-------|-------|
| Spark | 0 | ⚡ | Yellow |
| Fizz | 1 | 💧 | Cyan |
| Octo | 2 | 🐙 | Purple |
| Hoot | 3 | 🦉 | Orange |
| Buzz | 4 | 🐝 | Green |

**Agent states** (shown as colors/icons):
- **Thinking** 💭 - Planning next steps
- **Working** ⚙️ - Executing code/tools
- **Testing** 🧪 - Running verification
- **Success** ✅ - Feature passed
- **Error** ❌ - Feature failed

### Activity Feed

Real-time stream of agent actions:

```
[14:23:45] Spark: Reading feature requirements...
[14:23:48] Spark: Creating auth middleware component
[14:23:52] Spark: Running lint check... ✓
[14:23:55] Octo: Implementing database schema
[14:23:57] Hoot: Writing API endpoint tests
[14:24:01] Spark: Feature #3 completed ✓
```

**WebSocket events:**
- `agent_update`: Agent state change (thinking → working → success)
- `log`: Agent output line (with `agentIndex` for attribution)
- `feature_update`: Feature status change (pending → in_progress → passing)

### Debug Logs

The orchestrator writes detailed logs to `orchestrator_debug.log`:

```
[14:23:45.123] [STARTUP] Orchestrator run_loop starting
    project_dir: /path/to/my-app
    max_concurrency: 3
    yolo_mode: False
    testing_agent_ratio: 1

[14:23:46.456] [INIT] Starting initializer subprocess
    project_dir: /path/to/my-app

[14:43:12.789] [SPAWN] Starting features batch
    ready_count: 15
    slots_available: 3
    features_to_start: [3, 7, 12]

[14:43:15.234] [COMPLETE] Coding agent for feature #3 finished
    return_code: 0
    status: success

[14:43:16.567] [TESTING] Spawning 1 testing agent(s)
    yolo_mode: False
    testing_agent_ratio: 1
    passing_count: 1
```

**Sections:**
- `ORCHESTRATOR STARTUP`: Initial configuration
- `INITIALIZATION PHASE`: Initializer agent run
- `FEATURE LOOP STARTING`: Main orchestration loop
- `SPAWN`: Feature starts
- `COMPLETE`: Agent completions
- `TESTING`: Testing agent spawns
- `DB_DUMP`: Full database state (every 5 iterations)

**Viewing logs:**
```bash
# Windows
type orchestrator_debug.log

# Linux/macOS
tail -f orchestrator_debug.log
```

---

## How It Works

### Initialization Phase

**First run only** (when `features.db` doesn't exist):

```
1. Orchestrator checks: has_features(project_dir)
   └─► False → Run initializer

2. Spawn initializer subprocess:
   python autonomous_agent_demo.py \
     --project-dir /path/to/project \
     --agent-type initializer \
     --max-iterations 1

3. Initializer agent:
   - Reads prompts/app_spec.txt (XML format)
   - Calls feature_create_bulk with all features
   - Creates features.db with SQLite
   - Exits after ~10-20 minutes

4. Orchestrator:
   - Detects initializer completion (returncode==0)
   - Disposes old database engine
   - Creates fresh engine/session_maker
   - Proceeds to feature loop
```

**Timeout:** 30 minutes (`INITIALIZER_TIMEOUT = 1800`)

If initializer exceeds 30 minutes:
```
ERROR: Initializer timed out after 30 minutes
```
→ Process tree killed, orchestrator exits

### Feature Loop

**Main orchestration loop** (`parallel_orchestrator.py:780-1002`):

```python
while self.is_running:
    1. Check if all features complete:
       if get_all_complete():
           break

    2. Check capacity:
       if len(running_coding_agents) >= max_concurrency:
           sleep(POLL_INTERVAL)  # 5 seconds
           continue

    3. Priority 1: Resume features from previous session
       resumable = get_resumable_features()
       # Features with in_progress=true but passes=false
       for feature in resumable[:slots]:
           start_feature(feature["id"], resume=True)

    4. Priority 2: Start new ready features
       ready = get_ready_features()
       # Pending features with satisfied dependencies
       for feature in ready[:slots]:
           start_feature(feature["id"])

    5. Sleep between iterations:
       sleep(2)
```

**Polling interval:** 5 seconds (`POLL_INTERVAL = 5`)

### Scheduling Algorithm

**Step 1: Compute scheduling scores** (`api/dependency_resolver.py`)

```python
def compute_scheduling_scores(features: list[dict]) -> dict[int, int]:
    """
    Compute priority scores for features based on:
    - Base priority (lower number = higher priority)
    - Number of dependent features (boost if others depend on this)
    - Skip count (penalty for frequently skipped features)
    """
    # Build dependency graph
    dependent_count = {}  # feature_id → count of features that depend on it

    for feature in features:
        for dep_id in feature.get("dependencies", []):
            dependent_count[dep_id] = dependent_count.get(dep_id, 0) + 1

    # Compute scores
    scores = {}
    for feature in features:
        fid = feature["id"]
        priority = feature.get("priority", 1000)
        skip_count = feature.get("skip_count", 0)
        num_dependents = dependent_count.get(fid, 0)

        # Higher score = implement first
        score = (1000 - priority) + (100 * num_dependents) - (10 * skip_count)
        scores[fid] = score

    return scores
```

**Example:**
```
Feature #3: priority=1, dependents=5, skips=0
  → score = 999 + 500 + 0 = 1499 (highest priority)

Feature #7: priority=10, dependents=0, skips=0
  → score = 990 + 0 + 0 = 990

Feature #12: priority=5, dependents=0, skips=3
  → score = 995 + 0 - 30 = 965 (lowest priority)
```

**Step 2: Filter ready features**

```python
ready = []
for feature in pending_features:
    if all(dep_id in passing_ids for dep_id in feature.dependencies):
        ready.append(feature)

# Sort by score (descending), then priority, then ID
ready.sort(key=lambda f: (-scores[f.id], f.priority, f.id))
```

**Step 3: Start features up to capacity**

```python
slots = max_concurrency - len(running_coding_agents)
for feature in ready[:slots]:
    start_feature(feature["id"])
```

### Process Management

**Spawning coding agents:**

```python
cmd = [
    sys.executable, "-u",  # Python unbuffered
    "autonomous_agent_demo.py",
    "--project-dir", str(project_dir),
    "--max-iterations", "1",
    "--agent-type", "coding",
    "--feature-id", str(feature_id),
]

proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env={**os.environ, "PYTHONUNBUFFERED": "1"},
)
```

**Output streaming:**

```python
threading.Thread(
    target=_read_output,
    args=(feature_id, proc, abort_event, "coding"),
    daemon=True
).start()
```

Reads stdout line-by-line and:
- Calls `on_output(feature_id, line)` → WebSocket emission
- Prints to console: `[Feature #42] <line>`

**Process cleanup:**

```python
def _kill_process_tree(proc: subprocess.Popen, timeout: float = 5.0):
    """Kill process and all children (handles Windows + Unix)."""
    parent = psutil.Process(proc.pid)
    children = parent.children(recursive=True)

    # Terminate children first
    for child in children:
        child.terminate()

    # Wait for graceful termination
    _, still_alive = psutil.wait_procs(children, timeout=timeout)

    # Force kill remaining
    for child in still_alive:
        child.kill()

    # Terminate parent
    proc.terminate()
    proc.wait(timeout=timeout)
```

**Why process tree killing is critical:**
- Windows: `subprocess.terminate()` only kills immediate process, not children
- Without tree killing: orphaned Node dev servers, Playwright browsers
- With tree killing: all spawned processes cleaned up properly

---

## Best Practices

### Choosing Concurrency Level

**Decision Tree:**

```
Total features < 10
  → concurrency=1 (single agent)

Total features 10-20
  → concurrency=2 (light parallelism)

Total features 20-50
  → concurrency=3 (recommended default)

Total features 50-100
  → concurrency=4 (high parallelism)

Total features 100+
  → concurrency=5 (maximum)

Dependency chains > 5 levels deep
  → concurrency=2 (high blocking potential)
```

**Cost Calculator:**

| Concurrency | Features | Time Estimate | API Cost Estimate |
|-------------|----------|---------------|-------------------|
| 1 | 30 | 10 hours | $15 |
| 2 | 30 | 6 hours | $27 (1.8x) |
| 3 | 30 | 4 hours | $37.50 (2.5x) |
| 5 | 30 | 3 hours | $67.50 (4.5x) |

*(Assumes $0.50/feature average cost, 70% parallel efficiency)*

### Cost vs Speed Tradeoffs

**Scenario 1: Startup MVP (speed critical)**
```bash
# Goal: Launch in 24 hours
python autonomous_agent_demo.py --project-dir my-app -c 5 --testing-ratio 0
```
- 5 coding agents, no testing
- **Fastest delivery**: ~3-4 hours for 50 features
- **Highest cost**: ~4-5x baseline
- **Risk**: Regressions not caught

**Scenario 2: Production Feature (quality critical)**
```bash
# Goal: Zero regressions, high quality
python autonomous_agent_demo.py --project-dir my-app -c 2 --testing-ratio 2
```
- 2 coding agents, 2 testing agents per completion
- **Moderate speed**: ~6-8 hours for 50 features
- **Moderate cost**: ~2x baseline
- **Benefit**: High test coverage

**Scenario 3: Side Project (cost critical)**
```bash
# Goal: Minimize cost, no time pressure
python autonomous_agent_demo.py --project-dir my-app -c 1
```
- Single agent, standard testing
- **Slowest delivery**: ~15-20 hours for 50 features
- **Lowest cost**: 1x baseline
- **Benefit**: Can run overnight

### When to Use Testing Agents

✅ **Use testing agents (`--testing-ratio 1+`) when:**
- Building production code
- Refactoring existing features
- High feature interdependency
- Mission-critical application
- Long-term maintenance expected

❌ **Skip testing agents (`--testing-ratio 0` or `--yolo`) when:**
- Rapid prototyping
- Proof-of-concept
- Exploring design alternatives
- Throwaway code
- Cost is primary constraint

**Best practice:**
Start with `--testing-ratio 1` (default). Increase to 2 if you see regressions. Decrease to 0 only for prototypes.

### Dependency Management

**Minimize deep chains:**

❌ **Bad (10-level chain):**
```
Feature #1 → #2 → #3 → #4 → #5 → #6 → #7 → #8 → #9 → #10
```
Result: Features run almost sequentially (low parallelism)

✅ **Good (3 parallel branches):**
```
Branch 1: #1 → #4 → #7
Branch 2: #2 → #5 → #8
Branch 3: #3 → #6 → #9
```
Result: 3 features run in parallel at each level

**Declare dependencies sparingly:**

Only add `feature_add_dependency` when:
- Feature B **requires code** from Feature A
- Feature B **will fail** without Feature A

Don't add dependencies for:
- Logical ordering preferences
- "Nice to have" sequencing
- Related features that don't share code

**Check dependency graph:**

Use the Web UI Graph View (press `G`):
- Visualizes dependency relationships
- Identifies bottleneck features (many dependents)
- Shows critical paths

---

## Common Pitfalls

### 1. Too Many Agents for Few Features

❌ **Antipattern:**
```bash
# 5 features, 5 agents
python autonomous_agent_demo.py --project-dir my-app -c 5
```

**Problem:**
- High contention in `feature_claim_next`
- Agents compete for limited work
- No parallelism benefit

**Solution:**
```bash
# 5 features, 2 agents (max)
python autonomous_agent_demo.py --project-dir my-app -c 2
```

**Rule of thumb:** `concurrency ≤ total_features / 3`

### 2. Dependency Deadlock

❌ **Antipattern:**
```
All 30 features have dependencies
All dependencies are on features not yet started
No features can start
```

**Problem:**
Orchestrator polls forever, no progress.

**Solution:**
- Ensure some "seed features" have no dependencies
- Break circular dependencies
- Use `feature_remove_dependency` to unblock

**Diagnosis:**
```
[DEBUG] get_ready_features: 0 ready, 0 passing, 0 in_progress, 30 total
[DEBUG]   Skipped: 0 passing, 0 in_progress, 0 running, 0 failed, 30 blocked by deps
```

### 3. Forgetting to Dispose Engine After Subprocess Commits

❌ **Problem:**
```python
# Subprocess commits to database
agent_subprocess.wait()

# Orchestrator reads stale data (connection cached)
passing = session.query(Feature).filter(passes=True).count()
# → Returns old count, doesn't see new passing feature!
```

**Solution:** (`parallel_orchestrator.py:688`)
```python
# CRITICAL: Refresh database connection
self._engine.dispose()

# Now new session sees subprocess commits
session = self.get_session()
passing = session.query(Feature).filter(passes=True).count()
# → Returns updated count ✓
```

This is why `_on_agent_complete` disposes the engine.

### 4. Not Handling Process Tree Cleanup on Windows

❌ **Antipattern:**
```python
proc.terminate()  # Only kills immediate process on Windows
```

**Problem:**
- Spawned Node dev servers remain running
- Playwright browsers remain open
- Resource exhaustion

**Solution:** Use `_kill_process_tree` with `psutil`
```python
_kill_process_tree(proc, timeout=5.0)
```

### 5. Ignoring MAX_FEATURE_RETRIES

❌ **Problem:**
```
Feature #42 fails 10 times due to bug
Orchestrator retries forever
Wastes API cost, never progresses
```

**Solution:** (`parallel_orchestrator.py:106`)
```python
MAX_FEATURE_RETRIES = 3

if self._failure_counts.get(feature_id, 0) >= MAX_FEATURE_RETRIES:
    # Skip permanently failed feature
    continue
```

After 3 failures, feature is marked "permanently failed" and skipped.

---

## Performance Considerations

### Memory Usage

**Per coding agent:**
- Python process: ~100 MB
- Node dev server (if spawned): ~200 MB
- Playwright browser (if spawned): ~150 MB
- **Total: ~450 MB per agent**

**5 concurrent agents:**
- 5 × 450 MB = **2.25 GB**
- Plus orchestrator: ~150 MB
- **Total: ~2.4 GB**

**Recommendation:**
- Minimum 4 GB RAM for `--concurrency 3`
- Minimum 8 GB RAM for `--concurrency 5`

### Database Contention

**SQLite handles concurrency well for reads**, but writes can cause contention.

**Mitigations:**
1. **Atomic claiming** via SQL UPDATE (no SELECT then UPDATE race)
2. **Thread locks** for in-process safety (`_priority_lock`)
3. **Engine disposal** to refresh stale connections
4. **Retry logic** in `feature_claim_next` (max 10 retries)

**Typical contention:**
- 3 agents: 0-1 retries per claim
- 5 agents: 1-3 retries per claim

If seeing **high retries** (5+):
- Reduce concurrency
- Check for slow database (disk I/O)
- Verify `features.db` is on SSD (not network drive)

### Timeout Configuration

**Initializer timeout:** 30 minutes
```python
INITIALIZER_TIMEOUT = 1800  # seconds
```

**When to increase:**
- Very large spec (100+ features)
- Slow model (Haiku)
- Complex feature descriptions

**How to increase:**
Edit `parallel_orchestrator.py:107`:
```python
INITIALIZER_TIMEOUT = 3600  # 60 minutes
```

**Coding agent timeout:** None (unlimited)

Coding agents run until:
- Feature completes (success)
- Max iterations reached (configured by orchestrator to 1)
- Error occurs (retry up to 3 times)

### Polling Interval

**Feature loop polls every 5 seconds:**
```python
POLL_INTERVAL = 5  # seconds
```

**Tradeoff:**
- Shorter interval: Faster response to agent completions, higher CPU
- Longer interval: Lower CPU, slower agent spawning

**When to decrease to 1-2 seconds:**
- Very short features (< 1 minute each)
- High churn (agents completing rapidly)

**When to increase to 10 seconds:**
- Long features (10+ minutes each)
- Resource-constrained environment

---

## Troubleshooting

### Quick Diagnostics

**Check orchestrator status:**
```bash
# Windows
type orchestrator_debug.log | findstr "LOOP"

# Linux/macOS
grep "LOOP" orchestrator_debug.log
```

**Check agent count:**
```bash
# Windows
tasklist | findstr python

# Linux/macOS
ps aux | grep "autonomous_agent_demo.py"
```

**Check database state:**
```bash
python -c "from api.database import *; from pathlib import Path; engine, maker = create_database(Path('my-app')); session = maker(); features = session.query(Feature).all(); print(f'Passing: {sum(f.passes for f in features)}, In-progress: {sum(f.in_progress for f in features)}, Total: {len(features)}'); session.close()"
```

**Check for stuck processes:**
```bash
# Linux/macOS
lsof -i :3000  # Check if dev server still running
ps aux | grep node
```

### Agent Process Hangs

**Symptoms:**
```
[DEBUG] get_ready_features: 5 ready, 10 passing, 3 in_progress, 30 total
(No new agent starts for 10+ minutes)
```

**Diagnosis:**

1. **Check if agent process is alive:**
   ```bash
   # Linux/macOS
   ps aux | grep "feature-id"

   # Windows
   tasklist | findstr python
   ```

2. **Check orchestrator debug log:**
   ```bash
   tail -50 orchestrator_debug.log | grep "Feature #"
   ```

3. **Check for MCP server startup failure:**
   - Agent process may be waiting for MCP server that crashed
   - Look for "MCP server error" in console output

**Solutions:**

**If agent process dead:**
```bash
# Orchestrator should detect this automatically
# If not, manually clear in_progress:
python -c "from api.database import *; from pathlib import Path; engine, maker = create_database(Path('my-app')); session = maker(); feature = session.query(Feature).filter(Feature.id == 42).first(); feature.in_progress = False; session.commit(); session.close()"
```

**If agent process alive but hung:**
```bash
# Kill the agent process
# Windows
taskkill /F /PID <pid>

# Linux/macOS
kill -9 <pid>

# Orchestrator will detect completion and clean up
```

**Prevention:**
- Use shorter `--max-iterations` for subprocesses (orchestrator uses 1)
- Enable timeout for coding agents (currently unlimited)

### Process Tree Cleanup Failures

**Symptoms:**
```
Agent stopped, but Node dev server still running on port 3000
Playwright browser windows remain open
```

**Diagnosis:**
```bash
# Check for orphaned Node processes
# Windows
tasklist | findstr node

# Linux/macOS
ps aux | grep node
lsof -i :3000
```

**Solution:**

1. **Manual cleanup:**
   ```bash
   # Windows
   taskkill /F /IM node.exe

   # Linux/macOS
   pkill -9 node
   ```

2. **Fix in code:** Ensure `_kill_process_tree` is called

3. **Check psutil version:**
   ```bash
   pip show psutil
   # Should be 5.9.0+
   ```

**Prevention:**
- Always use `_kill_process_tree` instead of `proc.terminate()`
- Test on both Windows and Unix

### Deadlocks in Feature Claiming

**Symptoms:**
```
[ERROR] Failed to claim feature after maximum retries
[HINT] High contention detected - try again or reduce parallel agents
```

**Diagnosis:**

1. **Check retry count in debug log:**
   ```bash
   grep "claim_next_internal" orchestrator_debug.log
   ```

2. **Check number of agents vs features:**
   ```
   5 agents, 3 pending features → High contention
   ```

**Solutions:**

**If agents > pending features:**
```bash
# Reduce concurrency
python autonomous_agent_demo.py --project-dir my-app -c 2
```

**If database contention (slow disk):**
```bash
# Move features.db to SSD
# Check disk I/O with:
# Windows: Resource Monitor
# Linux: iotop
```

**If many dependency-blocked features:**
```bash
# Check blocked features
python -c "from api.database import *; from api.dependency_resolver import *; from pathlib import Path; engine, maker = create_database(Path('my-app')); session = maker(); features = session.query(Feature).all(); all_dicts = [f.to_dict() for f in features]; passing_ids = {f.id for f in features if f.passes}; pending = [f for f in features if not f.passes and not f.in_progress]; blocked = [f for f in pending if not all(d in passing_ids for d in (f.dependencies or []))]; print(f'Blocked: {len(blocked)}/{len(pending)}'); session.close()"
```

### Features Stuck in in_progress

**Symptoms:**
```
Feature #42 shows in_progress=True, but no agent working on it
Progress: 10/30 passing, 3 in_progress (stuck for hours)
```

**Diagnosis:**

```bash
# Check which features are stuck
python -c "from api.database import *; from pathlib import Path; engine, maker = create_database(Path('my-app')); session = maker(); stuck = session.query(Feature).filter(Feature.in_progress == True, Feature.passes == False).all(); print([f'{f.id}: {f.name}' for f in stuck]); session.close()"

# Check if agent processes exist
ps aux | grep "feature-id 42"
```

**Solution:**

**If no agent process exists:**
```python
# Clear in_progress manually
from api.database import *
from pathlib import Path

engine, maker = create_database(Path('my-app'))
session = maker()

feature = session.query(Feature).filter(Feature.id == 42).first()
feature.in_progress = False
session.commit()
session.close()
```

**If agent process exists but stuck:**
```bash
# Kill agent process
kill -9 <pid>

# Orchestrator will detect and clear in_progress
```

**Prevention:**
- Orchestrator's `_on_agent_complete` always clears `in_progress`
- This is by design: handles agent crashes gracefully

### Dependency Deadlock

**Symptoms:**
```
All pending features blocked by unmet dependencies
No features can start (infinite loop)
```

**Diagnosis:**

```bash
grep "blocked by unmet dependencies" orchestrator_debug.log
```

**Debug output:**
```
[DEBUG] get_ready_features: 0 ready, 5 passing, 0 in_progress, 30 total
[DEBUG]   Skipped: 5 passing, 0 in_progress, 0 running, 0 failed, 25 blocked by deps
```

**Solution:**

1. **Identify blocking features:**
   ```python
   from api.database import *
   from pathlib import Path

   engine, maker = create_database(Path('my-app'))
   session = maker()

   all_features = session.query(Feature).all()
   passing_ids = {f.id for f in all_features if f.passes}
   pending = [f for f in all_features if not f.passes and not f.in_progress]

   for f in pending:
       deps = f.dependencies or []
       unmet = [d for d in deps if d not in passing_ids]
       if unmet:
           print(f"Feature #{f.id} '{f.name}' blocked by: {unmet}")

   session.close()
   ```

2. **Check for circular dependencies:**
   ```python
   from api.dependency_resolver import would_create_circular_dependency

   # Check if adding a dependency creates a cycle
   would_create_circular_dependency(feature_id=3, new_dependency_id=7, all_features=all_dicts)
   ```

3. **Remove invalid dependencies:**
   ```python
   # If Feature #42 depends on non-existent Feature #999
   from api.database import *
   from pathlib import Path

   engine, maker = create_database(Path('my-app'))
   session = maker()

   feature = session.query(Feature).filter(Feature.id == 42).first()
   if 999 in feature.dependencies:
       feature.dependencies.remove(999)
       session.commit()

   session.close()
   ```

**Prevention:**
- Use Skip Management system to detect bad dependencies
- Run dependency graph visualization (Web UI Graph View)
- Ensure "seed features" (no dependencies) exist

### Testing Agents Not Spawning

**Symptoms:**
```
Coding agents completing successfully
No testing agents spawning
--testing-ratio 1 configured
```

**Diagnosis:**

1. **Check if YOLO mode enabled:**
   ```bash
   grep "yolo_mode" orchestrator_debug.log
   # Should show: yolo_mode: False
   ```

2. **Check if passing features exist:**
   ```bash
   grep "passing_count" orchestrator_debug.log
   # Should show: passing_count > 0
   ```

3. **Check testing agent ratio:**
   ```bash
   grep "testing_agent_ratio" orchestrator_debug.log
   # Should show: testing_agent_ratio: 1 (or higher)
   ```

**Solutions:**

**If YOLO mode enabled:**
```bash
# Remove --yolo flag
python autonomous_agent_demo.py --project-dir my-app -c 3
```

**If passing_count = 0:**
```
Testing agents only spawn AFTER first coding agent success
Wait for first feature to complete
```

**If testing_agent_ratio = 0:**
```bash
# Set ratio to 1+
python autonomous_agent_demo.py --project-dir my-app -c 3 --testing-ratio 1
```

**If MAX_TOTAL_AGENTS limit reached:**
```bash
# Check total agents
grep "At max total agents" orchestrator_debug.log

# Solution: Wait for agents to complete, or increase limit in code
MAX_TOTAL_AGENTS = 10  # Edit parallel_orchestrator.py:103
```

---

## Advanced Topics

### Process Isolation

Each coding agent runs in an **isolated subprocess** with:

**Unique agent ID:**
```python
agent_id = f"feature-{feature_id}"  # e.g., "feature-42"
```

**Browser context isolation:**
- Playwright MCP server uses `agent_id` to create separate browser contexts
- Each agent's browser automation is isolated (cookies, localStorage, etc.)

**Environment variables:**
```python
env = {
    **os.environ,
    "PYTHONUNBUFFERED": "1",
    "PROJECT_DIR": str(project_dir),
}
```

**Working directory:**
```python
cwd=str(AUTOCODER_ROOT)  # All agents share same working directory
```

**Why isolation matters:**
- Prevents agents from interfering with each other's browser state
- Allows testing agents to run independently
- Enables clean process tree cleanup

### Database Connection Pooling

**SQLAlchemy engine per orchestrator:**
```python
self._engine, self._session_maker = create_database(project_dir)
```

**Session per query:**
```python
def get_session():
    return _session_maker()

# Usage:
session = self.get_session()
try:
    features = session.query(Feature).all()
finally:
    session.close()
```

**Engine disposal after subprocess commits:**
```python
# CRITICAL: Refresh connection pool
self._engine.dispose()

# Forces new connections that see subprocess commits
session = self.get_session()
```

**Why disposal is needed:**
- SQLite allows concurrent reads, but writes lock the database
- Agent subprocesses commit to the database file
- Orchestrator's cached connections may not see new commits
- `engine.dispose()` closes all pooled connections
- Next `get_session()` creates fresh connection that sees new data

### Debug Logging

**Enable debug logging:**

Debug logging is **always enabled** and writes to `orchestrator_debug.log`.

**Custom debug log file:**
```python
from parallel_orchestrator import DebugLogger

logger = DebugLogger(log_file=Path("/custom/path/debug.log"))
logger.start_session()
logger.log("CUSTOM", "My message", key1="value1", key2="value2")
```

**Log levels:**
- `STARTUP`: Orchestrator initialization
- `INIT`: Initializer phase
- `LOOP`: Feature loop iterations
- `CAPACITY`: Concurrency checks
- `SPAWN`: Agent spawning
- `COMPLETE`: Agent completion
- `TESTING`: Testing agent spawns
- `DB`: Database operations
- `DB_DUMP`: Full database state

**Filtering logs:**
```bash
# Show only spawning events
grep "SPAWN" orchestrator_debug.log

# Show only completions
grep "COMPLETE" orchestrator_debug.log

# Show database state dumps
grep "DB_DUMP" orchestrator_debug.log
```

### Timeout Configuration

**Initializer timeout (30 minutes):**
```python
# parallel_orchestrator.py:107
INITIALIZER_TIMEOUT = 1800  # seconds
```

**To increase:**
```python
INITIALIZER_TIMEOUT = 3600  # 60 minutes
```

**Coding agent timeout (currently unlimited):**

To add timeout for coding agents, modify `_spawn_coding_agent`:

```python
# Add timeout handling
async def _wait_with_timeout(proc, timeout):
    try:
        await asyncio.wait_for(proc.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        _kill_process_tree(proc)
        raise

# Usage in _read_output:
await _wait_with_timeout(proc, timeout=3600)  # 60 min timeout
```

**Polling interval:**
```python
# parallel_orchestrator.py:105
POLL_INTERVAL = 5  # seconds between ready feature checks
```

**To decrease for faster agent spawning:**
```python
POLL_INTERVAL = 2  # 2 seconds
```

---

## Summary

**Parallel execution** is a powerful feature that can **reduce time-to-MVP by 3-5x** at the cost of higher API usage. Key takeaways:

✅ **Use for:** Large projects (20+ features), tight deadlines, independent features
❌ **Avoid for:** Small projects (< 10 features), highly dependent features, cost sensitivity

**Recommended starting configuration:**
```bash
python autonomous_agent_demo.py --project-dir my-app -c 3
```

**For troubleshooting:**
1. Check `orchestrator_debug.log`
2. Monitor Mission Control dashboard
3. Verify database state with SQL queries
4. Use `--testing-ratio 0` to simplify if issues persist

**For maximum speed:**
```bash
python autonomous_agent_demo.py --project-dir my-app -c 5 --yolo
```

**For maximum quality:**
```bash
python autonomous_agent_demo.py --project-dir my-app -c 2 --testing-ratio 2
```

**Next steps:**
- Read [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) for system design
- Read [TROUBLESHOOTING_MASTER.md](TROUBLESHOOTING_MASTER.md) for cross-cutting issues
- Read [SKIP_MANAGEMENT_USER_GUIDE.md](SKIP_MANAGEMENT_USER_GUIDE.md) for dependency handling

---

**Document Version:** 1.0
**Last Updated:** 2026-01-21
**Maintained By:** Autocoder Team
