# Sample Project: Todo List App

This is a **showcase project** demonstrating the complete autocoder workflow from design iteration to UX evaluation.

---

## Project Overview

**Name:** Simple Todo List App
**Purpose:** Demonstrate autocoder's complete workflow
**Complexity:** Small project (ideal for learning)
**Duration:** ~1-2 hours with autocoder

---

## What This Demonstrates

✅ **Design Iteration** - Multi-persona design validation
✅ **Development** - Automated feature implementation
✅ **Checkpoints** - Code quality gates during development
✅ **UX Evaluation** - Automated UX testing and validation
✅ **Complete Workflow** - End-to-end integration

---

## Project Structure

```
sample_project/
├── README.md                          # This file
├── initial_spec.md                    # Initial design specification
├── autocoder_config.yaml              # Workflow configuration
├── run_workflow.py                    # Workflow execution script
├── expected_output/                   # Expected output examples
│   ├── design_iteration_1.md
│   ├── design_iteration_2_final.md
│   ├── checkpoint_01_05_features.md
│   ├── checkpoint_02_10_features.md
│   └── UX_REPORT_FINAL.md
└── src/                               # Generated app code (after workflow)
```

---

## Quick Start

### Step 1: Copy Sample Project

```bash
# Copy sample project to your workspace
cp -r sample_project my-todo-app
cd my-todo-app
```

### Step 2: Run Workflow

```bash
# Option 1: Full workflow (design → dev → UX)
python run_workflow.py

# Option 2: Development only (skip design & UX)
python run_workflow.py --dev-only

# Option 3: Interactive (pause after each phase)
python run_workflow.py --interactive
```

### Step 3: Review Results

```bash
# Design iteration results
cat prompts/app_spec.txt

# Checkpoint reports
ls checkpoints/

# UX evaluation report
cat autocoder_output/UX_REPORT_FINAL.md

# Performance metrics
cat benchmarks/metrics_run_1.json
```

---

## Configuration

The sample uses this configuration (see `autocoder_config.yaml`):

```yaml
# Phase toggles
enable_design_iteration: true
enable_checkpoints: true
enable_ux_evaluation: true
enable_metrics: true

# Design iteration settings
max_design_iterations: 3
design_convergence_threshold: 0.8

# Checkpoint settings
checkpoint_frequency: 5        # Small project, checkpoint every 5 features
auto_pause_on_critical: true

# UX evaluation settings
run_ux_after_completion: true
ux_flows:
  - onboarding
  - dashboard
min_ux_score: 7.0

# Metrics settings
track_performance: true
generate_comparison: true

# Output settings
output_directory: ./autocoder_output
verbose_logging: true
```

---

## Expected Features

The workflow will create approximately **15 features**:

### Authentication (3 features)
1. User registration
2. User login
3. Session management

### Todo Management (8 features)
4. Create todo
5. Edit todo
6. Delete todo
7. Mark complete/incomplete
8. Todo list display
9. Filter by status (all/active/completed)
10. Sort todos (by date, priority)
11. Todo counter

### UI/UX (4 features)
12. Responsive layout
13. Loading states
14. Error handling
15. Accessibility features

---

## Expected Timeline

With autocoder:

- **Design Iteration:** 2-3 iterations (~5 minutes)
- **Development:** 15 features (~45 minutes)
- **Checkpoints:** 3 checkpoints (~5 minutes each)
- **UX Evaluation:** ~10 minutes

**Total:** ~1-1.5 hours (vs. 8-16 hours manual coding)

---

## Learning Objectives

After running this sample project, you will understand:

1. **How to write an initial specification** that personas can evaluate
2. **How persona feedback improves design** before coding starts
3. **How checkpoints catch issues early** (security, performance, code quality)
4. **How UX evaluation validates user experience** automatically
5. **How to configure the workflow** for different project sizes
6. **How to interpret reports** (design, checkpoint, UX)

---

## Next Steps

### Modify the Sample

Try these experiments:

1. **Change the spec** - Add a feature (e.g., "tags for todos")
   - Observe how personas react
   - See how many features get created

2. **Adjust checkpoint frequency** - Set to 3 instead of 5
   - See checkpoints run more often
   - Compare impact on development flow

3. **Raise UX score threshold** - Set to 8.5 instead of 7.0
   - See if UX evaluation becomes more strict
   - Observe suggested improvements

4. **Disable a phase** - Turn off design iteration
   - See how it affects final quality
   - Compare reports with/without design iteration

### Create Your Own Project

1. Copy the sample structure
2. Write your own `initial_spec.md`
3. Adjust `autocoder_config.yaml` for your project size
4. Run `run_workflow.py`

---

## Common Issues

### Design iteration fails
- **Fix:** Ensure `initial_spec.md` has clear requirements
- **Fix:** Check that personas are defined (should be automatic)

### Development stuck on feature
- **Fix:** Check `features.db` for blockers: `python start.py --show-blockers`
- **Fix:** Skip problematic feature: `python start.py --skip <id>`

### UX evaluation fails
- **Fix:** Ensure app is running: `npm start` (in generated `src/` directory)
- **Fix:** Install Playwright: `playwright install`

See [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) for more help.

---

## Files in This Sample

### `initial_spec.md`

The initial design specification. This is what you would write before starting autocoder.

Key sections:
- **Overview** - What the app does
- **Target Users** - Who will use it
- **Core Features** - What functionality it needs
- **Design Requirements** - UX constraints (accessibility, performance, etc.)

### `autocoder_config.yaml`

Workflow configuration optimized for this small project.

Key settings:
- `checkpoint_frequency: 5` - Checkpoint every 5 features (vs. default 10)
- `max_design_iterations: 3` - Limit iterations for small project
- `min_ux_score: 7.0` - Standard quality threshold

### `run_workflow.py`

Workflow execution script with options:
- `--dev-only` - Skip design & UX
- `--interactive` - Pause after each phase
- `--no-checkpoints` - Disable checkpoints

### `expected_output/`

Example outputs showing what you should see after running the workflow.

Use these to verify your results match expectations.

---

## Advanced Usage

### Run Phases Separately

```python
from pathlib import Path
from integration.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig

orchestrator = WorkflowOrchestrator(Path("."), config)

# Just design iteration
spec = await orchestrator.run_design_iteration(initial_spec)

# Just development
await orchestrator.run_development_with_checkpoints(features_total=15)

# Just UX evaluation
score = await orchestrator.run_ux_evaluation("http://localhost:3000")
```

### Custom Personas

Create `personas/custom_persona.json`:
```json
{
  "name": "Alex",
  "role": "Keyboard Power User",
  "background": "Uses only keyboard, no mouse",
  "evaluation_rubric": {
    "keyboard_navigation": {"weight": 0.5},
    "shortcuts": {"weight": 0.3},
    "focus_indicators": {"weight": 0.2}
  }
}
```

Load in workflow:
```python
from design.persona_system import PersonaLoader

loader = PersonaLoader()
alex = loader.load_persona(Path("personas/custom_persona.json"))
```

---

## Support

- **Documentation:** [docs/USER_GUIDE.md](../docs/USER_GUIDE.md)
- **API Reference:** [docs/API_DOCUMENTATION.md](../docs/API_DOCUMENTATION.md)
- **Troubleshooting:** [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)
- **Issues:** https://github.com/anthropics/autocoder/issues

---

**Sample Version:** 1.0
**Last Updated:** January 2026
**Difficulty:** Beginner
**Duration:** 1-2 hours
