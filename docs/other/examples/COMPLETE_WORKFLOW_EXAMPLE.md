# Complete Workflow Example

This example demonstrates running the complete autocoder workflow from design iteration to UX evaluation.

---

## Scenario

You want to build a **Task Management Dashboard** with:
- Kanban board view
- User authentication
- Task filtering and search
- Mobile-responsive design
- WCAG AA accessibility

---

## Step 1: Create Project

```bash
# Create project directory
mkdir task-dashboard
cd task-dashboard

# Initialize project
python /path/to/autocoder-2/start.py
# Select: [1] Create new project
# Name: task-dashboard
```

---

## Step 2: Configure Workflow

```bash
# Run configuration wizard
python -m integration.config_ui --setup --project-dir .
```

Answer the questions:

```
🚀 Autocoder Configuration Wizard
==================================================

📋 Phase Toggles:
  Enable design iteration? [Y/n]: Y
  Enable checkpoints? [Y/n]: Y
  Enable UX evaluation? [Y/n]: Y
  Enable metrics tracking? [Y/n]: Y

⚙️  Thresholds:
  Checkpoint frequency (features) [10]: 10
  Max design iterations [4]: 4
  Minimum UX score (1-10) [7.0]: 8.0

✓ Configuration saved!
   Location: autocoder_config.yaml
```

---

## Step 3: Create Initial Specification

Create `initial_spec.md`:

```markdown
# Task Management Dashboard

## Overview
A web-based task management dashboard with kanban board visualization.

## Target Users
- Individual users managing personal tasks
- Small teams coordinating projects

## Core Features

### 1. User Authentication
- Email/password login
- OAuth (Google)
- Session management

### 2. Kanban Board
- Three columns: To Do, In Progress, Done
- Drag and drop tasks between columns
- Color-coded priority labels (High, Medium, Low)

### 3. Task Management
- Create, edit, delete tasks
- Task details: title, description, due date, priority
- Attach tags/labels
- Mark tasks complete

### 4. Filtering & Search
- Filter by: priority, tags, due date
- Search by title/description
- Sort: due date, priority, creation date

### 5. Mobile Support
- Responsive design (mobile, tablet, desktop)
- Touch-friendly interactions
- Optimized for iOS and Android

## Design Requirements
- Clean, modern aesthetic
- WCAG AA accessibility compliance
- Fast load times (<2 seconds)
- Intuitive onboarding for new users

## Technical Stack
- Frontend: React + TypeScript
- Backend: Node.js + Express
- Database: PostgreSQL
- Authentication: JWT tokens (httpOnly cookies)
```

---

## Step 4: Run Complete Workflow

Create `run_workflow.py`:

```python
import asyncio
from pathlib import Path
from integration.workflow_orchestrator import run_complete_workflow, WorkflowConfig

async def main():
    # Read initial spec
    with open('initial_spec.md', 'r') as f:
        initial_spec = f.read()

    # Configure workflow
    config = WorkflowConfig(
        enable_design_iteration=True,
        enable_checkpoints=True,
        enable_ux_evaluation=True,
        enable_metrics=True,
        checkpoint_frequency=10,
        max_design_iterations=4,
        min_ux_score=8.0,
        verbose_logging=True
    )

    print("🚀 Starting complete workflow for Task Management Dashboard")
    print("=" * 60)

    # Run workflow
    result = await run_complete_workflow(
        project_dir=Path("."),
        initial_spec=initial_spec,
        config=config
    )

    # Print results
    print("\n" + "=" * 60)
    print("📊 WORKFLOW RESULTS")
    print("=" * 60)
    print(f"Success: {'✅ Yes' if result.success else '❌ No'}")
    print(f"Duration: {result.total_duration_seconds:.1f}s ({result.total_duration_seconds/3600:.1f}h)")
    print()
    print("Design Iteration:")
    print(f"  Iterations: {result.design_iterations}")
    print(f"  Final spec: {result.design_spec_path}")
    print()
    print("Development:")
    print(f"  Features: {result.features_completed}/{result.features_total}")
    print(f"  Checkpoints: {result.checkpoints_run}")
    print(f"  Critical issues: {result.critical_issues_found}")
    print()
    print("UX Evaluation:")
    print(f"  Score: {result.ux_score}/10")
    print(f"  Report: {result.ux_report_path}")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(main())
```

Run it:

```bash
python run_workflow.py
```

---

## Step 5: Observe Design Iteration

The workflow starts with design iteration:

```
==================================================
PHASE 1: DESIGN ITERATION
==================================================

Creating initial design from specification...

Iteration 1: Initial Design
  Personas reviewing design...

  Sarah (Accessibility): ⚠️  Issues found
    - Missing keyboard navigation plan
    - No screen reader announcements specified
    - Color contrast ratios undefined

  Marcus (Power User): ⚠️  Issues found
    - No keyboard shortcuts defined
    - Missing bulk operations
    - No data export functionality

  Elena (Novice): ⚠️  Issues found
    - Onboarding flow unclear
    - Too many features exposed initially
    - Help text missing

  David (Mobile-First): ❌ Critical issues
    - No mobile layout specified
    - Touch targets undefined
    - Responsive breakpoints missing

  Aisha (Brand/Aesthetics): ⚠️  Issues found
    - Color palette undefined
    - Typography hierarchy unclear
    - Visual style guide missing

  Raj (Security): ✅ Looks good
    - JWT in httpOnly cookies ✓
    - OAuth security considered ✓

  Lisa (Performance): ⚠️  Issues found
    - Bundle size not considered
    - No lazy loading plan
    - Heavy dependencies possible

Synthesizing feedback...
Creating Iteration 2...

Iteration 2: Addressing Feedback
  ✓ Added keyboard navigation spec
  ✓ Added mobile-first layouts
  ✓ Defined 3-step onboarding
  ✓ Created accessible color palette (WCAG AA)
  ✓ Added performance budget

  Personas reviewing design...

  Sarah: ✅ Much better!
  Marcus: ✅ Great improvements
  Elena: ✅ Onboarding clear now
  David: ✅ Mobile layouts perfect
  Aisha: ✅ Love the color scheme
  Raj: ✅ Security looks good
  Lisa: ✅ Performance considered

Design converged after 2 iterations!
✅ Final spec saved to: prompts/app_spec.txt
```

---

## Step 6: Monitor Development

Development starts automatically:

```
==================================================
PHASE 2: DEVELOPMENT WITH CHECKPOINTS
==================================================

Development and checkpoint integration ready
Checkpoints will run every 10 features

[Session 1] Initializer agent creating features...
Created 45 features from spec.

[Session 2] Implementing Feature 1: User registration form
  ✅ Complete

[Session 2] Implementing Feature 2: Email validation
  ✅ Complete

...

[10 features complete] → Running checkpoint...

🚧 CHECKPOINT: 10 features complete

Running checkpoint agents:
  ✓ Code Review Agent
  ✓ Security Audit Agent
  ✓ Performance Agent

Code Review: ⚠️ PASS WITH WARNINGS
  Warnings:
    - Duplicated validation logic in 2 files
    - Magic number (100) without constant

Security Audit: ✅ PASS
  No vulnerabilities found

Performance: ✅ PASS
  Bundle size: 245 KB (target: <300 KB)

Decision: ✅ CONTINUE_WITH_WARNINGS

...

[20 features complete] → Running checkpoint...

Security Audit: ❌ FAIL - CRITICAL ISSUES
  Critical:
    - JWT tokens stored in localStorage (XSS risk)
    - No rate limiting on login endpoint

CRITICAL ISSUE - Development paused.

Creating fix features:
  Feature 46: Migrate JWT storage to httpOnly cookies
  Feature 47: Add rate limiting to authentication

[Implementing fix features...]
  Feature 46: ✅ Complete
  Feature 47: ✅ Complete

[Re-running checkpoint...]
  ✅ All checks passed

Continuing development...

...

[45 features complete]
✅ All features passing!
```

---

## Step 7: UX Evaluation

After development completes:

```
==================================================
PHASE 3: UX EVALUATION
==================================================

Generating Playwright tests...
   ✓ Generated test for: onboarding
   ✓ Generated test for: dashboard
   ✓ Generated test for: settings

Running Playwright tests...
  ✅ All tests passed: 3/3

Evaluating UX from screenshots...

Visual QA:
  ✓ No alignment issues
  ✓ No overflow detected
  ✓ Responsive design verified

Specialist Evaluation:
  Accessibility: 9.3/10 (Excellent)
  Brand Consistency: 8.8/10 (Very good)
  Mobile UX: 9.1/10 (Excellent)
  Onboarding: 8.5/10 (Very good)

Persona User Testing:
  Sarah: "Perfect keyboard navigation!" ✅ Would use
  Marcus: "Love the shortcuts" ✅ Would use
  Elena: "Easiest onboarding" ✅ Would use
  David: "Works great on phone" ✅ Would use
  Aisha: "Beautiful design" ✅ Would use

Generating final UX report...
✅ UX evaluation passed: 8.9/10 (min: 8.0)
   Report saved to: autocoder_output/UX_REPORT_FINAL.md
```

---

## Step 8: Review Results

```
==================================================
✅ WORKFLOW COMPLETE
==================================================
   Duration: 18245.3s (5.1h)
   UX Score: 8.9/10

📊 WORKFLOW RESULTS
==================================================
Success: ✅ Yes
Duration: 18245.3s (5.1h)

Design Iteration:
  Iterations: 2
  Final spec: prompts/app_spec.txt

Development:
  Features: 45/45
  Checkpoints: 4
  Critical issues: 2 (fixed)

UX Evaluation:
  Score: 8.9/10
  Report: autocoder_output/UX_REPORT_FINAL.md
==================================================
```

---

## Step 9: Review Reports

### Design Specification

```bash
cat prompts/app_spec.txt
```

Contains the final, persona-validated design.

### UX Report

```bash
cat autocoder_output/UX_REPORT_FINAL.md
```

Contains:
- Executive summary
- Strengths (accessibility, mobile UX, etc.)
- Weaknesses (minor improvements needed)
- Suggested improvements
- Feature ideas from personas

### Checkpoint Reports

```bash
ls checkpoints/
# checkpoint_01_10_features.md
# checkpoint_02_20_features.md
# checkpoint_03_30_features.md
# checkpoint_04_45_features.md
```

---

## Next Steps

1. **Address UX Improvements** - Implement suggested improvements from UX report
2. **Deploy** - Application is ready for deployment
3. **Monitor Metrics** - Review performance report for ROI analysis

---

## Full Code

Complete example available at: [docs/examples/task-dashboard/](task-dashboard/)
