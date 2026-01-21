# Skip Management Troubleshooting Guide

**Version:** 1.0
**Phase:** Phase 1 Complete
**Last Updated:** 2026-01-21

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Database Issues](#database-issues)
4. [Dependency Detection Issues](#dependency-detection-issues)
5. [Blocker Management Issues](#blocker-management-issues)
6. [Assumption Tracking Issues](#assumption-tracking-issues)
7. [Performance Issues](#performance-issues)
8. [Integration Issues](#integration-issues)

---

## Quick Diagnostics

### Health Check Script

Run this to diagnose common issues:

```bash
# Create health_check.sh
cat > health_check.sh << 'EOF'
#!/bin/bash

PROJECT_DIR="${1:-.}"
echo "=== Skip Management Health Check ==="
echo "Project: $PROJECT_DIR"
echo

# 1. Check database exists
if [ -f "$PROJECT_DIR/features.db" ]; then
    echo "✓ Database exists"
else
    echo "✗ Database not found"
    exit 1
fi

# 2. Check schema
python3 << PYTHON
from pathlib import Path
from sqlalchemy import inspect, create_engine

db_path = Path("$PROJECT_DIR") / "features.db"
engine = create_engine(f"sqlite:///{db_path}")
inspector = inspect(engine)

required_tables = ["features", "feature_dependencies", "feature_assumptions", "feature_blockers"]
for table in required_tables:
    if table in inspector.get_table_names():
        print(f"✓ Table '{table}' exists")
    else:
        print(f"✗ Table '{table}' missing")
PYTHON

# 3. Check CLI tools
if [ -f "dependency_detector.py" ]; then
    echo "✓ dependency_detector.py exists"
else
    echo "✗ dependency_detector.py missing"
fi

if [ -f "assumptions_cli.py" ]; then
    echo "✓ assumptions_cli.py exists"
else
    echo "✗ assumptions_cli.py missing"
fi

if [ -f "blockers_cli.py" ]; then
    echo "✓ blockers_cli.py exists"
else
    echo "✗ blockers_cli.py missing"
fi

echo
echo "=== Health Check Complete ==="
EOF

chmod +x health_check.sh
./health_check.sh my-app
```

---

## Common Issues

### Issue: Feature Keeps Getting Skipped

**Symptoms:**
- Same feature skips multiple times
- `skip_count` increases
- No progress on specific features

**Diagnosis:**
```bash
# Check skip history
python blockers_cli.py --project-dir my-app --show-blockers

# Check feature details
sqlite3 my-app/features.db "SELECT id, name, was_skipped, skip_count, blocker_type FROM features WHERE was_skipped = 1;"
```

**Solutions:**

1. **If blocker is ENV_CONFIG:**
```bash
# Add missing environment variables
echo "OAUTH_CLIENT_ID=your-value" >> .env
echo "OAUTH_CLIENT_SECRET=your-value" >> .env

# Unblock the feature
python blockers_cli.py --project-dir my-app --unblock <feature_id>
```

2. **If blocker is TECH_PREREQUISITE:**
```bash
# Check dependencies
python blockers_cli.py --project-dir my-app --dependencies <feature_id>

# Ensure prerequisite feature is completed first
sqlite3 my-app/features.db "SELECT id, name, passes FROM features WHERE id = <dependency_id>;"
```

3. **If blocker is UNCLEAR_REQUIREMENTS:**
```bash
# Update feature description with clearer requirements
# Then unblock
python blockers_cli.py --project-dir my-app --unblock <feature_id>
```

### Issue: Dependencies Not Detected

**Symptoms:**
- Expected dependencies missing
- Skip impact analysis shows no dependents
- Features implemented in wrong order

**Diagnosis:**
```bash
# Run dependency detection
python dependency_detector.py my-app

# Check detected dependencies
sqlite3 my-app/features.db "SELECT f1.name AS 'Feature', f2.name AS 'Depends On', d.confidence, d.detected_method FROM feature_dependencies d JOIN features f1 ON d.feature_id = f1.id JOIN features f2 ON d.depends_on_feature_id = f2.id;"
```

**Solutions:**

1. **Make dependencies explicit in description:**
```bash
# Update feature description to include explicit references
# Bad:  "Show OAuth avatar"
# Good: "After feature #5 (OAuth) is done, show OAuth avatar"
```

2. **Manually add dependency:**
```bash
sqlite3 my-app/features.db << EOF
INSERT INTO feature_dependencies (feature_id, depends_on_feature_id, confidence, detected_method)
VALUES (12, 5, 1.0, 'manual');
EOF
```

3. **Lower confidence threshold (if too strict):**
```python
# In dependency_detector.py, adjust thresholds
CONFIDENCE_THRESHOLDS = {
    'explicit_id_reference': 0.95,
    'keyword_detection': 0.60,  # Lower from 0.75
    'category_based': 0.50,      # Lower from 0.65
}
```

### Issue: BLOCKERS.md Not Updating

**Symptoms:**
- `BLOCKERS.md` file out of sync
- Unblocked features still shown
- Missing blockers

**Diagnosis:**
```bash
# Check database blockers
sqlite3 my-app/features.db "SELECT f.id, f.name, b.blocker_type, b.status FROM features f JOIN feature_blockers b ON f.id = b.feature_id WHERE b.status = 'ACTIVE';"

# Check file modification time
ls -la my-app/BLOCKERS.md
```

**Solutions:**

1. **Regenerate BLOCKERS.md:**
```bash
python blockers_md_generator.py my-app
```

2. **Check file permissions:**
```bash
# Ensure writable
chmod 644 my-app/BLOCKERS.md
```

3. **Verify auto-generation is enabled:**
```python
# In human_intervention.py or blockers_cli.py
# Ensure this is called after blockers change:
from blockers_md_generator import BlockersMdGenerator
generator = BlockersMdGenerator(session)
generator.update(project_dir)
```

### Issue: Assumptions Not Being Tracked

**Symptoms:**
- No assumptions in database
- Assumption prompts not shown to agent
- Review workflow doesn't find assumptions

**Diagnosis:**
```bash
# Check if assumptions exist
sqlite3 my-app/features.db "SELECT COUNT(*) FROM feature_assumptions;"

# Check for skipped dependencies
python assumptions_cli.py --project-dir my-app --show-all
```

**Solutions:**

1. **Ensure dependencies are detected first:**
```bash
python dependency_detector.py my-app
```

2. **Verify feature references skipped dependency:**
```bash
# Feature description should mention the skipped feature
sqlite3 my-app/features.db "SELECT id, name, description FROM features WHERE id = <feature_id>;"
```

3. **Manually create assumption:**
```python
from assumptions_workflow import AssumptionsWorkflow
from api.database import create_database

_, SessionLocal = create_database(Path("my-app"))
session = SessionLocal()
workflow = AssumptionsWorkflow(session)

assumption = workflow.create_assumption(
    feature_id=12,
    depends_on_feature_id=5,
    assumption_text="OAuth will use Google OAuth provider",
    code_location="src/api/users.js:145"
)
print(f"Created assumption #{assumption.id}")
```

---

## Database Issues

### Issue: Database Schema Missing Columns

**Symptoms:**
- `OperationalError: no such column: was_skipped`
- Import errors related to FeatureDependency, FeatureAssumption, etc.

**Diagnosis:**
```bash
# Check schema
sqlite3 my-app/features.db ".schema features"
```

**Solution:**

Run migration:
```python
from api.database import create_database
from pathlib import Path

_, SessionLocal = create_database(Path("my-app"))
print("Migration complete")
```

Or manually:
```bash
sqlite3 my-app/features.db << EOF
-- Add Phase 1 columns to features table
ALTER TABLE features ADD COLUMN was_skipped BOOLEAN DEFAULT 0;
ALTER TABLE features ADD COLUMN skip_count INTEGER DEFAULT 0;
ALTER TABLE features ADD COLUMN blocker_type VARCHAR(50);
ALTER TABLE features ADD COLUMN blocker_description TEXT;
ALTER TABLE features ADD COLUMN is_blocked BOOLEAN DEFAULT 0;
ALTER TABLE features ADD COLUMN passing_with_mocks BOOLEAN DEFAULT 0;

-- Create new tables (if missing)
CREATE TABLE IF NOT EXISTS feature_dependencies (
    id INTEGER PRIMARY KEY,
    feature_id INTEGER NOT NULL,
    depends_on_feature_id INTEGER NOT NULL,
    confidence REAL DEFAULT 1.0,
    detected_method VARCHAR(50) NOT NULL,
    detected_keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feature_id) REFERENCES features(id),
    FOREIGN KEY (depends_on_feature_id) REFERENCES features(id)
);

CREATE TABLE IF NOT EXISTS feature_assumptions (
    id INTEGER PRIMARY KEY,
    feature_id INTEGER NOT NULL,
    depends_on_feature_id INTEGER,
    assumption_text TEXT NOT NULL,
    code_location VARCHAR(500),
    impact_description TEXT,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP,
    FOREIGN KEY (feature_id) REFERENCES features(id),
    FOREIGN KEY (depends_on_feature_id) REFERENCES features(id)
);

CREATE TABLE IF NOT EXISTS feature_blockers (
    id INTEGER PRIMARY KEY,
    feature_id INTEGER NOT NULL,
    blocker_type VARCHAR(50) NOT NULL,
    blocker_description TEXT NOT NULL,
    required_action TEXT,
    required_values TEXT,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    resolution_action VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (feature_id) REFERENCES features(id)
);
EOF
```

### Issue: Database Locked

**Symptoms:**
- `database is locked` error
- Timeouts when accessing database
- Cannot update features

**Diagnosis:**
```bash
# Check for lock file
ls -la my-app/features.db-shm
ls -la my-app/features.db-wal

# Check for open connections
lsof my-app/features.db
```

**Solutions:**

1. **Close all connections:**
```bash
# Kill processes holding database
lsof my-app/features.db | awk '{print $2}' | tail -n +2 | xargs kill -9
```

2. **Increase timeout:**
```python
# In api/database.py
engine = create_engine(db_url, connect_args={
    "check_same_thread": False,
    "timeout": 60  # Increase from 30 to 60 seconds
})
```

3. **Use WAL mode (better concurrency):**
```bash
sqlite3 my-app/features.db "PRAGMA journal_mode=WAL;"
```

### Issue: Database Corruption

**Symptoms:**
- `malformed database`
- Query errors
- Missing data

**Diagnosis:**
```bash
# Check integrity
sqlite3 my-app/features.db "PRAGMA integrity_check;"
```

**Solutions:**

1. **Recover from backup:**
```bash
cp my-app/features.db.backup my-app/features.db
```

2. **Export and reimport:**
```bash
# Export
sqlite3 my-app/features.db .dump > features_backup.sql

# Reimport
rm my-app/features.db
sqlite3 my-app/features.db < features_backup.sql
```

3. **Recreate from scratch (if no backup):**
```python
from api.database import create_database
from pathlib import Path

# Backup corrupted database
Path("my-app/features.db").rename("my-app/features.db.corrupted")

# Create new database
_, SessionLocal = create_database(Path("my-app"))
print("New database created")
```

---

## Dependency Detection Issues

### Issue: False Positives in Dependencies

**Symptoms:**
- Dependencies detected that don't exist
- Wrong features linked
- Confidence scores too high

**Solutions:**

1. **Remove false positive:**
```bash
sqlite3 my-app/features.db "DELETE FROM feature_dependencies WHERE id = <dependency_id>;"
```

2. **Adjust confidence threshold:**
```python
# In skip_analyzer.py or dependency_detector.py
MIN_CONFIDENCE = 0.80  # Increase from 0.65
```

3. **Review detected keywords:**
```bash
sqlite3 my-app/features.db "SELECT feature_id, depends_on_feature_id, detected_keywords FROM feature_dependencies WHERE detected_method = 'keyword_detection';"
```

### Issue: Circular Dependencies Detected

**Symptoms:**
- Feature A depends on Feature B depends on Feature A
- Infinite loops in dependency graphs
- Stack overflow in recursive functions

**Diagnosis:**
```bash
# Find circular dependencies
python3 << EOF
from pathlib import Path
from api.database import create_database
from dependency_detector import DependencyDetector

_, SessionLocal = create_database(Path("my-app"))
session = SessionLocal()
detector = DependencyDetector(session)

# Check for cycles
try:
    graph = detector.get_dependency_graph(max_depth=10)
    print("No circular dependencies detected")
except RecursionError:
    print("Circular dependency detected!")
EOF
```

**Solutions:**

1. **Manually break the cycle:**
```bash
# Identify the weakest link (lowest confidence)
sqlite3 my-app/features.db "SELECT id, feature_id, depends_on_feature_id, confidence FROM feature_dependencies WHERE feature_id IN (12, 15) AND depends_on_feature_id IN (12, 15);"

# Delete the weakest link
sqlite3 my-app/features.db "DELETE FROM feature_dependencies WHERE id = <weakest_link_id>;"
```

2. **Add cycle detection:**
```python
# In dependency_detector.py
def _detect_cycle(self, feature_id: int, visited: set = None) -> bool:
    if visited is None:
        visited = set()

    if feature_id in visited:
        return True  # Cycle detected

    visited.add(feature_id)

    deps = self.db.query(FeatureDependency).filter(
        FeatureDependency.feature_id == feature_id
    ).all()

    for dep in deps:
        if self._detect_cycle(dep.depends_on_feature_id, visited.copy()):
            return True

    return False
```

---

## Blocker Management Issues

### Issue: Blocker Classification Wrong

**Symptoms:**
- ENV_CONFIG blocker classified as EXTERNAL_SERVICE
- Wrong prompts shown to user
- Incorrect resolution workflow

**Solutions:**

1. **Reclassify manually:**
```bash
sqlite3 my-app/features.db "UPDATE feature_blockers SET blocker_type = 'ENV_CONFIG' WHERE id = <blocker_id>;"
```

2. **Improve keyword detection:**
```python
# In blocker_classifier.py, add more keywords
BlockerType.ENV_CONFIG: [
    "environment variable", "env var", "missing", "api key",
    "secret", "credential", "token", ".env",
    # Add your custom keywords
    "configuration", "config value"
]
```

### Issue: Required Values Not Extracted

**Symptoms:**
- `required_values` field is empty
- User doesn't know what to provide
- Generic error messages

**Solutions:**

1. **Manually set required values:**
```bash
sqlite3 my-app/features.db "UPDATE feature_blockers SET required_values = '[\"OAUTH_CLIENT_ID\", \"OAUTH_CLIENT_SECRET\"]' WHERE id = <blocker_id>;"
```

2. **Improve extraction regex:**
```python
# In blocker_classifier.py
import re

def extract_required_values(self, text: str) -> List[str]:
    # Match uppercase words with underscores (env var pattern)
    matches = re.findall(r'\b[A-Z][A-Z0-9_]{2,}\b', text)

    # Also match words after "missing", "need", "require"
    context_matches = re.findall(
        r'(?:missing|need|require|must provide)\s+([A-Z][A-Z0-9_]+)',
        text,
        re.IGNORECASE
    )

    return list(set(matches + context_matches))
```

---

## Assumption Tracking Issues

### Issue: Assumption Review Not Triggered

**Symptoms:**
- Feature completed but assumptions not reviewed
- No "ASSUMPTION REVIEW REQUIRED" message
- Assumptions stay in ACTIVE status

**Diagnosis:**
```bash
# Check if feature was skipped
sqlite3 my-app/features.db "SELECT id, name, was_skipped, passes FROM features WHERE id = <feature_id>;"

# Check if assumptions exist
sqlite3 my-app/features.db "SELECT COUNT(*) FROM feature_assumptions WHERE depends_on_feature_id = <feature_id>;"
```

**Solutions:**

1. **Manually trigger review:**
```bash
python assumptions_cli.py --project-dir my-app --review <feature_id>
```

2. **Ensure integration in agent:**
```python
# In agent.py, after marking feature as passing:
from assumptions_workflow import should_review_assumptions, AssumptionsWorkflow

if feature.was_skipped and should_review_assumptions(db_session, feature.id):
    workflow = AssumptionsWorkflow(db_session)
    review_prompt = workflow.get_assumption_review_prompt(feature.id)
    # Include prompt in agent context
    workflow.mark_assumptions_for_review(feature.id)
```

### Issue: Cannot Validate/Invalidate Assumptions

**Symptoms:**
- CLI commands fail
- Status not updating
- Permission errors

**Solutions:**

1. **Check assumption exists:**
```bash
sqlite3 my-app/features.db "SELECT id, status FROM feature_assumptions WHERE id = <assumption_id>;"
```

2. **Update status directly:**
```bash
# Validate
sqlite3 my-app/features.db "UPDATE feature_assumptions SET status = 'VALIDATED', validated_at = datetime('now') WHERE id = <assumption_id>;"

# Invalidate
sqlite3 my-app/features.db "UPDATE feature_assumptions SET status = 'INVALID', validated_at = datetime('now') WHERE id = <assumption_id>;"
```

---

## Performance Issues

### Issue: Dependency Detection is Slow

**Symptoms:**
- `detect_all_dependencies()` takes minutes
- High CPU usage
- Many database queries

**Solutions:**

1. **Use batch detection:**
```python
# Cache features to reduce queries
detector = DependencyDetector(session)
detector._feature_cache = {f.id: f for f in session.query(Feature).all()}
detector.detect_all_dependencies()
```

2. **Add indexes:**
```bash
sqlite3 my-app/features.db << EOF
CREATE INDEX IF NOT EXISTS idx_features_category ON features(category);
CREATE INDEX IF NOT EXISTS idx_feature_deps_feature ON feature_dependencies(feature_id);
CREATE INDEX IF NOT EXISTS idx_feature_deps_depends_on ON feature_dependencies(depends_on_feature_id);
EOF
```

3. **Limit detection scope:**
```python
# Only detect for features without dependencies
features_without_deps = session.query(Feature).filter(
    ~Feature.id.in_(
        session.query(FeatureDependency.feature_id)
    )
).all()

for feature in features_without_deps:
    detector.detect_dependencies(feature.id)
```

### Issue: Skip Impact Analysis Hangs

**Symptoms:**
- `analyze_skip_impact()` never returns
- Stack overflow
- Infinite recursion

**Solutions:**

1. **Limit recursion depth:**
```python
# In skip_analyzer.py
def analyze_skip_impact(self, feature_id: int, max_depth: int = 2) -> Dict:
    # Reduce from 3 to 2
    ...
```

2. **Add memoization:**
```python
from functools import lru_cache

class SkipImpactAnalyzer:
    @lru_cache(maxsize=128)
    def _get_dependents_cached(self, feature_id: int, depth: int) -> Tuple:
        # Cache results
        ...
```

---

## Integration Issues

### Issue: Agent Not Using Skip Management

**Symptoms:**
- Features skipped but no blocker classification
- No dependency detection
- No assumption tracking

**Solutions:**

1. **Verify integration in agent.py:**
```python
# Should have these imports
from dependency_detector import DependencyDetector
from skip_analyzer import SkipImpactAnalyzer
from assumptions_workflow import AssumptionsWorkflow

# Should call on session start
detector = DependencyDetector(db_session)
detector.detect_all_dependencies()
```

2. **Check MCP server integration:**
```bash
# Verify MCP tools are available
# In agent prompt or logs, should see:
# - feature_check_dependencies
# - feature_create_assumption
```

### Issue: CLI Tools Not Found

**Symptoms:**
- `command not found: python blockers_cli.py`
- Import errors
- Module not found

**Solutions:**

1. **Ensure tools are in correct location:**
```bash
ls -la | grep -E "(dependency_detector|assumptions_cli|blockers_cli)\.py"
```

2. **Add to PATH:**
```bash
export PATH="$PATH:$(pwd)"
```

3. **Use absolute paths:**
```bash
python /full/path/to/blockers_cli.py --project-dir my-app --show-blockers
```

---

## Getting Help

If you're still stuck after trying these solutions:

1. **Check logs:**
```bash
# Agent logs
tail -f agent.log

# Database queries
sqlite3 my-app/features.db ".log stdout"
```

2. **Run health check:**
```bash
./health_check.sh my-app
```

3. **Create minimal reproduction:**
```python
# Minimal script to reproduce issue
from pathlib import Path
from api.database import create_database, Feature

project_dir = Path("test-project")
project_dir.mkdir(exist_ok=True)

_, SessionLocal = create_database(project_dir)
session = SessionLocal()

# Add minimal test data
feature = Feature(
    priority=1,
    category="test",
    name="Test feature",
    description="Test",
    steps=["Step 1"]
)
session.add(feature)
session.commit()

# Reproduce issue here
...
```

4. **Report issue:**
- Include Python version: `python --version`
- Include SQLite version: `sqlite3 --version`
- Include error messages (full traceback)
- Include database schema: `sqlite3 my-app/features.db ".schema"`
- Report at: https://github.com/anthropics/autocoder/issues

---

**Document Version:** 1.0
**Last Updated:** 2026-01-21
**Feedback:** Please report documentation issues or suggest improvements
