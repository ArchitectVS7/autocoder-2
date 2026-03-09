# Troubleshooting Master Guide

**Cross-cutting diagnostic procedures and solutions**

---

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Database Issues](#database-issues)
  - [Connection Pool Stale Data](#connection-pool-stale-data)
  - [Database Locked](#database-locked)
  - [Database Corruption](#database-corruption)
  - [Migration Failures](#migration-failures)
- [Performance Issues](#performance-issues)
  - [Slow Agent Responses](#slow-agent-responses)
  - [Memory Leaks](#memory-leaks)
  - [High CPU Usage](#high-cpu-usage)
  - [Disk I/O Bottlenecks](#disk-io-bottlenecks)
- [Network Issues](#network-issues)
  - [API Timeouts](#api-timeouts)
  - [WebSocket Disconnections](#websocket-disconnections)
  - [MCP Server Connection Failures](#mcp-server-connection-failures)
- [Permission Issues](#permission-issues)
  - [Bash Command Blocked](#bash-command-blocked)
  - [File Access Denied](#file-access-denied)
  - [Sandbox Violations](#sandbox-violations)
- [Integration Issues](#integration-issues)
  - [MCP Server Crashes](#mcp-server-crashes)
  - [Playwright Failures](#playwright-failures)
  - [Git Conflicts](#git-conflicts)
  - [NPM Install Failures](#npm-install-failures)
- [Platform-Specific Issues](#platform-specific-issues)
  - [Windows Path Issues](#windows-path-issues)
  - [Unix Permission Issues](#unix-permission-issues)
  - [Cross-Platform Line Endings](#cross-platform-line-endings)
- [Environment Issues](#environment-issues)
  - [Python Version Mismatch](#python-version-mismatch)
  - [Node Version Mismatch](#node-version-mismatch)
  - [Missing Dependencies](#missing-dependencies)
  - [Virtual Environment Issues](#virtual-environment-issues)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

### Health Check Script

```bash
# Create health_check.sh in autocoder-2 root
cat > health_check.sh << 'EOF'
#!/bin/bash

echo "=== Autocoder Health Check ==="
echo

# Python version
echo "Python version:"
python --version
echo

# Dependencies
echo "Key dependencies:"
pip show claude-agent-sdk sqlalchemy fastapi psutil | grep -E "Name|Version"
echo

# Project directory
if [ -z "$1" ]; then
    echo "Usage: ./health_check.sh <project-dir>"
    exit 1
fi

PROJECT_DIR="$1"
echo "Project directory: $PROJECT_DIR"
echo

# Features database
if [ -f "$PROJECT_DIR/features.db" ]; then
    echo "Features database: EXISTS"
    python -c "from api.database import *; from pathlib import Path; engine, maker = create_database(Path('$PROJECT_DIR')); session = maker(); features = session.query(Feature).all(); print(f'  Total features: {len(features)}'); print(f'  Passing: {sum(f.passes for f in features)}'); print(f'  In-progress: {sum(f.in_progress for f in features)}'); session.close()"
else
    echo "Features database: MISSING (needs initialization)"
fi
echo

# Orchestrator status
if [ -f "orchestrator_debug.log" ]; then
    echo "Recent orchestrator activity:"
    tail -5 orchestrator_debug.log
else
    echo "Orchestrator debug log: NOT FOUND"
fi
echo

# Running processes
echo "Python agent processes:"
ps aux | grep "autonomous_agent_demo.py" | grep -v grep || echo "  None running"
echo

# Ports
echo "Port usage:"
lsof -i :8000 | grep LISTEN || echo "  Port 8000: FREE (API server not running)"
lsof -i :3000 | grep LISTEN || echo "  Port 3000: FREE (UI dev server not running)"

echo
echo "=== Health Check Complete ==="
EOF

chmod +x health_check.sh
```

**Usage:**

```bash
./health_check.sh my-app
```

### Quick Command Reference

| Issue | Diagnostic Command |
|-------|-------------------|
| **Check feature stats** | `python -c "from api.database import *; from pathlib import Path; engine, maker = create_database(Path('my-app')); session = maker(); features = session.query(Feature).all(); print(f'Passing: {sum(f.passes for f in features)}/{len(features)}'); session.close()"` |
| **Check running agents** | `ps aux \| grep autonomous_agent_demo.py` |
| **Check ports** | `lsof -i :8000; lsof -i :3000` |
| **Check database locks** | `lsof my-app/features.db` |
| **Check disk space** | `df -h` |
| **Check memory** | `free -h` (Linux) / `vm_stat` (macOS) |
| **Check Node processes** | `ps aux \| grep node` |
| **View recent logs** | `tail -50 orchestrator_debug.log` |

---

## Database Issues

### Connection Pool Stale Data

**Symptoms:**
```
Agent marks feature passing, but orchestrator doesn't see it
Progress: 10/30 passing (expected 11/30)
WebSocket shows old data
```

**Cause:**

SQLAlchemy connection pool caches connections. After a subprocess commits to the database, the orchestrator's cached connection may not see the new data.

**Diagnosis:**

```bash
# Check if agent actually wrote to database
sqlite3 my-app/features.db "SELECT passes FROM features WHERE id = 42"
# Returns: 1

# But Python shows old value:
python -c "from api.database import *; from pathlib import Path; engine, maker = create_database(Path('my-app')); session = maker(); feature = session.query(Feature).filter(Feature.id == 42).first(); print(feature.passes); session.close()"
# Returns: False (STALE!)
```

**Solution:**

**In orchestrator code** (`parallel_orchestrator.py:688`):

```python
def _on_agent_complete(self, feature_id, return_code, agent_type, proc):
    # CRITICAL: Dispose engine to refresh connection pool
    self._engine.dispose()

    # Now get fresh session
    session = self.get_session()
    feature = session.query(Feature).filter(Feature.id == feature_id).first()
    # feature.passes now shows correct value ✓
```

**Manually dispose engine:**

```python
from api.database import *
from pathlib import Path

engine, maker = create_database(Path('my-app'))
engine.dispose()  # Close all pooled connections

# Next query will use fresh connection
session = maker()
feature = session.query(Feature).filter(Feature.id == 42).first()
print(feature.passes)  # Correct value ✓
```

**Prevention:**
- Always call `engine.dispose()` after subprocess operations
- Use `session.expire_all()` before queries to force refresh

### Database Locked

**Symptoms:**
```
sqlite3.OperationalError: database is locked
Agent hangs when calling feature_mark_passing
```

**Cause:**

SQLite only allows one writer at a time. If a transaction is open (uncommitted), other writers block.

**Diagnosis:**

```bash
# Check which process has the database open
lsof my-app/features.db

# Output:
python  12345 user  3u  REG  /path/to/features.db
python  12346 user  4w  REG  /path/to/features.db  # Writer waiting!
```

**Solution 1: Kill blocking process**

```bash
# Identify blocking PID
lsof my-app/features.db | grep python

# Kill it
kill -9 12345

# Database will auto-rollback uncommitted transaction
```

**Solution 2: Increase timeout**

```python
# api/database.py
engine = create_engine(
    database_url,
    connect_args={"timeout": 30}  # Wait 30 seconds instead of 5
)
```

**Solution 3: Use WAL mode (Write-Ahead Logging)**

```python
# api/database.py
def create_database(project_dir: Path):
    engine = create_engine(database_url)

    # Enable WAL mode for better concurrency
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))

    return engine, session_maker
```

**Prevention:**
- Always commit or rollback transactions promptly
- Use `try/finally` blocks to ensure session cleanup
- Consider PostgreSQL for > 5 concurrent agents

### Database Corruption

**Symptoms:**
```
sqlite3.DatabaseError: database disk image is malformed
Cannot read features.db
```

**Cause:**

- Disk full during write
- Power loss / system crash
- SQLite bug (rare)

**Diagnosis:**

```bash
# Check database integrity
sqlite3 my-app/features.db "PRAGMA integrity_check"

# If output is NOT "ok", database is corrupted
```

**Solution 1: Restore from backup**

```bash
# If you have a backup:
cp my-app/features.db.backup my-app/features.db
```

**Solution 2: Export and reimport**

```bash
# Attempt to export data
sqlite3 my-app/features.db ".dump" > dump.sql

# Create new database
mv my-app/features.db my-app/features.db.corrupted
sqlite3 my-app/features.db < dump.sql
```

**Solution 3: Rebuild from spec**

```bash
# If export fails, reinitialize
rm my-app/features.db

# Run initializer agent again
python autonomous_agent_demo.py --project-dir my-app --agent-type initializer --max-iterations 1
```

**Prevention:**
- Regular backups: `cp features.db features.db.backup`
- Enable WAL mode (reduces corruption risk)
- Monitor disk space: `df -h`
- Use ECC RAM on server (prevents bit flips)

### Migration Failures

**Symptoms:**
```
sqlalchemy.exc.OperationalError: no such column: features.dependencies
Legacy JSON file exists, but migration failed
```

**Cause:**

Migration from `feature_list.json` to SQLite failed partway.

**Diagnosis:**

```bash
# Check if JSON file exists
ls -lh my-app/feature_list.json

# Check database schema
sqlite3 my-app/features.db ".schema features"
```

**Solution:**

```python
# Manual migration
from api.migration import migrate_json_to_sqlite
from api.database import create_database
from pathlib import Path

project_dir = Path('my-app')
engine, maker = create_database(project_dir)

# Force migration
migrate_json_to_sqlite(project_dir, maker)
```

**If migration still fails:**

```bash
# Backup JSON
cp my-app/feature_list.json my-app/feature_list.json.backup

# Delete database and JSON
rm my-app/features.db my-app/feature_list.json

# Reinitialize
python autonomous_agent_demo.py --project-dir my-app --agent-type initializer --max-iterations 1
```

---

## Performance Issues

### Slow Agent Responses

**Symptoms:**
```
Agent takes 10+ minutes per feature (expected 3-5 minutes)
Long pauses between tool uses
```

**Diagnosis:**

**Check API latency:**

```python
import time
from claude_agent_sdk import ClaudeSDKClient

start = time.time()
await client.query("What is 2+2?")
async for msg in client.receive_response():
    pass
elapsed = time.time() - start
print(f"Response time: {elapsed:.1f}s")  # Should be < 5s for simple query
```

**Check MCP server startup time:**

```bash
# Test Feature MCP server
time python -m mcp_server.feature_mcp
# Should start in < 2 seconds
```

**Check disk I/O:**

```bash
# Linux
iostat -x 1 10  # Monitor for 10 seconds

# macOS
sudo fs_usage | grep features.db
```

**Solutions:**

**1. Move database to SSD:**

```bash
# If features.db is on HDD, move to SSD
mkdir /mnt/ssd/my-app
mv my-app/features.db /mnt/ssd/my-app/
ln -s /mnt/ssd/my-app/features.db my-app/features.db
```

**2. Reduce MCP server startup overhead:**

```python
# client.py
# Remove unused MCP servers in YOLO mode
if yolo_mode:
    mcp_servers = {"features": {...}}  # Skip Playwright
```

**3. Use faster model:**

```bash
# Haiku is 3x faster than Sonnet (but lower quality)
python autonomous_agent_demo.py --project-dir my-app --model claude-haiku-3.5
```

**4. Increase API timeout:**

```python
# client.py
sdk_env = {
    "API_TIMEOUT_MS": "120000"  # 2 minutes instead of default 30s
}
```

### Memory Leaks

**Symptoms:**
```
Memory usage grows over time
System becomes slow after 10+ features
Eventually crashes with OOM (Out of Memory)
```

**Diagnosis:**

```bash
# Monitor memory usage
# Linux
watch -n 5 'ps aux | grep python | awk "{sum+=\$6} END {print sum/1024\" MB\"}"'

# macOS
while true; do ps aux | grep python | awk '{sum+=$6} END {print sum/1024" MB"}'; sleep 5; done
```

**Common Causes:**

**1. Unclosed database sessions:**

```python
# BAD
session = maker()
features = session.query(Feature).all()
# session never closed → memory leak!

# GOOD
session = maker()
try:
    features = session.query(Feature).all()
finally:
    session.close()
```

**2. Playwright browser not closed:**

```python
# Agent should call browser_close after testing
# Check if browsers accumulate:
ps aux | grep chrome
# If many chrome processes, browsers aren't closing
```

**3. Large log files in memory:**

```python
# BAD
all_logs = []
for line in proc.stdout:
    all_logs.append(line)  # Grows unbounded!

# GOOD
for line in proc.stdout:
    process_line(line)
    # Don't store in memory
```

**Solutions:**

**1. Restart orchestrator periodically:**

```bash
# After every 50 features:
if passing_count % 50 == 0:
    orchestrator.stop_all()
    exit(0)

# External script restarts:
while true; do
    python autonomous_agent_demo.py --project-dir my-app -c 3
    if [ $? -ne 0 ]; then break; fi
done
```

**2. Force garbage collection:**

```python
import gc

# After agent completion
def _on_agent_complete(self, feature_id, return_code, agent_type, proc):
    # ... cleanup code ...
    gc.collect()  # Force garbage collection
```

**3. Limit log retention:**

```python
# Truncate orchestrator_debug.log after 10,000 lines
if os.path.getsize("orchestrator_debug.log") > 10 * 1024 * 1024:  # 10 MB
    os.rename("orchestrator_debug.log", "orchestrator_debug.log.old")
```

### High CPU Usage

**Symptoms:**
```
CPU usage 100% for extended periods
System becomes unresponsive
Fans at maximum speed
```

**Diagnosis:**

```bash
# Identify CPU-hungry processes
# Linux
top -o %CPU

# macOS
top -o cpu

# Find autocoder processes
ps aux | grep python | sort -k3 -rn  # Sort by CPU%
```

**Common Causes:**

**1. Polling loop too fast:**

```python
# BAD
while True:
    ready = get_ready_features()
    # No delay → 100% CPU!

# GOOD
while True:
    ready = get_ready_features()
    await asyncio.sleep(POLL_INTERVAL)  # 5 seconds
```

**2. Regex in tight loop:**

```python
# BAD
for line in all_log_lines:  # 100,000 lines
    if re.match(r"Feature #(\d+) (completed|failed)", line):
        # ... slow regex on every line

# GOOD
pattern = re.compile(r"Feature #(\d+) (completed|failed)")
for line in all_log_lines:
    if pattern.match(line):  # Pre-compiled regex is faster
```

**3. Too many concurrent agents:**

```bash
# 10 agents on 4-core machine → thrashing
python autonomous_agent_demo.py --project-dir my-app -c 10

# Solution: Match concurrency to CPU cores
python autonomous_agent_demo.py --project-dir my-app -c 3
```

**Solutions:**

**1. Increase polling interval:**

```python
# parallel_orchestrator.py
POLL_INTERVAL = 10  # 10 seconds instead of 5
```

**2. Optimize hot paths:**

```python
# Use generators instead of lists
def get_ready_features():
    # BAD: Load all features into memory
    all_features = session.query(Feature).all()
    return [f for f in all_features if not f.passes]

    # GOOD: Stream features
    return session.query(Feature).filter(Feature.passes == False).yield_per(100)
```

**3. Profile with cProfile:**

```bash
python -m cProfile -o profile.stats autonomous_agent_demo.py --project-dir my-app -c 3
python -m pstats profile.stats
# (Pstats)> sort cumtime
# (Pstats)> stats 10
```

### Disk I/O Bottlenecks

**Symptoms:**
```
Agent writes code slowly
Git operations take minutes
Database queries slow
```

**Diagnosis:**

```bash
# Linux: Check disk I/O
iostat -x 1 10
# Look for %util > 80% (disk saturated)

# macOS: Monitor disk activity
sudo fs_usage | grep -E "READ|WRITE"
```

**Solutions:**

**1. Move project to SSD:**

```bash
# If on HDD, move to SSD
mv my-app /mnt/ssd/
cd /mnt/ssd/my-app
```

**2. Disable antivirus scanning:**

```bash
# Windows Defender slows file writes
# Add exclusion: my-app/ directory
```

**3. Use tmpfs for database (Linux):**

```bash
# Mount tmpfs (RAM disk)
sudo mkdir /mnt/tmpfs
sudo mount -t tmpfs -o size=1G tmpfs /mnt/tmpfs

# Copy database to RAM
cp my-app/features.db /mnt/tmpfs/
ln -sf /mnt/tmpfs/features.db my-app/features.db

# WARNING: Data lost on reboot! Backup regularly.
```

---

## Network Issues

### API Timeouts

**Symptoms:**
```
Error: Request timed out after 30000ms
Agent hangs waiting for API response
```

**Diagnosis:**

```bash
# Test API endpoint
time curl -X GET http://localhost:8000/api/health

# Should respond in < 1 second
```

**Solutions:**

**1. Increase timeout:**

```python
# client.py
sdk_env = {
    "API_TIMEOUT_MS": "180000"  # 3 minutes
}
```

**2. Check for blocking I/O in API:**

```python
# server/routers/features.py

# BAD: Blocking I/O in async function
@router.get("/features")
async def get_features():
    features = session.query(Feature).all()  # Blocks event loop!

# GOOD: Use async database library or run in executor
@router.get("/features")
async def get_features():
    loop = asyncio.get_running_loop()
    features = await loop.run_in_executor(None, lambda: session.query(Feature).all())
```

**3. Restart API server:**

```bash
# Kill and restart
pkill -f "uvicorn server.main:app"
cd server && uvicorn main:app --reload
```

### WebSocket Disconnections

**Symptoms:**
```
UI shows "Disconnected" badge
Real-time updates stop
```

**Diagnosis:**

```bash
# Check WebSocket endpoint
wscat -c ws://localhost:8000/ws/projects/my-app
# Should connect and show messages
```

**Solutions:**

**1. Check CORS settings:**

```python
# server/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add UI origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**2. Add reconnection logic in UI:**

```typescript
// ui/src/hooks/useWebSocket.ts
useEffect(() => {
    let reconnectTimer: NodeJS.Timeout

    const connect = () => {
        const ws = new WebSocket(wsUrl)

        ws.onclose = () => {
            // Reconnect after 5 seconds
            reconnectTimer = setTimeout(connect, 5000)
        }
    }

    connect()

    return () => clearTimeout(reconnectTimer)
}, [])
```

**3. Increase WebSocket timeout:**

```python
# server/websocket.py
@app.websocket("/ws/projects/{project_name}")
async def websocket_endpoint(websocket: WebSocket, project_name: str):
    await websocket.accept()

    # Send keepalive every 30 seconds
    async def keepalive():
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})

    asyncio.create_task(keepalive())
```

### MCP Server Connection Failures

**Symptoms:**
```
Error: Failed to connect to MCP server 'features'
Agent crashes on tool use
```

**Diagnosis:**

```bash
# Test Feature MCP server manually
python -m mcp_server.feature_mcp

# Should start without errors and show:
# MCP Server 'features' listening...
```

**Solutions:**

**1. Check Python path:**

```python
# client.py
mcp_servers["features"] = {
    "command": sys.executable,  # Use same Python as main process
    "args": ["-m", "mcp_server.feature_mcp"],
    "env": {
        "PYTHONPATH": str(Path(__file__).parent.resolve()),  # Add autocoder to path
    }
}
```

**2. Check PROJECT_DIR environment variable:**

```bash
# MCP server needs PROJECT_DIR to find database
echo $PROJECT_DIR
# Should output: /path/to/my-app
```

**3. Check for import errors:**

```bash
# Test imports
python -c "from mcp_server.feature_mcp import mcp; print('OK')"
```

**4. Increase MCP server startup timeout:**

```python
# Claude SDK default timeout is 10 seconds
# If MCP server takes longer, it fails

# Workaround: Pre-warm dependencies
import mcp_server.feature_mcp  # Import before creating client
```

---

## Permission Issues

### Bash Command Blocked

**Symptoms:**
```
[BLOCKED] Command 'rm' is not in the allowed commands list
Agent cannot run necessary command
```

**Diagnosis:**

Check `security.py:ALLOWED_COMMANDS`:

```python
ALLOWED_COMMANDS = {
    "ls", "cat", "head", "tail", "npm", "git", ...
}
```

**Solutions:**

**1. Add command to allowlist:**

```python
# security.py
ALLOWED_COMMANDS = {
    ...
    "mycustomcommand",  # Add new command
}
```

**2. Use alternative command:**

```bash
# Instead of 'rm':
git rm file.txt  # git is allowed

# Instead of 'find':
ls -R  # ls is allowed
```

**3. Temporarily disable security hook (NOT RECOMMENDED):**

```python
# client.py
# Remove bash_security_hook for debugging
hooks={}  # Empty (no validation)
```

### File Access Denied

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/path/outside/project'
Agent cannot read/write file
```

**Cause:**

File is outside project directory, or file permissions are wrong.

**Diagnosis:**

```bash
# Check file location
ls -l /path/to/file

# Check ownership
stat /path/to/file
```

**Solutions:**

**1. Move file into project:**

```bash
cp /path/outside/project/file.txt my-app/
```

**2. Fix permissions:**

```bash
# Make readable
chmod 644 my-app/file.txt

# Make executable
chmod +x my-app/script.sh
```

**3. Run as correct user:**

```bash
# Check current user
whoami

# Change ownership
sudo chown $USER:$USER my-app/features.db
```

### Sandbox Violations

**Symptoms:**
```
SecurityError: Sandbox violation detected
Command attempted to escape project directory
```

**Diagnosis:**

Check agent's bash command:

```bash
# BAD: Uses absolute path outside project
cd /etc && cat passwd

# GOOD: Relative path within project
cd src && cat config.txt
```

**Solutions:**

**1. Use relative paths:**

```bash
# Instead of:
cd /path/to/my-app/src

# Use:
cd src  # (cwd is already my-app/)
```

**2. Adjust cwd setting:**

```python
# client.py
ClaudeAgentOptions(
    cwd=str(project_dir.resolve()),  # Sets working directory to project
)
```

**3. Copy external files into project:**

```bash
# If agent needs /etc/hosts, copy it in:
cp /etc/hosts my-app/.hosts
# Agent can now read my-app/.hosts
```

---

## Integration Issues

### MCP Server Crashes

**Symptoms:**
```
Tool use error: MCP server 'playwright' exited unexpectedly
Agent crashes when calling browser_navigate
```

**Diagnosis:**

```bash
# Check MCP server logs
# Feature MCP: Check stderr
python -m mcp_server.feature_mcp 2>&1 | tee feature_mcp.log

# Playwright MCP: Check Node logs
npx @playwright/mcp@latest 2>&1 | tee playwright_mcp.log
```

**Common Causes:**

**1. Playwright browser not installed:**

```bash
# Install browsers
npx playwright install
```

**2. Memory exhaustion:**

```bash
# Check memory
free -h  # Linux
vm_stat  # macOS

# If low, reduce concurrency
python autonomous_agent_demo.py --project-dir my-app -c 2
```

**3. Incompatible Playwright version:**

```bash
# Update Playwright
npm install -g @playwright/mcp@latest
```

**Solutions:**

**Restart MCP server manually:**

```bash
# The Claude SDK will auto-restart crashed MCP servers
# But you can test manually:
npx @playwright/mcp@latest --viewport-size 1280x720
```

### Playwright Failures

**Symptoms:**
```
browser_navigate error: Navigation timeout
browser_click error: Element not found
```

**Diagnosis:**

```bash
# Run browser in non-headless mode to see what's happening
export PLAYWRIGHT_HEADLESS=false
python autonomous_agent_demo.py --project-dir my-app
```

**Solutions:**

**1. Increase timeout:**

```typescript
// Agent should call browser_wait_for before interacting
await browser_wait_for({selector: ".button", timeout: 10000})
```

**2. Check dev server is running:**

```bash
# If testing localhost:3000, ensure dev server is up
cd my-app && npm run dev

# Check port
lsof -i :3000
```

**3. Use headless mode for screenshots only:**

```bash
# Debugging: visible browser
export PLAYWRIGHT_HEADLESS=false

# Production: headless (faster)
export PLAYWRIGHT_HEADLESS=true
```

### Git Conflicts

**Symptoms:**
```
git commit fails: Merge conflict in package.json
Agent cannot commit changes
```

**Diagnosis:**

```bash
cd my-app
git status
# Shows conflicted files
```

**Solutions:**

**1. Abort merge:**

```bash
git merge --abort
```

**2. Reset to HEAD:**

```bash
# WARNING: Loses uncommitted changes
git reset --hard HEAD
```

**3. Manually resolve:**

```bash
# Edit conflicted file
vim package.json
# Remove conflict markers <<< === >>>
git add package.json
git commit -m "Resolve conflict"
```

**Prevention:**

- Use separate branch per agent (`--parallel` mode)
- Merge sequentially, not concurrently
- Avoid modifying same files in parallel agents

### NPM Install Failures

**Symptoms:**
```
npm ERR! code ERESOLVE
npm install fails with dependency conflict
```

**Diagnosis:**

```bash
cd my-app
npm install --loglevel verbose
```

**Solutions:**

**1. Use legacy peer deps:**

```bash
npm install --legacy-peer-deps
```

**2. Clear cache:**

```bash
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

**3. Use pnpm instead:**

```bash
npm install -g pnpm
cd my-app
pnpm install  # Better dependency resolution
```

---

## Platform-Specific Issues

### Windows Path Issues

**Symptoms:**
```
FileNotFoundError: C:\Users\...\my-app\src/components/App.tsx
Mixed path separators cause failures
```

**Cause:**

Windows uses `\`, Unix uses `/`. Python's `Path` handles this, but bash commands don't.

**Solutions:**

**1. Use Path.resolve():**

```python
from pathlib import Path

# BAD
project_dir = "C:\\Users\\me\\my-app"

# GOOD
project_dir = Path("C:/Users/me/my-app").resolve()
# Automatically uses correct separators
```

**2. Use forward slashes in bash:**

```bash
# WORKS on Windows
cd src/components && ls

# FAILS on Windows
cd src\components && ls  # Backslash not recognized in bash
```

**3. Use WSL (Windows Subsystem for Linux):**

```bash
# Install WSL
wsl --install

# Run autocoder in WSL
wsl
cd /mnt/c/Users/me/my-app
python autonomous_agent_demo.py --project-dir .
```

### Unix Permission Issues

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: './init.sh'
Script is not executable
```

**Diagnosis:**

```bash
ls -l init.sh
# Output: -rw-r--r-- (not executable)
```

**Solutions:**

```bash
chmod +x init.sh
./init.sh
```

**Prevention:**

```bash
# When creating scripts, always set +x
echo "#!/bin/bash\necho 'Hello'" > script.sh
chmod +x script.sh
```

### Cross-Platform Line Endings

**Symptoms:**
```
bash: ./init.sh: /bin/bash^M: bad interpreter
Script fails on Unix with ^M characters
```

**Cause:**

Windows uses CRLF (`\r\n`), Unix uses LF (`\n`). Git may check out files with wrong line endings.

**Diagnosis:**

```bash
file init.sh
# Output: init.sh: Bourne-Again shell script, ASCII text, with CRLF line terminators (BAD)
```

**Solutions:**

**1. Convert line endings:**

```bash
# Linux/macOS
dos2unix init.sh

# If dos2unix not installed:
sed -i 's/\r$//' init.sh
```

**2. Configure Git:**

```bash
# .gitattributes
*.sh text eol=lf
*.md text eol=lf
*.py text eol=lf
```

**3. Configure Git globally:**

```bash
# Windows: Checkout LF, commit LF
git config --global core.autocrlf input

# Unix: Don't convert
git config --global core.autocrlf false
```

---

## Environment Issues

### Python Version Mismatch

**Symptoms:**
```
ImportError: Cannot import name 'TypedDict' from 'typing'
Syntax error on 'match' statement (Python < 3.10)
```

**Diagnosis:**

```bash
python --version
# Requires: Python 3.10+
```

**Solutions:**

**1. Install correct Python version:**

```bash
# Ubuntu/Debian
sudo apt install python3.10

# macOS (Homebrew)
brew install python@3.10

# Windows
# Download from python.org
```

**2. Use pyenv:**

```bash
# Install pyenv
curl https://pyenv.run | bash

# Install Python 3.10
pyenv install 3.10.12
pyenv local 3.10.12

# Verify
python --version  # Should be 3.10.12
```

**3. Create virtual environment with specific version:**

```bash
python3.10 -m venv venv
source venv/bin/activate
python --version  # 3.10.12
```

### Node Version Mismatch

**Symptoms:**
```
npm ERR! Unsupported engine
Playwright fails to install
```

**Diagnosis:**

```bash
node --version
# Requires: Node 18+
```

**Solutions:**

**1. Use nvm (Node Version Manager):**

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install Node 18
nvm install 18
nvm use 18

# Verify
node --version  # v18.x.x
```

**2. Update Node:**

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node@18
```

### Missing Dependencies

**Symptoms:**
```
ModuleNotFoundError: No module named 'psutil'
ImportError: No module named 'fastapi'
```

**Diagnosis:**

```bash
pip list | grep psutil
# Empty output = not installed
```

**Solutions:**

**1. Install from requirements.txt:**

```bash
pip install -r requirements.txt
```

**2. Install individually:**

```bash
pip install psutil fastapi sqlalchemy claude-agent-sdk
```

**3. Check virtual environment:**

```bash
which python
# Should be: /path/to/autocoder-2/venv/bin/python
# If not: source venv/bin/activate
```

### Virtual Environment Issues

**Symptoms:**
```
Command 'python' not found
Packages installed but not found
```

**Diagnosis:**

```bash
# Check if venv activated
echo $VIRTUAL_ENV
# Should output: /path/to/autocoder-2/venv

# If empty, venv not activated
```

**Solutions:**

**1. Activate venv:**

```bash
# Windows
venv\Scripts\activate

# Unix
source venv/bin/activate
```

**2. Recreate venv if corrupted:**

```bash
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Use absolute path to Python:**

```bash
# Instead of:
python autonomous_agent_demo.py

# Use:
/path/to/autocoder-2/venv/bin/python autonomous_agent_demo.py
```

---

## Getting Help

### 1. Check Documentation

- **This Guide**: Cross-cutting issues
- **[PARALLEL_EXECUTION_GUIDE.md](PARALLEL_EXECUTION_GUIDE.md)**: Parallel execution troubleshooting
- **[SKIP_MANAGEMENT_USER_GUIDE.md](SKIP_MANAGEMENT_USER_GUIDE.md)**: Dependency and blocker issues
- **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)**: System design and data flow

### 2. Check Debug Logs

```bash
# Orchestrator logs
tail -100 orchestrator_debug.log | less

# Agent output (if using UI)
# Check Terminal panel in Web UI

# API server logs
# Check console where uvicorn is running
```

### 3. Enable Verbose Logging

```bash
# Python logging
export PYTHONVERBOSE=1
python autonomous_agent_demo.py --project-dir my-app

# MCP server logging
export MCP_DEBUG=1
python -m mcp_server.feature_mcp
```

### 4. Minimal Reproduction

Create a minimal test case:

```bash
# Start with empty project
python start.py
# 1. Create new project: "test-repro"
# 2. Use simple spec (5 features)

# Run with single agent
python autonomous_agent_demo.py --project-dir test-repro -c 1

# If issue reproduces, share:
# - Spec (prompts/app_spec.txt)
# - Database (features.db)
# - Logs (orchestrator_debug.log)
```

### 5. Report Issues

**GitHub Issues:** https://github.com/anthropics/claude-code/issues

**Include:**
- OS and version (Linux/macOS/Windows)
- Python version (`python --version`)
- Node version (`node --version`)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (truncate sensitive data)

**Example Issue:**

```markdown
### Bug: Agent hangs after claiming feature in parallel mode

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.10.12
- Node: 18.19.0
- Concurrency: 3

**Steps to Reproduce:**
1. Run `python autonomous_agent_demo.py --project-dir my-app -c 3`
2. Agent 1 claims feature #5
3. Agent hangs indefinitely (no output for 10+ minutes)

**Expected:** Agent implements feature #5

**Actual:** Agent hangs after printing "Feature #5 claimed"

**Logs:**
```
[14:23:45] Agent 1: Claiming next feature...
[14:23:46] Agent 1: Feature #5 claimed
(no further output)
```

**Database State:**
```sql
SELECT id, name, in_progress, passes FROM features WHERE id = 5;
-- id=5, in_progress=1, passes=0
```
```

---

## Summary

**Common Issues Quick Reference:**

| Issue | First Thing to Try |
|-------|-------------------|
| **Stale database** | `engine.dispose()` |
| **Database locked** | Kill blocking process with `lsof` → `kill -9` |
| **Slow agent** | Move to SSD, use `--model claude-haiku-3.5` |
| **High memory** | Restart orchestrator every 50 features |
| **WebSocket disconnects** | Add reconnection logic in UI |
| **MCP server crash** | Check `npx playwright install`, increase memory |
| **Bash command blocked** | Add to `ALLOWED_COMMANDS` in `security.py` |
| **Git conflict** | Use `git reset --hard HEAD` (WARNING: loses changes) |
| **Wrong Python** | Use `pyenv local 3.10`, recreate venv |

**Health Check Routine:**

1. Run `./health_check.sh my-app`
2. Check `orchestrator_debug.log` for errors
3. Verify database integrity: `sqlite3 my-app/features.db "PRAGMA integrity_check"`
4. Monitor memory: `watch -n 5 'free -h'`
5. Check disk space: `df -h`

**When in Doubt:**

1. Restart everything (orchestrator, API, UI)
2. Check logs (orchestrator, MCP, API)
3. Verify database state (use SQL queries)
4. Create minimal reproduction
5. Report issue with detailed logs

---

**Document Version:** 1.0
**Last Updated:** 2026-01-21
**Maintained By:** Autocoder Team
