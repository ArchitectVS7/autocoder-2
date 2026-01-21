# Autocoder Enhancement - Phased Implementation Plan

**Version:** 1.0
**Created:** 2026-01-21
**Based on:** PRD_ENHANCEMENT.md
**Status:** Ready for Implementation

---

## Executive Summary

This document provides a detailed, phased implementation plan for upgrading the autocoder system with multi-agent UX evaluation, design iteration, and intelligent skip management capabilities.

**Phase Priority (Re-ordered based on user feedback):**
1. **Phase 1** - Skip Management & Dependency Tracking (Weeks 1-2)
2. **Phase 2** - Benchmarking & Performance Metrics (Week 3)
3. **Phase 3** - Checkpoint System (Weeks 4-5)
4. **Phase 4** - Design Iteration with Personas (Weeks 6-8)
5. **Phase 5** - Playwright + Visual UX Evaluation (Weeks 9-11)
6. **Phase 6** - Integration & Polish (Week 12)

**Total Timeline:** 12 weeks
**Critical Path:** Phases 1-2 (foundational for all other features)

---

## Phase Prioritization Rationale

Based on user feedback, we're prioritizing:

1. **Skip Management First** - Prevents rework and wasted effort when skipped features are eventually implemented
2. **Benchmarking Early** - Validates that autocoder provides real value vs simpler alternatives
3. **Checkpoints Next** - Quality gates during development
4. **Design Iteration** - Pre-development validation (high value but can come after basics)
5. **Visual UX Last** - Nice-to-have, requires Playwright infrastructure

---

## PHASE 1: Intelligent Skip Management & Dependency Tracking

**Timeline:** 2 weeks
**Priority:** 🔴 CRITICAL
**Effort:** High
**User Need:** "When we come back later and code the skipped feature, we don't want re-work"

### Goals

- Track dependencies between features automatically
- Detect when skipping a feature will impact downstream work
- Provide human-in-the-loop workflow for blockers (env vars, API keys)
- Create blocker dashboard and unblock commands
- Document implementation assumptions when building on skipped features

### Week 1: Foundation (Tasks 1.1 - 1.4)

#### Task 1.1: Database Schema Extensions (2 days)
**Owner:** Backend
**Dependencies:** None

**Deliverables:**
- Add `dependencies` table to `features.db`
  - `id`, `feature_id`, `depends_on_feature_id`, `confidence`, `detected_method`
- Add `feature_assumptions` table
  - `id`, `feature_id`, `assumption_text`, `depends_on_feature_id`, `created_at`
- Add `feature_blockers` table
  - `id`, `feature_id`, `blocker_type`, `blocker_description`, `required_action`, `status`
- Migration script: `migrations/005_add_dependencies.py`

**Validation:**
```bash
# Test migration
python -m pytest tests/test_dependencies_schema.py
```

---

#### Task 1.2: Dependency Detection Engine (3 days)
**Owner:** ML/NLP
**Dependencies:** Task 1.1

**Deliverables:**
- `dependency_detector.py` - Analyzes feature descriptions for dependencies
- Keyword detection: "requires", "depends on", "after", "once X is done"
- Feature ID reference detection: "#5", "Feature 12"
- Category-based detection: "authentication", "payment", etc.
- Confidence scoring (0.0 - 1.0)

**Detection Examples:**
```python
# Input
feature = {
    "id": 15,
    "description": "After OAuth is implemented, show user's avatar from provider"
}

# Output
dependencies = [
    {
        "depends_on": 5,  # OAuth feature
        "confidence": 0.85,
        "method": "keyword_detection",
        "keywords": ["after", "OAuth"]
    }
]
```

**Implementation:**
```python
# dependency_detector.py
import re
from typing import List, Dict

class DependencyDetector:
    DEPENDENCY_KEYWORDS = [
        "requires", "depends on", "after", "once",
        "when", "needs", "prerequisite", "blocked by"
    ]

    def detect(self, feature: Dict, all_features: List[Dict]) -> List[Dict]:
        """Detect dependencies for a feature."""
        dependencies = []

        # 1. Explicit feature ID references
        dependencies.extend(self._detect_id_references(feature))

        # 2. Keyword-based detection
        dependencies.extend(self._detect_keywords(feature, all_features))

        # 3. Category-based detection
        dependencies.extend(self._detect_categories(feature, all_features))

        return self._deduplicate_and_score(dependencies)

    def _detect_id_references(self, feature: Dict) -> List[Dict]:
        """Find explicit feature ID references like '#5' or 'Feature 12'"""
        pattern = r'(?:#|Feature\s+)(\d+)'
        matches = re.findall(pattern, feature['description'], re.IGNORECASE)
        return [
            {
                'depends_on': int(match),
                'confidence': 0.95,
                'method': 'explicit_id_reference'
            }
            for match in matches
        ]

    # ... additional methods
```

**Validation:**
```bash
# Unit tests
python -m pytest tests/test_dependency_detector.py -v

# Integration test with real features
python test_dependency_detection.py --features-db features.db
```

---

#### Task 1.3: Skip Impact Analysis (2 days)
**Owner:** Backend
**Dependencies:** Task 1.2

**Deliverables:**
- `skip_analyzer.py` - Analyzes impact when feature is skipped
- Find all downstream dependent features
- Calculate cascade depth
- Generate impact report with recommendations

**Implementation:**
```python
# skip_analyzer.py
class SkipImpactAnalyzer:
    def analyze_skip_impact(self, feature_id: int) -> Dict:
        """Analyze impact of skipping a feature."""

        # Find all features that depend on this one
        dependents = self.db.get_dependent_features(feature_id)

        # Build dependency tree
        dep_tree = self._build_dependency_tree(feature_id, depth=3)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            feature_id, dependents, dep_tree
        )

        return {
            'feature_id': feature_id,
            'immediate_dependents': len(dependents),
            'total_impact': self._count_all_descendants(dep_tree),
            'dependency_tree': dep_tree,
            'recommendations': recommendations,
            'suggested_action': self._suggest_action(dependents)
        }

    def _suggest_action(self, dependents: List[Dict]) -> str:
        """Suggest best action when skipping."""
        if not dependents:
            return "SAFE_TO_SKIP"
        elif len(dependents) >= 5:
            return "CASCADE_SKIP"  # Skip all dependents too
        else:
            return "IMPLEMENT_WITH_MOCKS"  # Use placeholders
```

**Output Format:**
```
⚠️  SKIP IMPACT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Skipping Feature #5: "OAuth authentication"

Downstream impact (3 features depend on this):
  • Feature #12: User profile OAuth avatar (confidence: 0.85)
  • Feature #23: Third-party account linking (confidence: 0.92)
  • Feature #31: Social media sharing (confidence: 0.78)

Cascade depth: 2 levels
  Feature #12 → Feature #45 (avatar in email notifications)

Recommendation: IMPLEMENT_WITH_MOCKS
  ⚠️  Implement dependent features with documented assumptions
  ⚠️  Mark them for review when #5 is implemented
  ✓  Alternative: Skip and cascade all dependent features

Actions:
  [1] Skip all dependent features (cascade)
  [2] Implement dependents with mocks/placeholders
  [3] Cancel skip (implement this feature now)
```

**Validation:**
```bash
python test_skip_analyzer.py --feature-id 5
```

---

#### Task 1.4: Blocker Classification System (2 days)
**Owner:** Agent Prompt Engineering
**Dependencies:** Task 1.1

**Deliverables:**
- Blocker type taxonomy
- Agent prompts for classification
- Database models for blockers
- CLI interface for blocker detection

**Blocker Types:**
| Type | Requires Human | Auto-Action | Example |
|------|----------------|-------------|---------|
| ENV_CONFIG | Yes | Pause & ask | Missing `OAUTH_CLIENT_ID` |
| EXTERNAL_SERVICE | Yes | Pause & ask | Need Stripe account |
| TECH_PREREQUISITE | Maybe | Analyze deps | API endpoint not built |
| UNCLEAR_REQUIREMENTS | Yes | Pause & ask | Ambiguous spec |
| LEGITIMATE_DEFERRAL | No | Skip silently | Polish animations |

**Agent Prompt:**
```markdown
You're about to skip a feature. Classify the reason:

Feature: {feature_name}

Blocker Type Options:
1. ENV_CONFIG - Missing environment variable, API key, or configuration
   Example: Need STRIPE_API_KEY in .env file

2. EXTERNAL_SERVICE - Third-party service not set up yet
   Example: Need to create Stripe account first

3. TECH_PREREQUISITE - Depends on another feature not yet built
   Example: Need API endpoint before building frontend

4. UNCLEAR_REQUIREMENTS - Specification is ambiguous
   Example: "What should the error message say?"

5. LEGITIMATE_DEFERRAL - Can safely defer without issues
   Example: Polish animations, nice-to-have features

Based on your reason for skipping, select the blocker type (1-5):
```

**Implementation:**
```python
# blocker_classifier.py
from enum import Enum

class BlockerType(Enum):
    ENV_CONFIG = "environment_config"
    EXTERNAL_SERVICE = "external_service"
    TECH_PREREQUISITE = "technical_prerequisite"
    UNCLEAR_REQUIREMENTS = "unclear_requirements"
    LEGITIMATE_DEFERRAL = "legitimate_deferral"

class BlockerClassifier:
    def classify(self, feature: Dict, skip_reason: str) -> BlockerType:
        """Classify blocker type based on skip reason."""
        # Agent-driven classification via prompt
        result = self.agent.classify_blocker(feature, skip_reason)
        return BlockerType(result)

    def requires_human_intervention(self, blocker_type: BlockerType) -> bool:
        """Check if blocker type requires human input."""
        return blocker_type in [
            BlockerType.ENV_CONFIG,
            BlockerType.EXTERNAL_SERVICE,
            BlockerType.UNCLEAR_REQUIREMENTS
        ]
```

---

### Week 2: Human-in-the-Loop & Unblock Workflow (Tasks 1.5 - 1.8)

#### Task 1.5: Human Intervention Workflow (3 days)
**Owner:** Full-stack
**Dependencies:** Task 1.4

**Deliverables:**
- Pause agent when blocker requires human input
- Interactive CLI prompt for user action
- Auto-generation of `BLOCKERS.md` checklist
- Three action paths: Provide Now, Defer, Mock

**User Experience:**
```
🛑 HUMAN INPUT REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature #5: "OAuth authentication"
Blocker Type: Environment Configuration

Required information:
  • OAUTH_CLIENT_ID (from Google Cloud Console)
  • OAUTH_CLIENT_SECRET (from Google Cloud Console)
  • OAUTH_PROVIDER (google/github/facebook)

Actions:
  [1] Provide values now (continue immediately)
  [2] Defer (I'll add to .env later)
  [3] Mock (use fake values for now)

Select action (1-3): _
```

**Implementation Flow:**
```python
# human_intervention.py
class HumanInterventionHandler:
    def handle_blocker(self, feature: Dict, blocker: Dict) -> str:
        """Handle blocker requiring human input."""

        # Display blocker info
        self.display_blocker_prompt(feature, blocker)

        # Get user choice
        choice = self.prompt_user_action()

        if choice == 1:  # Provide now
            values = self.collect_values(blocker['required_values'])
            self.write_to_env(values)
            return "RESUME_IMMEDIATELY"

        elif choice == 2:  # Defer
            self.add_to_blockers_md(feature, blocker)
            return "SKIP_AND_DEFER"

        elif choice == 3:  # Mock
            self.implement_with_mocks(feature, blocker)
            return "IMPLEMENT_WITH_MOCKS"
```

**Action 1: Provide Now**
- CLI prompts for each required value
- Masked input for secrets (password-style)
- Validates format (URL, API key format, etc.)
- Writes to `.env` file automatically
- Agent resumes immediately

**Action 2: Defer**
- Adds to `BLOCKERS.md` with checkbox
- Skips feature (priority = max + 1)
- Agent continues with other work
- User can unblock later with command

**Action 3: Mock**
- Agent implements with fake/placeholder values
- Adds `// TODO: Replace with real values` comments
- Marks feature as "passing_with_mocks"
- Tracked for production readiness review

---

#### Task 1.6: BLOCKERS.md Auto-Generation (1 day)
**Owner:** Backend
**Dependencies:** Task 1.5

**Deliverables:**
- Auto-generated blockers checklist
- Categorized by blocker type
- Instructions for unblocking
- Dynamic updates when blockers resolved

**Format:**
```markdown
# Blockers Requiring Human Input

Last updated: 2026-01-21 14:35:22
Total blockers: 3

## Environment Variables Needed

- [ ] **Feature #5: OAuth authentication**
  - `OAUTH_CLIENT_ID` - Get from Google Cloud Console
  - `OAUTH_CLIENT_SECRET` - Get from Google Cloud Console
  - `OAUTH_PROVIDER` - Choose: google|github|facebook
  - **To unblock:** Add to `.env`, then run `python start.py --unblock 5`

## External Services to Configure

- [ ] **Feature #18: Email notifications**
  - Sign up for SendGrid account at https://sendgrid.com
  - Create API key in Settings > API Keys
  - Add to `.env` as `SENDGRID_API_KEY`
  - **To unblock:** Run `python start.py --unblock 18`

## Requirements Clarifications Needed

- [ ] **Feature #25: User roles system**
  - Q: What roles do we need? (admin/user/guest?)
  - Q: Can users have multiple roles?
  - Q: Who can assign roles?
  - **To unblock:** Update feature description, run `python start.py --unblock 25`

---

**Quick Commands:**
```bash
# Unblock specific feature
python start.py --unblock 5

# Unblock all (agent will retry all blocked features)
python start.py --unblock-all

# View blocker details
python start.py --show-blockers
```
```

**Implementation:**
```python
# blockers_md_generator.py
class BlockersMdGenerator:
    def generate(self, blockers: List[Dict]) -> str:
        """Generate BLOCKERS.md content."""
        template = self._load_template()

        # Group by blocker type
        grouped = self._group_by_type(blockers)

        # Render sections
        sections = []
        for blocker_type, items in grouped.items():
            sections.append(self._render_section(blocker_type, items))

        return template.format(
            last_updated=datetime.now(),
            total_blockers=len(blockers),
            sections="\n\n".join(sections)
        )

    def update(self, project_dir: Path):
        """Update BLOCKERS.md file."""
        blockers = self.db.get_active_blockers()
        content = self.generate(blockers)

        blockers_file = project_dir / "BLOCKERS.md"
        blockers_file.write_text(content)
```

---

#### Task 1.7: Unblock Command Implementation (2 days)
**Owner:** CLI
**Dependencies:** Task 1.6

**Deliverables:**
- `--unblock <feature_id>` CLI command
- `--unblock-all` for batch unblocking
- `--show-blockers` to list active blockers
- Agent automatically retries unblocked features

**CLI Commands:**
```bash
# Unblock specific feature
python start.py --unblock 5

# Output:
✓ Feature #5 marked as unblocked
✓ Removed from BLOCKERS.md
→ Agent will retry this feature in next session

# Unblock all
python start.py --unblock-all

# Output:
✓ Unblocked 3 features: #5, #18, #25
→ Agent will retry all in next session

# Show active blockers
python start.py --show-blockers

# Output:
Active Blockers (3):

#5  OAuth authentication [ENV_CONFIG]
    Missing: OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET

#18 Email notifications [EXTERNAL_SERVICE]
    Need: SendGrid account and API key

#25 User roles system [UNCLEAR_REQUIREMENTS]
    Need: Role types clarification
```

**Implementation:**
```python
# cli_commands.py
def cmd_unblock(feature_id: int = None, all: bool = False):
    """Unblock one or all blocked features."""

    if all:
        # Unblock all features
        blocked = db.get_blocked_features()
        for feature in blocked:
            db.mark_unblocked(feature['id'])
            db.reset_priority(feature['id'])  # Move back to original priority

        # Update BLOCKERS.md
        blockers_md_generator.update(project_dir)

        print(f"✓ Unblocked {len(blocked)} features")

    elif feature_id:
        # Unblock specific feature
        db.mark_unblocked(feature_id)
        db.reset_priority(feature_id)

        # Update BLOCKERS.md
        blockers_md_generator.update(project_dir)

        print(f"✓ Feature #{feature_id} marked as unblocked")

    print("→ Agent will retry unblocked features in next session")

def cmd_show_blockers():
    """Show all active blockers."""
    blockers = db.get_active_blockers()

    if not blockers:
        print("No active blockers! ✨")
        return

    print(f"\nActive Blockers ({len(blockers)}):\n")

    for blocker in blockers:
        print(f"#{blocker['feature_id']}  {blocker['feature_name']} [{blocker['type']}]")
        print(f"    {blocker['description']}")
        print()
```

---

#### Task 1.8: Implementation Assumptions Tracking (1 day)
**Owner:** Backend + Agent Prompts
**Dependencies:** Task 1.3

**Deliverables:**
- Agent documents assumptions in code when building on skipped features
- Store assumptions in database
- Review assumptions when skipped feature implemented
- CLI command to show assumptions for feature

**Agent Behavior:**
When implementing Feature B that depends on skipped Feature A:

1. Agent detects dependency
2. Agent documents assumption in code comment
3. Agent stores assumption in database
4. When Feature A later implemented, agent reviews assumptions

**Code Comment Format:**
```javascript
// ASSUMPTION: Feature #5 (OAuth) will use Google OAuth
// If different provider chosen, update avatar URL parsing
// See: features.db assumption #123
async function getOAuthAvatar(userId) {
  // Placeholder implementation until OAuth (#5) is done
  return '/default-avatar.png';
}
```

**Database Storage:**
```python
# Store assumption
db.create_assumption(
    feature_id=12,  # Current feature (avatar)
    depends_on_feature_id=5,  # Skipped feature (OAuth)
    assumption_text="OAuth will use Google OAuth provider",
    code_location="src/api/users.js:145-152",
    impact="If different provider, must update avatar URL parsing"
)
```

**Review Workflow:**
When Feature #5 (OAuth) is finally implemented:
```
✓ Feature #5 "OAuth authentication" marked as passing

⚠️  ASSUMPTION REVIEW REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3 features made assumptions about this implementation:

Feature #12: User profile OAuth avatar
  Assumption: "OAuth will use Google OAuth provider"
  Location: src/api/users.js:145-152
  Status: ✅ VALID (Google was chosen)

Feature #23: Third-party account linking
  Assumption: "OAuth tokens stored in JWT"
  Location: src/api/auth.js:67-82
  Status: ⚠️ INVALID (We use httpOnly cookies, not JWT)
  Action: Mark Feature #23 for review

Feature #31: Social media sharing
  Assumption: "OAuth includes social media scopes"
  Location: src/api/sharing.js:34-41
  Status: ⚠️ NEEDS_VERIFICATION

Recommendations:
  → Review Feature #23 (invalid assumption detected)
  → Verify Feature #31 (manual check needed)
```

---

### Validation & Testing (Week 2, Day 5)

#### Integration Tests
```bash
# Test full skip workflow
python -m pytest tests/integration/test_skip_workflow.py

# Test cases:
# 1. Skip feature with dependencies → impact analysis shown
# 2. Skip with ENV_CONFIG blocker → human prompt triggered
# 3. User chooses "Provide Now" → env vars collected, agent resumes
# 4. User chooses "Defer" → BLOCKERS.md updated
# 5. User chooses "Mock" → feature implemented with placeholders
# 6. Unblock feature → agent retries next session
# 7. Implement skipped feature → assumption review triggered
```

#### Success Criteria
- ✅ Dependency detection accuracy >80% on test suite
- ✅ Skip impact analysis correctly identifies all downstream features
- ✅ Human intervention workflow completes without errors
- ✅ BLOCKERS.md auto-generates correctly
- ✅ Unblock commands work as expected
- ✅ Assumptions tracked and reviewed correctly

---

## PHASE 2: Benchmarking & Performance Metrics

**Timeline:** 1 week
**Priority:** 🔴 CRITICAL
**Effort:** Medium
**User Need:** "Evaluate how we did versus other coding systems"

### Goals

- Track key performance metrics throughout development
- Generate comprehensive performance reports
- Compare autocoder vs alternatives (manual coding, Claude skill, Cursor)
- Prove ROI and validate system value
- Identify bottlenecks for continuous improvement

### Week 3: Metrics & Reporting (Tasks 2.1 - 2.4)

#### Task 2.1: Metrics Collection System (2 days)
**Owner:** Backend
**Dependencies:** None

**Deliverables:**
- Metrics database schema
- Real-time metrics collection during agent execution
- Metrics storage in `benchmarks/` directory

**Metrics to Track:**

| Metric | Description | Target | Collection Point |
|--------|-------------|--------|------------------|
| Time to MVP | Hours from spec to working prototype | <24h | Start to all features passing |
| Feature completion rate | % features passing on first try | >60% | Per feature |
| Rework ratio | Features needing fixes / total | <20% | Per session |
| Skip rate | % features skipped at least once | <30% | Per session |
| Human interventions | # times user input required | <10 | Per blocker |
| Code quality score | Static analysis + linting | >85/100 | Post-development |
| Cost (API) | Total Claude API cost | <$50 for MVP | Per API call |
| LOC generated | Total lines of code | N/A | Post-development |
| Test coverage | % code covered by tests | >80% | Post-development |
| Velocity | Features per hour | N/A | Per session |

**Database Schema:**
```sql
CREATE TABLE metrics_runs (
    id INTEGER PRIMARY KEY,
    project_name TEXT NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_features INTEGER,
    features_completed INTEGER,
    run_status TEXT,  -- 'in_progress', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE metrics_sessions (
    id INTEGER PRIMARY KEY,
    run_id INTEGER REFERENCES metrics_runs(id),
    session_number INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    features_completed INTEGER,
    features_skipped INTEGER,
    api_calls INTEGER,
    api_cost REAL,
    created_at TIMESTAMP
);

CREATE TABLE metrics_features (
    id INTEGER PRIMARY KEY,
    run_id INTEGER REFERENCES metrics_runs(id),
    feature_id INTEGER,
    feature_name TEXT,
    first_try_pass BOOLEAN,
    attempts_needed INTEGER,
    was_skipped BOOLEAN,
    time_to_complete_seconds INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE metrics_interventions (
    id INTEGER PRIMARY KEY,
    run_id INTEGER REFERENCES metrics_runs(id),
    intervention_type TEXT,  -- 'blocker', 'clarification', 'error'
    description TEXT,
    resolution_time_seconds INTEGER,
    created_at TIMESTAMP
);
```

**Implementation:**
```python
# metrics_collector.py
class MetricsCollector:
    def __init__(self, project_name: str):
        self.run = self._create_run(project_name)
        self.session_start = None

    def start_session(self, session_number: int):
        """Start tracking a new session."""
        self.session_start = datetime.now()
        self.current_session = {
            'run_id': self.run.id,
            'session_number': session_number,
            'start_time': self.session_start,
            'api_calls': 0,
            'api_cost': 0.0
        }

    def track_feature_complete(self, feature: Dict, first_try: bool, attempts: int):
        """Track feature completion."""
        db.insert('metrics_features', {
            'run_id': self.run.id,
            'feature_id': feature['id'],
            'feature_name': feature['name'],
            'first_try_pass': first_try,
            'attempts_needed': attempts,
            'was_skipped': feature.get('was_skipped', False),
            'time_to_complete_seconds': self._calculate_time(feature)
        })

    def track_api_call(self, cost: float):
        """Track API call and cost."""
        self.current_session['api_calls'] += 1
        self.current_session['api_cost'] += cost

    def track_intervention(self, intervention_type: str, description: str):
        """Track human intervention."""
        intervention_start = datetime.now()
        # ... wait for resolution ...
        resolution_time = (datetime.now() - intervention_start).total_seconds()

        db.insert('metrics_interventions', {
            'run_id': self.run.id,
            'intervention_type': intervention_type,
            'description': description,
            'resolution_time_seconds': resolution_time
        })
```

---

#### Task 2.2: Real-Time Performance Dashboard (2 days)
**Owner:** CLI/UI
**Dependencies:** Task 2.1

**Deliverables:**
- Real-time CLI dashboard during agent execution
- Live metrics display (velocity, cost, quality)
- ETA calculation based on current velocity

**Dashboard Display:**
```
┌─────────────────────────────────────────────┐
│     AUTOCODER PERFORMANCE                   │
├─────────────────────────────────────────────┤
│ Runtime:              3h 24m                │
│ Features completed:   45/257 (18%)          │
│ Velocity:             13.2 features/hour    │
│ Estimated completion: 16h remaining         │
│                                             │
│ Efficiency:                                 │
│   Pass on first try:  28/45 (62%) ✓        │
│   Needed fixes:       17/45 (38%)           │
│   Skipped features:   12/257 (5%) ✓        │
│                                             │
│ Cost tracking:                              │
│   API calls:          1,247                 │
│   Estimated cost:     $18.50                │
│   Cost per feature:   $0.41                 │
│                                             │
│ Quality metrics:                            │
│   Code quality:       86/100 ✓             │
│   Test coverage:      79% (target: 80%)     │
│   Accessibility:      WCAG AA ✓             │
│                                             │
└─────────────────────────────────────────────┘
```

**Implementation:**
```python
# performance_dashboard.py
from rich.console import Console
from rich.table import Table
from rich.live import Live

class PerformanceDashboard:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.console = Console()

    def render(self) -> Table:
        """Render dashboard as rich table."""
        table = Table(title="AUTOCODER PERFORMANCE", show_header=False)

        # Runtime stats
        runtime = self._format_duration(self.metrics.get_runtime())
        completed = self.metrics.get_features_completed()
        total = self.metrics.get_total_features()
        pct = (completed / total * 100) if total > 0 else 0

        table.add_row("Runtime:", runtime)
        table.add_row("Features completed:", f"{completed}/{total} ({pct:.0f}%)")

        # Velocity
        velocity = self.metrics.get_velocity()
        eta = self._calculate_eta(completed, total, velocity)
        table.add_row("Velocity:", f"{velocity:.1f} features/hour")
        table.add_row("Estimated completion:", eta)

        # ... more rows ...

        return table

    def start_live_display(self):
        """Start live updating dashboard."""
        with Live(self.render(), refresh_per_second=1) as live:
            while not self.metrics.is_complete():
                live.update(self.render())
                time.sleep(1)
```

---

#### Task 2.3: Comprehensive Performance Report Generator (2 days)
**Owner:** Reporting
**Dependencies:** Task 2.1

**Deliverables:**
- Post-completion performance report
- Comparison to baseline estimates (manual coding, alternatives)
- ROI calculation
- Bottleneck identification
- Recommendations for improvement

**Report Template:** (See Appendix C in PRD for full example)

**Key Sections:**
1. Summary (completion rate, time, cost, quality)
2. Comparison to Alternatives (manual, Claude skill, Cursor)
3. ROI Analysis (savings calculation)
4. Detailed Metrics (velocity, quality, interventions)
5. Bottlenecks Identified (slowest sessions, common issues)
6. Recommendations (for future runs)
7. Is Autocoder Worth It? (decision framework)

**Implementation:**
```python
# report_generator.py
class PerformanceReportGenerator:
    def generate(self, run_id: int) -> str:
        """Generate comprehensive performance report."""

        # Collect all metrics
        run = db.get_run(run_id)
        sessions = db.get_sessions(run_id)
        features = db.get_features(run_id)
        interventions = db.get_interventions(run_id)

        # Calculate key metrics
        metrics = self._calculate_metrics(run, sessions, features, interventions)

        # Generate comparison data
        comparison = self._generate_comparison(metrics)

        # Calculate ROI
        roi = self._calculate_roi(metrics, comparison)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(sessions, features)

        # Generate recommendations
        recommendations = self._generate_recommendations(bottlenecks, metrics)

        # Render report
        return self._render_report(metrics, comparison, roi, bottlenecks, recommendations)
```

---

#### Task 2.4: A/B Testing Framework (Optional, 1 day)
**Owner:** Testing
**Dependencies:** Task 2.1-2.3

**Deliverables:**
- Support for benchmark mode flag
- Parallel run comparison
- Side-by-side comparison report

**Usage:**
```bash
# Run autocoder in benchmark mode
python start.py --benchmark-mode autocoder --project test-app

# Run Claude skill for comparison
claude /code --project test-app --benchmark-mode skill

# Generate comparison
python benchmark_compare.py autocoder vs skill
```

---

### Validation & Testing (Week 3, Day 5)

#### Success Criteria
- ✅ All metrics collected accurately during runs
- ✅ Real-time dashboard updates correctly
- ✅ Performance report generates successfully
- ✅ ROI calculation matches manual verification
- ✅ Comparison data provides actionable insights

---

## PHASE 3: Checkpoint System (Quality Gates)

**Timeline:** 2 weeks
**Priority:** 🟡 HIGH
**Effort:** High
**User Need:** Catch bugs and issues during development

### Goals

- Run quality checks at regular intervals
- Pause development on critical issues
- Auto-create fix features for detected problems
- Support multiple checkpoint types (code review, security, performance)

### Week 4: Checkpoint Infrastructure (Tasks 3.1 - 3.3)

#### Task 3.1: Checkpoint Configuration System (2 days)
**Owner:** Backend
**Dependencies:** None

**Deliverables:**
- `autocoder_config.yaml` support
- Checkpoint frequency settings
- Enable/disable checkpoint types
- Manual checkpoint trigger

**Configuration Format:**
```yaml
# autocoder_config.yaml
checkpoints:
  enabled: true
  frequency: 10  # Every 10 features
  types:
    code_review: true
    security_audit: true
    performance_check: true
    accessibility_check: false
  auto_pause_on_critical: true

  # Custom checkpoint triggers
  triggers:
    - feature_count: 10
    - feature_count: 20
    - feature_count: 50
    - milestone: "authentication"  # Before specific features
    - milestone: "payments"
```

---

#### Task 3.2: Checkpoint Orchestration Engine (2 days)
**Owner:** Backend
**Dependencies:** Task 3.1

**Deliverables:**
- Checkpoint trigger detection
- Parallel execution of checkpoint agents
- Result aggregation
- Decision logic (PAUSE, CONTINUE, CONTINUE_WITH_WARNINGS)

**Implementation:**
```python
# checkpoint_orchestrator.py
class CheckpointOrchestrator:
    def should_run_checkpoint(self, features_completed: int) -> bool:
        """Check if checkpoint should run."""
        frequency = config.get('checkpoints.frequency', 10)
        return features_completed % frequency == 0

    async def run_checkpoint(self, project_dir: Path, features_completed: int):
        """Run all enabled checkpoint agents in parallel."""

        print(f"\n🚧 CHECKPOINT: {features_completed} features complete\n")

        # Determine which checkpoints to run
        enabled_checkpoints = self._get_enabled_checkpoints()

        # Run all checkpoints in parallel
        results = await asyncio.gather(*[
            self._run_checkpoint_agent(checkpoint_type, project_dir)
            for checkpoint_type in enabled_checkpoints
        ])

        # Aggregate results
        aggregated = self._aggregate_results(results)

        # Make decision
        decision = self._make_decision(aggregated)

        # Save checkpoint report
        self._save_report(features_completed, aggregated, decision)

        return decision

    def _make_decision(self, aggregated: Dict) -> str:
        """Decide whether to pause, continue, or warn."""

        if aggregated['critical_count'] > 0:
            print("❌ CRITICAL ISSUES - Pausing development")
            return "PAUSE"

        elif aggregated['warning_count'] > 0:
            print(f"⚠️  {aggregated['warning_count']} warnings - Continuing")
            return "CONTINUE_WITH_WARNINGS"

        else:
            print("✅ All checks passed")
            return "CONTINUE"
```

---

#### Task 3.3: Checkpoint Report Storage (1 day)
**Owner:** Backend
**Dependencies:** Task 3.2

**Deliverables:**
- Save checkpoint reports to `checkpoints/` directory
- Markdown format for human readability
- Database storage for querying

**Report Format:**
```
checkpoints/
├── checkpoint_01_10_features.md
├── checkpoint_02_20_features.md
└── checkpoint_03_30_features.md
```

---

### Week 5: Checkpoint Agents (Tasks 3.4 - 3.7)

#### Task 3.4: Code Review Checkpoint Agent (2 days)
**Owner:** Agent Development
**Dependencies:** Task 3.2

**Deliverables:**
- Agent that analyzes recently changed files
- Detects code smells, anti-patterns
- Validates naming conventions
- Suggests refactoring opportunities

**Agent Capabilities:**
- Read recent git diffs
- Analyze code structure
- Check for duplication
- Validate patterns

**Output Format:**
```markdown
## Code Review

**Status:** ⚠️ PASS WITH WARNINGS

### Warnings
1. **Duplicated Logic** (Medium)
   - Location: `src/api/users.js`, `src/api/projects.js`
   - Issue: Pagination logic duplicated
   - Suggestion: Extract to `src/utils/pagination.js`

### Info
- Code style consistent
- TypeScript types properly defined
```

---

#### Task 3.5: Security Audit Checkpoint Agent (2 days)
**Owner:** Security + Agent Development
**Dependencies:** Task 3.2

**Deliverables:**
- Scans for OWASP Top 10 vulnerabilities
- Checks authentication/authorization logic
- Validates input sanitization
- Reviews API endpoint security

**Detection Rules:**
- JWT in localStorage → Critical
- No rate limiting on auth → Critical
- SQL injection vulnerabilities → Critical
- XSS vulnerabilities → Critical
- Missing CSRF protection → Warning

---

#### Task 3.6: Performance Checkpoint Agent (2 days)
**Owner:** Performance + Agent Development
**Dependencies:** Task 3.2

**Deliverables:**
- Analyzes bundle sizes
- Reviews database query efficiency
- Checks for N+1 queries
- Identifies heavy dependencies

**Checks:**
- Bundle size > 300KB → Warning
- Heavy dependency detected (moment.js) → Info
- N+1 query patterns → Warning

---

#### Task 3.7: Auto-Fix Feature Creation (1 day)
**Owner:** Backend
**Dependencies:** Task 3.4-3.6

**Deliverables:**
- When critical issue found, auto-create fix feature
- Insert at high priority in queue
- Agent implements fix before continuing

**Flow:**
```
Checkpoint finds critical issue
  → Create fix feature in database
  → Set priority = current_priority - 0.5 (insert before next)
  → Mark as "checkpoint_fix"
  → Agent implements in next iteration
  → Re-run checkpoint after fix
  → Continue if resolved
```

---

### Validation & Testing (Week 5, Day 5)

#### Success Criteria
- ✅ Checkpoints run at correct frequency
- ✅ All checkpoint types execute successfully
- ✅ Critical issues correctly pause development
- ✅ Fix features auto-created and implemented
- ✅ Checkpoint reports saved correctly

---

## PHASE 4: Persona-Based Design Iteration

**Timeline:** 3 weeks
**Priority:** 🟢 MEDIUM
**Effort:** High
**User Need:** Pre-development design validation

### Goals

- Create persona system with diverse perspectives
- Run multi-round design iteration before coding
- Aggregate feedback from personas
- Converge on polished design spec

### Week 6: Persona Foundation (Tasks 4.1 - 4.2)

#### Task 4.1: Persona Definition System (2 days)

**Deliverables:**
- JSON-based persona definitions
- 7 built-in personas (see PRD Appendix A)
- Persona loader and validator

**Persona Schema:**
```json
{
  "id": "accessibility_advocate",
  "name": "Sarah Chen",
  "age": 34,
  "background": "Blind user, accessibility consultant",
  "expertise": ["WCAG 2.1", "ARIA", "Screen readers"],
  "bias": "Prioritizes accessibility over aesthetics",
  "personality": "Direct, thorough, passionate",
  "typical_concerns": ["Color contrast", "Keyboard nav", ...],
  "evaluation_rubric": {
    "keyboard_navigation": {"weight": 0.3, "criteria": "..."},
    "screen_reader": {"weight": 0.3, "criteria": "..."}
  }
}
```

**Built-in Personas:**
1. Sarah Chen - Accessibility Advocate
2. Marcus Rodriguez - Power User
3. Elena Martinez - Novice User
4. David Kim - Mobile-First User
5. Aisha Patel - Brand/Aesthetics
6. Raj Sharma - Security Conscious
7. Lisa Johnson - Performance Optimizer

---

#### Task 4.2: Design Iteration Agent (3 days)

**Deliverables:**
- Agent that takes rough spec and creates detailed design
- Outputs mockup descriptions
- Creates user flow diagrams
- Defines component hierarchy

---

### Week 7-8: Review & Synthesis (Tasks 4.3 - 4.6)

#### Task 4.3: Persona Review Panel (3 days)
Each persona reviews current design iteration and provides feedback.

#### Task 4.4: Design Synthesis Agent (3 days)
Aggregates feedback, resolves conflicts, creates next iteration.

#### Task 4.5: Convergence Detection (2 days)
Detects when feedback becomes minimal and design is ready.

#### Task 4.6: Design Review CLI (2 days)
```bash
python design_review.py --spec initial_spec.md
```

---

## PHASE 5: Playwright + Visual UX Evaluation

**Timeline:** 3 weeks
**Priority:** 🟢 LOW
**Effort:** High
**User Need:** Post-development UX validation

### Goals

- Generate Playwright tests for key user flows
- Capture screenshots at each step
- Analyze screenshots with AI for UX issues
- Generate comprehensive UX report with persona feedback

### Week 9: Playwright Infrastructure (Tasks 5.1 - 5.2)

#### Task 5.1: Playwright Test Generation (3 days)
Agent generates tests for onboarding, dashboard, settings, etc.

#### Task 5.2: Automated Test Execution (2 days)
Runs tests, captures screenshots, organizes by flow.

---

### Week 10: Visual Analysis (Tasks 5.3 - 5.4)

#### Task 5.3: Visual QA Agent (3 days)
Analyzes screenshots for visual bugs (alignment, spacing, etc.).

#### Task 5.4: Screenshot-Based UX Evaluation (2 days)
Multiple specialist agents score UX criteria.

---

### Week 11: Persona Testing & Reporting (Tasks 5.5 - 5.6)

#### Task 5.5: Persona User Testing (2 days)
Each persona "uses" the app via screenshots, provides feedback.

#### Task 5.6: UX Report Generator (3 days)
Comprehensive report with scores, issues, recommendations.

---

## PHASE 6: Integration & Polish

**Timeline:** 1 week
**Priority:** 🟢 MEDIUM
**Effort:** Medium

### Goals

- Seamless end-to-end workflow
- Configuration and customization
- Documentation and examples
- Sample project showcase

### Week 12: Final Integration (Tasks 6.1 - 6.4)

#### Task 6.1: End-to-End Workflow Integration (2 days)
Connect all phases: skip management → checkpoints → design → UX.

#### Task 6.2: Configuration UI (1 day)
CLI/UI for enabling/disabling features, setting thresholds.

#### Task 6.3: Documentation (2 days)
User guides, API docs, examples, troubleshooting.

#### Task 6.4: Sample Project (1 day)
Showcase project demonstrating full workflow.

---

## Implementation Timeline Overview

```
Month 1: Foundation & Core Value
├── Week 1-2: Phase 1 - Skip Management & Dependencies ✅ CRITICAL
├── Week 3:   Phase 2 - Benchmarking & Metrics ✅ CRITICAL
└── Week 4-5: Phase 3 - Checkpoint System ⚠️ HIGH

Month 2: Design & UX
├── Week 6-8:  Phase 4 - Persona Design Iteration ℹ️ MEDIUM
└── Week 9-11: Phase 5 - Playwright + Visual UX ℹ️ LOW

Month 3: Polish
└── Week 12: Phase 6 - Integration & Documentation ℹ️ MEDIUM
```

---

## Critical Path Analysis

**Must-Have for MVP:**
1. Phase 1 (Skip Management) - Prevents rework ✅
2. Phase 2 (Benchmarking) - Validates value ✅
3. Phase 3 (Checkpoints) - Ensures quality ⚠️

**Nice-to-Have:**
4. Phase 4 (Design Iteration) - Improves specs
5. Phase 5 (Visual UX) - Post-dev validation

**Recommended Minimum:** Phases 1-3 (8 weeks)
**Full System:** All phases (12 weeks)

---

## Resource Requirements

### Team Composition
- 1 Backend Developer (Python, SQLAlchemy)
- 1 Agent/Prompt Engineer (Claude Agent SDK)
- 1 Full-stack Developer (CLI, UI integration)
- 1 QA Engineer (Testing, validation)

### Infrastructure
- Claude API access (Sonnet 4.5)
- Git repository
- CI/CD pipeline (optional)
- Test environment

### Budget Estimate
- Development: 12 weeks × 4 engineers
- API costs (development): ~$500
- API costs (per production run): $40-100

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Dependency detection accuracy low | Medium | High | Manual override available, iterative improvement |
| Human intervention delays | High | Low | Auto-defer after timeout, async workflow |
| Checkpoint false positives | Medium | Medium | User can override warnings, tune over time |
| Benchmarking comparison unfair | Medium | High | Standardized test projects, multiple runs |
| Phase overruns | High | Medium | Phase 1-2 prioritized, rest can slip |

---

## Success Metrics

### Phase 1 (Skip Management)
- Dependency detection accuracy >80%
- <5% rework rate due to skipped features
- <2 min avg human intervention resolution time

### Phase 2 (Benchmarking)
- ROI >100x vs manual coding
- <$50 API cost for typical MVP
- Performance reports generated successfully

### Phase 3 (Checkpoints)
- >5 critical issues caught before production
- <10% false positive rate
- Auto-fix features succeed >90%

### Phase 4 (Design Iteration)
- Design converges in <4 iterations
- >80% persona satisfaction in final iteration

### Phase 5 (Visual UX)
- >8.0/10 average UX score
- >5 actionable issues identified
- WCAG AA compliance

---

## Next Steps

1. **Review & Approve** this implementation plan
2. **Prioritize Phases** - Confirm Phases 1-2 as critical path
3. **Resource Allocation** - Assign team members
4. **Kickoff Phase 1** - Start Week 1 tasks
5. **Weekly Standups** - Track progress, adjust as needed

---

## Appendices

### Appendix A: Task Dependencies Graph
```
Phase 1 (Skip Management)
├── 1.1 Database Schema → 1.2, 1.4
├── 1.2 Dependency Detection → 1.3
├── 1.3 Skip Analysis → 1.8
├── 1.4 Blocker Classification → 1.5
├── 1.5 Human Intervention → 1.6
├── 1.6 BLOCKERS.md Generation → 1.7
├── 1.7 Unblock Commands
└── 1.8 Assumptions Tracking

Phase 2 (Benchmarking)
├── 2.1 Metrics Collection → 2.2, 2.3
├── 2.2 Dashboard → 2.3
├── 2.3 Report Generator → 2.4
└── 2.4 A/B Testing

Phase 3 (Checkpoints)
├── 3.1 Configuration → 3.2
├── 3.2 Orchestration → 3.3, 3.4-3.7
├── 3.3 Report Storage
├── 3.4 Code Review Agent → 3.7
├── 3.5 Security Agent → 3.7
├── 3.6 Performance Agent → 3.7
└── 3.7 Auto-Fix Creation
```

### Appendix B: Configuration Examples
See `autocoder_config.yaml` examples in PRD.

### Appendix C: Testing Strategy
- Unit tests for each component
- Integration tests for workflows
- End-to-end tests for full cycles
- Performance benchmarks

---

**Document Status:** ✅ Ready for Review
**Prepared By:** Implementation Planning Team
**Date:** 2026-01-21
**Next Review:** After Phase 1 completion
