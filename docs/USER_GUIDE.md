# Autocoder User Guide

**Version:** 2.0 (Phase 6 Integration & Polish)
**Last Updated:** January 2026

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Complete Workflow](#complete-workflow)
4. [Phase-by-Phase Guide](#phase-by-phase-guide)
5. [Configuration](#configuration)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Introduction

Autocoder is an **autonomous coding agent system** that transforms your product requirements into fully-functional applications through a multi-phase workflow:

1. **Design Iteration** (Phase 4) - Multi-persona design validation before coding
2. **Development** (Phases 1-3) - Automated feature implementation with quality gates
3. **UX Evaluation** (Phase 5) - Post-development UX testing and validation

### Key Features

✅ **Multi-Persona Design Review** - 7 built-in personas validate your design
✅ **Intelligent Skip Management** - Dependency tracking prevents rework
✅ **Automated Checkpoints** - Code quality gates during development
✅ **UX Evaluation** - Automated Playwright tests and visual QA
✅ **Performance Metrics** - Track velocity, cost, and ROI

---

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourorg/autocoder-2.git
cd autocoder-2

# Install dependencies
pip install -r requirements.txt

# Run the launcher
python start.py
```

### Quick Start

```bash
# 1. Create a new project
python start.py

# 2. Run configuration wizard
python -m integration.config_ui --setup

# 3. Start the workflow
python autonomous_agent_demo.py --project-dir my-project
```

---

## Complete Workflow

### Option 1: Full Workflow (All Phases)

```python
from pathlib import Path
from integration.workflow_orchestrator import run_complete_workflow, WorkflowConfig

# Configure workflow
config = WorkflowConfig(
    enable_design_iteration=True,
    enable_checkpoints=True,
    enable_ux_evaluation=True,
    checkpoint_frequency=10,
    min_ux_score=7.0
)

# Run complete workflow
result = await run_complete_workflow(
    project_dir=Path("my-project"),
    initial_spec="Build a task management dashboard...",
    config=config
)

# Check results
print(f"Success: {result.success}")
print(f"UX Score: {result.ux_score}/10")
```

### Option 2: Development Only (Skip Design & UX)

```python
config = WorkflowConfig(
    enable_design_iteration=False,
    enable_checkpoints=True,
    enable_ux_evaluation=False
)

result = await run_complete_workflow(
    project_dir=Path("my-project"),
    config=config
)
```

---

## Phase-by-Phase Guide

### Phase 1: Design Iteration

**What it does:** Validates your design with 7 diverse personas before writing any code.

**When to use:** Starting a new project or major redesign.

**How to run:**

```bash
# Interactive design review
python design_review.py --spec initial_spec.md --project-dir my-project

# Auto mode (runs until convergence)
python design_review.py --spec initial_spec.md --auto --project-dir my-project
```

**Built-in Personas:**
- **Sarah Chen** - Accessibility Advocate (WCAG, screen readers)
- **Marcus Rodriguez** - Power User (efficiency, shortcuts)
- **Elena Martinez** - Novice User (simplicity, onboarding)
- **David Kim** - Mobile-First User (touch-friendly, responsive)
- **Aisha Patel** - Brand/Aesthetics (visual appeal)
- **Raj Sharma** - Security Conscious (privacy, encryption)
- **Lisa Johnson** - Performance Optimizer (speed, bundle size)

**Example Output:**

```
Design Iteration 1:
  Sarah: ⚠️  Missing keyboard navigation
  Marcus: ✅ Bulk operations look good
  Elena: ⚠️  Onboarding needs more steps
  David: ❌ No mobile layout specified
  Aisha: ⚠️  Color palette undefined

Iteration 2: Addressing feedback...
  ✅ All personas approve!

Design converged after 2 iterations.
Final spec saved to: prompts/app_spec.txt
```

---

### Phase 2: Development with Checkpoints

**What it does:** Implements features with automated quality gates.

**Checkpoints run every N features** (configurable, default: 10)

**Checkpoint Types:**
- **Code Review** - Detects code smells, duplication, naming issues
- **Security Audit** - OWASP Top 10 vulnerability scanning
- **Performance** - Bundle size, N+1 queries, heavy dependencies

**Example:**

```bash
# Run development
python autonomous_agent_demo.py --project-dir my-project

# During development, checkpoints run automatically:
[10 features complete] → Running checkpoint...
  ✅ Code review: PASS
  ✅ Security audit: PASS
  ⚠️  Performance: Bundle size growing (warning)

Continue? [Y/n] Y

[20 features complete] → Running checkpoint...
  ❌ Security: JWT in localStorage (critical)

CRITICAL ISSUE - Development paused.
Fix required in: src/auth/tokenManager.js:23

# Agent creates fix feature automatically
Feature 21: Migrate JWT storage to httpOnly cookies
  ✅ Complete

# Checkpoint re-runs
  ✅ Security: PASS

Continuing development...
```

---

### Phase 3: UX Evaluation

**What it does:** Automated UX testing with Playwright and multi-specialist evaluation.

**When to run:** After development completes or on-demand.

**How to run:**

```bash
# Start your app first
npm start  # Your app runs on http://localhost:3000

# Run UX evaluation
python -c "
from pathlib import Path
from ux_eval.ux_evaluator import UXEvaluator
import asyncio

async def main():
    evaluator = UXEvaluator(Path('my-project'))
    result = await evaluator.evaluate('http://localhost:3000')
    report = evaluator.generate_final_report(result)
    evaluator.save_report(report, Path('UX_REPORT_FINAL.md'))

asyncio.run(main())
"
```

**What it evaluates:**

1. **Visual QA** - Layout issues, alignment, overflow
2. **Accessibility** - WCAG AA compliance
3. **Brand Consistency** - Visual appeal, color scheme
4. **Mobile UX** - Touch targets, responsive design
5. **Onboarding** - Clarity, intuitiveness

**Example Output:**

```
UX Evaluation Results:
  Overall Score: 8.4/10 ✅ PASS

Specialist Feedback:
  Accessibility: 9.3/10 (Excellent keyboard nav)
  Mobile UX: 9.0/10 (Perfect responsive design)
  Onboarding: 7.6/10 (Could be more concise)

Persona User Testing:
  Sarah (Accessibility): "Perfect keyboard navigation!"
  Marcus (Power User): "Love the bulk edit feature"
  Elena (Novice): "Easiest onboarding I've seen"

Issues Found:
  ⚠️  Settings button misalignment (4px offset)
  ⚠️  Card padding inconsistency (16px vs 20px)

Report saved to: UX_REPORT_FINAL.md
```

---

## Configuration

### Configuration File: `autocoder_config.yaml`

```yaml
# Phase toggles
enable_design_iteration: true
enable_checkpoints: true
enable_ux_evaluation: true
enable_metrics: true

# Design iteration settings
max_design_iterations: 4
design_convergence_threshold: 0.8

# Checkpoint settings
checkpoint_frequency: 10
auto_pause_on_critical: true

# UX evaluation settings
run_ux_after_completion: true
ux_flows:
  - onboarding
  - dashboard
  - settings
min_ux_score: 7.0

# Metrics settings
track_performance: true
generate_comparison: true

# Output settings
output_directory: ./autocoder_output
verbose_logging: true
```

### Using the Configuration CLI

```bash
# Show current configuration
python -m integration.config_ui --show

# Enable/disable features
python -m integration.config_ui --enable design
python -m integration.config_ui --disable ux

# Set thresholds
python -m integration.config_ui --set checkpoint_frequency 5
python -m integration.config_ui --set min_ux_score 8.5

# Interactive setup wizard
python -m integration.config_ui --setup

# Reset to defaults
python -m integration.config_ui --reset

# Export/import
python -m integration.config_ui --export my_config.json
python -m integration.config_ui --import my_config.json
```

---

## Best Practices

### 1. Start with Design Iteration

✅ **DO:** Run design iteration for new projects
```bash
python design_review.py --spec initial_spec.md --auto
```

❌ **DON'T:** Skip design iteration for complex UIs
❌ **DON'T:** Start coding without persona feedback

### 2. Use Appropriate Checkpoint Frequency

- **Small projects (<50 features):** Every 5 features
- **Medium projects (50-200 features):** Every 10 features (default)
- **Large projects (>200 features):** Every 20 features

```bash
python -m integration.config_ui --set checkpoint_frequency 5
```

### 3. Always Run UX Evaluation Before Launch

✅ **DO:** Run UX evaluation on staging
```bash
# Start staging app
npm start

# Run UX evaluation
python ux_evaluation.py --url http://localhost:3000
```

✅ **DO:** Address critical UX issues immediately
✅ **DO:** Re-run evaluation after fixes

### 4. Monitor Performance Metrics

```bash
# View real-time dashboard during development
python metrics_dashboard.py --project my-project

# Generate performance report after completion
python report_generator.py --project my-project
```

### 5. Handle Blockers Promptly

When agent pauses for blockers:

**Option 1: Provide Now** (recommended for quick values)
```
Required: OAUTH_CLIENT_ID
Enter value: [paste from console]
```

**Option 2: Defer** (for values you'll add later)
```
Actions:
  [2] Defer (I'll add to .env later)
```

Check blockers:
```bash
python start.py --show-blockers
```

Unblock when ready:
```bash
python start.py --unblock 5
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide.

### Quick Fixes

**Agent stuck on a feature?**
```bash
# Skip the feature
python start.py --skip 15
```

**Checkpoint blocking progress?**
```bash
# Disable checkpoints temporarily
python -m integration.config_ui --disable checkpoints
```

**UX evaluation failing?**
```bash
# Check if app is running
curl http://localhost:3000

# Reduce flows to test
python -m integration.config_ui --set ux_flows onboarding,dashboard
```

---

## Next Steps

- **Advanced Usage:** See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Examples:** See [docs/examples/](examples/)
- **Troubleshooting:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Contributing:** See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

---

**Need Help?**

- GitHub Issues: https://github.com/yourorg/autocoder-2/issues
- Discussions: https://github.com/yourorg/autocoder-2/discussions
- Documentation: https://autocoder-docs.example.com
