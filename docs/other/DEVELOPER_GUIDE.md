# Skip Management Developer Guide

**Version:** 1.0
**Phase:** Phase 1 Complete
**Last Updated:** 2026-01-21

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [Core Modules](#core-modules)
4. [Integration Points](#integration-points)
5. [Extending the System](#extending-the-system)
6. [Testing](#testing)
7. [Performance Considerations](#performance-considerations)
8. [Security](#security)

---

## Architecture Overview

The Skip Management system consists of several interconnected modules:

```
┌─────────────────────────────────────────────────────────┐
│                    SKIP MANAGEMENT SYSTEM                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────┐ │
│  │   Dependency   │→│  Skip Impact   │→│  Blocker  │ │
│  │   Detector     │  │    Analyzer    │  │ Classifier│ │
│  └────────────────┘  └────────────────┘  └───────────┘ │
│          │                    │                  │       │
│          └────────────┬───────┴──────────────────┘       │
│                       ▼                                  │
│          ┌────────────────────────────┐                  │
│          │   Human Intervention       │                  │
│          │      Handler               │                  │
│          └────────────┬───────────────┘                  │
│                       │                                  │
│          ┌────────────▼───────────────┐                  │
│          │    Assumptions Workflow    │                  │
│          └────────────────────────────┘                  │
│                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────┐ │
│  │  BLOCKERS.md   │  │ Blockers CLI   │  │Assumptions│ │
│  │   Generator    │  │                │  │    CLI    │ │
│  └────────────────┘  └────────────────┘  └───────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   features.db   │
                  │   (SQLite)      │
                  └─────────────────┘
```

### Key Design Principles

1. **Separation of Concerns:** Each module has a single responsibility
2. **Database as Single Source of Truth:** All state in SQLite database
3. **Agent-Friendly:** Prompts and workflows designed for AI agents
4. **Human-in-the-Loop:** Graceful pause for human intervention
5. **Backward Compatible:** Migrations for existing databases

---

## Database Schema

### Feature Table (Extended)

```sql
CREATE TABLE features (
    -- Existing columns
    id INTEGER PRIMARY KEY,
    priority INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    steps JSON NOT NULL,
    passes BOOLEAN DEFAULT 0,
    in_progress BOOLEAN DEFAULT 0,

    -- Phase 1: Skip Management columns
    was_skipped BOOLEAN DEFAULT 0,
    skip_count INTEGER DEFAULT 0,
    blocker_type VARCHAR(50),           -- ENV_CONFIG, EXTERNAL_SERVICE, etc.
    blocker_description TEXT,
    is_blocked BOOLEAN DEFAULT 0,
    passing_with_mocks BOOLEAN DEFAULT 0
);
```

### FeatureDependency Table

```sql
CREATE TABLE feature_dependencies (
    id INTEGER PRIMARY KEY,
    feature_id INTEGER NOT NULL,
    depends_on_feature_id INTEGER NOT NULL,
    confidence REAL DEFAULT 1.0,        -- 0.0-1.0 confidence score
    detected_method VARCHAR(50) NOT NULL, -- 'explicit_id', 'keyword', 'category'
    detected_keywords JSON,             -- Keywords that triggered detection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (feature_id) REFERENCES features(id),
    FOREIGN KEY (depends_on_feature_id) REFERENCES features(id)
);
```

### FeatureAssumption Table

```sql
CREATE TABLE feature_assumptions (
    id INTEGER PRIMARY KEY,
    feature_id INTEGER NOT NULL,
    depends_on_feature_id INTEGER,
    assumption_text TEXT NOT NULL,
    code_location VARCHAR(500),         -- File path and line numbers
    impact_description TEXT,            -- What happens if wrong
    status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, VALIDATED, INVALID, NEEDS_REVIEW
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP,

    FOREIGN KEY (feature_id) REFERENCES features(id),
    FOREIGN KEY (depends_on_feature_id) REFERENCES features(id)
);
```

### FeatureBlocker Table

```sql
CREATE TABLE feature_blockers (
    id INTEGER PRIMARY KEY,
    feature_id INTEGER NOT NULL,
    blocker_type VARCHAR(50) NOT NULL,
    blocker_description TEXT NOT NULL,
    required_action TEXT,               -- What user needs to do
    required_values JSON,               -- List of env vars or config needed
    status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, RESOLVED, DEFERRED
    resolution_action VARCHAR(50),      -- PROVIDED, DEFERRED, MOCKED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,

    FOREIGN KEY (feature_id) REFERENCES features(id)
);
```

---

## Core Modules

### 1. dependency_detector.py

**Purpose:** Detect dependencies between features automatically

**Key Classes:**
```python
class DependencyDetector:
    def __init__(self, db_session: Session)

    def detect_dependencies(self, feature_id: int) -> List[FeatureDependency]
    def detect_all_dependencies(self) -> int
    def get_dependency_graph(self, max_depth: int = 3) -> Dict
```

**Detection Strategies:**
1. **Explicit ID References:** `#5`, `Feature 12`, `Task #3`
2. **Keyword Detection:** "after", "once", "depends on", "requires"
3. **Category-Based:** Implicit dependencies by feature category

**Confidence Scoring:**
- Explicit references: 95%
- Keyword detection: 75%
- Category-based: 65%

**Usage:**
```python
from dependency_detector import DependencyDetector
from api.database import create_database

_, SessionLocal = create_database(project_dir)
session = SessionLocal()

detector = DependencyDetector(session)
dependencies = detector.detect_dependencies(feature_id=12)

# Or detect all at once
count = detector.detect_all_dependencies()
print(f"Detected {count} dependencies")
```

### 2. skip_analyzer.py

**Purpose:** Analyze impact when a feature is skipped

**Key Classes:**
```python
class SkipImpactAnalyzer:
    def __init__(self, db_session: Session)

    def analyze_skip_impact(self, feature_id: int) -> Dict
    def get_dependent_features(self, feature_id: int, max_depth: int = 3) -> List[Feature]
    def cascade_skip(self, feature_id: int) -> int
```

**Impact Metrics:**
- **immediate_dependents:** Direct dependencies count
- **total_impact:** Cascade depth 2-3 levels
- **suggested_action:** SAFE_TO_SKIP, CASCADE_SKIP, IMPLEMENT_WITH_MOCKS, etc.

**Usage:**
```python
from skip_analyzer import SkipImpactAnalyzer

analyzer = SkipImpactAnalyzer(session)
impact = analyzer.analyze_skip_impact(feature_id=5)

print(f"Immediate dependents: {impact['immediate_dependents']}")
print(f"Total impact: {impact['total_impact']}")
print(f"Recommendation: {impact['suggested_action']}")

# If recommendation is CASCADE_SKIP:
count = analyzer.cascade_skip(feature_id=5)
print(f"Skipped {count} dependent features")
```

### 3. blocker_classifier.py

**Purpose:** Classify blocker types and extract required values

**Key Classes:**
```python
from enum import Enum

class BlockerType(Enum):
    ENV_CONFIG = "environment_config"
    EXTERNAL_SERVICE = "external_service"
    TECH_PREREQUISITE = "technical_prerequisite"
    UNCLEAR_REQUIREMENTS = "unclear_requirements"
    LEGITIMATE_DEFERRAL = "legitimate_deferral"

class BlockerClassifier:
    def classify_blocker_text(self, text: str) -> BlockerType
    def extract_required_values(self, text: str) -> List[str]
    def requires_human_intervention(self, blocker_type: BlockerType) -> bool
```

**Usage:**
```python
from blocker_classifier import BlockerClassifier, BlockerType

classifier = BlockerClassifier(session)
blocker_type = classifier.classify_blocker_text(
    "Missing OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET env vars"
)

if blocker_type == BlockerType.ENV_CONFIG:
    required = classifier.extract_required_values(description)
    print(f"Required env vars: {required}")
```

### 4. human_intervention.py

**Purpose:** Handle human-in-the-loop workflow for blockers

**Key Classes:**
```python
class HumanInterventionHandler:
    def handle_blocker(self, feature: Feature, blocker: FeatureBlocker) -> str
    def collect_env_values(self, required_values: List[str]) -> Dict[str, str]
    def write_to_env(self, values: Dict[str, str]) -> None
```

**Usage:**
```python
from human_intervention import HumanInterventionHandler

handler = HumanInterventionHandler(session, project_dir)

# When blocker detected:
action = handler.handle_blocker(feature, blocker)

# Returns: "RESUME_IMMEDIATELY", "SKIP_AND_DEFER", or "IMPLEMENT_WITH_MOCKS"
```

### 5. assumptions_workflow.py

**Purpose:** Track and review implementation assumptions

**Key Classes:**
```python
class AssumptionsWorkflow:
    def check_for_skipped_dependencies(self, feature_id: int) -> List[Dict]
    def get_assumption_prompt(self, current_feature_id: int, dependency_feature_id: int) -> str
    def create_assumption(self, feature_id: int, depends_on_feature_id: int, ...) -> FeatureAssumption
    def get_assumptions_for_review(self, completed_feature_id: int) -> List[FeatureAssumption]
    def validate_assumption(self, assumption_id: int) -> bool
    def invalidate_assumption(self, assumption_id: int) -> Tuple[bool, Optional[int]]
```

**Usage:**
```python
from assumptions_workflow import AssumptionsWorkflow

workflow = AssumptionsWorkflow(session)

# Before implementing feature with skipped dependency:
skipped_deps = workflow.check_for_skipped_dependencies(feature_id=12)
if skipped_deps:
    prompt = workflow.get_assumption_prompt(12, skipped_deps[0]['dependency_id'])
    # Include prompt in agent instructions

# After implementing:
assumption = workflow.create_assumption(
    feature_id=12,
    depends_on_feature_id=5,
    assumption_text="OAuth will use Google OAuth provider",
    code_location="src/api/users.js:145-152",
    impact_description="If different provider, avatar URL parsing needs update"
)

# When skipped feature is completed:
assumptions = workflow.get_assumptions_for_review(completed_feature_id=5)
for assumption in assumptions:
    # Review and validate/invalidate
    workflow.validate_assumption(assumption.id)
```

---

## Integration Points

### Integration with Agent Workflow

**In `agent.py` or `autonomous_agent_demo.py`:**

```python
from dependency_detector import DependencyDetector
from skip_analyzer import SkipImpactAnalyzer
from assumptions_workflow import AssumptionsWorkflow, should_document_assumptions, should_review_assumptions

# 1. On Session Start: Run dependency detection
detector = DependencyDetector(db_session)
detector.detect_all_dependencies()

# 2. Before implementing a feature: Check for skipped dependencies
if should_document_assumptions(db_session, feature.id):
    workflow = AssumptionsWorkflow(db_session)
    skipped_deps = workflow.check_for_skipped_dependencies(feature.id)

    for dep in skipped_deps:
        # Add assumption prompt to agent context
        prompt = workflow.get_assumption_prompt(feature.id, dep['dependency_id'])
        # Include in agent instructions

# 3. When agent decides to skip a feature:
from human_intervention import handle_feature_skip

should_pause, action = handle_feature_skip(project_dir, feature.id, skip_reason)

if action == "RETRY":
    # Don't skip, retry immediately
    continue
elif action == "MOCK":
    # Implement with mocks
    feature.passing_with_mocks = True
elif action == "SKIP":
    # Skip normally
    feature.was_skipped = True
    feature.skip_count += 1

# 4. When marking a feature as passing:
if feature.was_skipped and should_review_assumptions(db_session, feature.id):
    workflow = AssumptionsWorkflow(db_session)
    review_prompt = workflow.get_assumption_review_prompt(feature.id)

    # Agent reviews assumptions and reports findings
    # Mark assumptions as needing review
    count = workflow.mark_assumptions_for_review(feature.id)
```

### Integration with MCP Server

**In `mcp_server/feature_mcp.py`:**

```python
# Add new MCP tools:

@server.call_tool()
async def feature_check_dependencies(arguments: dict) -> list[TextContent]:
    """Check if a feature has dependencies on skipped features."""
    feature_id = arguments["feature_id"]
    workflow = AssumptionsWorkflow(db)
    skipped_deps = workflow.check_for_skipped_dependencies(feature_id)

    if skipped_deps:
        return [TextContent(
            type="text",
            text=json.dumps({
                "has_skipped_dependencies": True,
                "dependencies": skipped_deps
            })
        )]
    else:
        return [TextContent(type="text", text=json.dumps({"has_skipped_dependencies": False}))]

@server.call_tool()
async def feature_create_assumption(arguments: dict) -> list[TextContent]:
    """Create an assumption about a skipped dependency."""
    workflow = AssumptionsWorkflow(db)
    assumption = workflow.create_assumption(
        feature_id=arguments["feature_id"],
        depends_on_feature_id=arguments["depends_on_feature_id"],
        assumption_text=arguments["assumption_text"],
        code_location=arguments.get("code_location"),
        impact_description=arguments.get("impact_description")
    )

    return [TextContent(type="text", text=json.dumps({"assumption_id": assumption.id}))]
```

---

## Extending the System

### Adding New Blocker Types

1. **Define the blocker type** in `blocker_classifier.py`:

```python
class BlockerType(Enum):
    # ... existing types ...
    CUSTOM_BLOCKER = "custom_blocker_name"
```

2. **Add classification keywords** in `BlockerClassifier._get_blocker_keywords()`:

```python
BlockerType.CUSTOM_BLOCKER: [
    "custom keyword 1",
    "custom keyword 2",
    "pattern that indicates this blocker"
]
```

3. **Update human intervention logic** in `human_intervention.py` if needed.

### Adding Custom Dependency Detection Strategies

Extend `DependencyDetector` with new detection methods:

```python
class CustomDependencyDetector(DependencyDetector):
    def detect_dependencies(self, feature_id: int) -> List[FeatureDependency]:
        # Call parent detection
        dependencies = super().detect_dependencies(feature_id)

        # Add custom detection logic
        custom_deps = self._detect_custom_pattern(feature_id)
        dependencies.extend(custom_deps)

        return dependencies

    def _detect_custom_pattern(self, feature_id: int) -> List[FeatureDependency]:
        # Your custom detection logic
        pass
```

### Adding Custom Assumption Validation

Extend `AssumptionsWorkflow` with custom validation:

```python
class CustomAssumptionsWorkflow(AssumptionsWorkflow):
    def auto_validate_assumptions(self, completed_feature_id: int) -> List[int]:
        """Automatically validate assumptions based on code analysis."""
        assumptions = self.get_assumptions_for_review(completed_feature_id)

        validated_ids = []
        for assumption in assumptions:
            # Custom validation logic (e.g., parse code, check implementations)
            if self._is_assumption_valid(assumption):
                self.validate_assumption(assumption.id)
                validated_ids.append(assumption.id)
            else:
                self.invalidate_assumption(assumption.id)

        return validated_ids

    def _is_assumption_valid(self, assumption: FeatureAssumption) -> bool:
        # Your custom validation logic
        pass
```

---

## Testing

### Running Tests

```bash
# Run all Phase 1 integration tests
pytest tests/test_phase1_integration.py -v

# Run specific test class
pytest tests/test_phase1_integration.py::TestDependencyDetection -v

# Run with coverage
pytest tests/test_phase1_integration.py --cov=. --cov-report=html
```

### Writing New Tests

**Template for integration tests:**

```python
import pytest
from pathlib import Path
from api.database import create_database, Feature

@pytest.fixture
def db_session(temp_project_dir):
    """Create a database session for testing."""
    _, SessionLocal = create_database(temp_project_dir)
    session = SessionLocal()
    yield session
    session.close()

def test_your_feature(db_session):
    """Test description."""
    # Setup: Create test data
    feature = Feature(
        priority=1,
        category="test",
        name="Test feature",
        description="Test",
        steps=["Step 1"]
    )
    db_session.add(feature)
    db_session.commit()

    # Execute: Call your function
    result = your_function(db_session, feature.id)

    # Assert: Verify results
    assert result is not None
    assert result.some_field == expected_value
```

---

## Performance Considerations

### Dependency Detection Performance

**Issue:** O(n²) complexity when detecting all dependencies

**Optimization:**
```python
# Cache feature data to reduce database queries
class DependencyDetector:
    def __init__(self, db_session: Session):
        self.db = db_session
        self._feature_cache = {}  # Cache features

    def _get_all_features(self) -> List[Feature]:
        if not self._feature_cache:
            features = self.db.query(Feature).all()
            self._feature_cache = {f.id: f for f in features}
        return list(self._feature_cache.values())
```

### Database Query Optimization

**Use indexes:**
```sql
CREATE INDEX idx_feature_dependencies_feature_id ON feature_dependencies(feature_id);
CREATE INDEX idx_feature_dependencies_depends_on ON feature_dependencies(depends_on_feature_id);
CREATE INDEX idx_feature_assumptions_feature_id ON feature_assumptions(feature_id);
CREATE INDEX idx_feature_assumptions_depends_on ON feature_assumptions(depends_on_feature_id);
CREATE INDEX idx_feature_blockers_feature_id ON feature_blockers(feature_id);
CREATE INDEX idx_feature_blockers_status ON feature_blockers(status);
```

**Batch queries:**
```python
# Instead of:
for feature in features:
    deps = db.query(FeatureDependency).filter(
        FeatureDependency.feature_id == feature.id
    ).all()

# Do:
feature_ids = [f.id for f in features]
all_deps = db.query(FeatureDependency).filter(
    FeatureDependency.feature_id.in_(feature_ids)
).all()

# Group by feature_id
deps_by_feature = {}
for dep in all_deps:
    if dep.feature_id not in deps_by_feature:
        deps_by_feature[dep.feature_id] = []
    deps_by_feature[dep.feature_id].append(dep)
```

---

## Security

### Environment Variable Handling

**Never log or expose secrets:**

```python
# Good:
print("✓ OAUTH_CLIENT_SECRET provided (masked)")

# Bad:
print(f"OAUTH_CLIENT_SECRET: {value}")  # Exposes secret!
```

**Mask input for secrets:**

```python
import getpass

if is_secret_field(field_name):
    value = getpass.getpass(f"{field_name}: ")
else:
    value = input(f"{field_name}: ")
```

### .env File Security

**Set proper permissions:**

```python
import os
import stat

env_file = project_dir / ".env"
env_file.touch(mode=0o600)  # -rw------- (owner read/write only)
```

**Never commit .env files:**

```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

### SQL Injection Prevention

**Always use parameterized queries:**

```python
# Good (SQLAlchemy ORM - automatically parameterized):
feature = db.query(Feature).filter(Feature.id == feature_id).first()

# Good (raw SQL with parameters):
result = db.execute(text("SELECT * FROM features WHERE id = :id"), {"id": feature_id})

# Bad (vulnerable to SQL injection):
result = db.execute(f"SELECT * FROM features WHERE id = {feature_id}")  # DON'T DO THIS!
```

---

## API Reference

### Full Module Documentation

For detailed API reference, see:
- `dependency_detector.py`: 415 lines, 15 public methods
- `skip_analyzer.py`: 325 lines, 10 public methods
- `blocker_classifier.py`: 380 lines, 8 public methods
- `human_intervention.py`: 340 lines, 12 public methods
- `blockers_md_generator.py`: 320 lines, 6 public methods
- `blockers_cli.py`: 420 lines, CLI interface
- `assumptions_workflow.py`: New, 12 public methods
- `assumptions_cli.py`: New, CLI interface

---

## Contributing

### Code Style

- **PEP 8** compliance
- **Type hints** for all function signatures
- **Docstrings** for all public methods
- **Clear variable names** (no single-letter except iterators)

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints included
- [ ] No security vulnerabilities
- [ ] Performance tested (for O(n²) operations)
- [ ] Backward compatible (migrations included)

---

## Next Steps

- **User Guide:** Learn how to use skip management features
- **Troubleshooting Guide:** Debug common issues
- **Phase 2 Planning:** Benchmarking & Performance Metrics

---

**Need Help?**
- Check [User Guide](./SKIP_MANAGEMENT_USER_GUIDE.md)
- See [Troubleshooting Guide](./TROUBLESHOOTING.md)
- Report issues at: https://github.com/anthropics/autocoder/issues
