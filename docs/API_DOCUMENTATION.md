# Autocoder API Documentation

**Version:** 2.0 (Phase 6 Integration & Polish)
**Last Updated:** January 2026

---

## Table of Contents

1. [Workflow Orchestrator API](#workflow-orchestrator-api)
2. [Configuration API](#configuration-api)
3. [Design Iteration API](#design-iteration-api)
4. [Checkpoint API](#checkpoint-api)
5. [UX Evaluation API](#ux-evaluation-api)
6. [Metrics API](#metrics-api)
7. [Integration Patterns](#integration-patterns)

---

## Workflow Orchestrator API

### `WorkflowOrchestrator`

Orchestrates the complete workflow from design to UX evaluation.

#### Constructor

```python
from pathlib import Path
from integration.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig

orchestrator = WorkflowOrchestrator(
    project_dir=Path("my-project"),
    config=WorkflowConfig()  # Optional, uses defaults if not provided
)
```

#### Methods

##### `run_complete_workflow(initial_spec, app_url)`

Run the complete workflow from design to UX evaluation.

**Parameters:**
- `initial_spec` (str, optional): Initial design specification for design iteration phase
- `app_url` (str): URL of running application for UX evaluation (default: "http://localhost:3000")

**Returns:** `WorkflowResult` - Complete workflow status

**Example:**

```python
result = await orchestrator.run_complete_workflow(
    initial_spec="Build a task management dashboard with kanban boards...",
    app_url="http://localhost:3000"
)

if result.success:
    print(f"✅ Workflow complete!")
    print(f"   UX Score: {result.ux_score}/10")
    print(f"   Duration: {result.total_duration_seconds}s")
```

##### `update_development_progress(features_completed)`

Update development progress during implementation.

**Parameters:**
- `features_completed` (int): Number of features completed

**Example:**

```python
# In your development loop
orchestrator.update_development_progress(25)
```

##### `record_checkpoint(critical_issues)`

Record checkpoint execution results.

**Parameters:**
- `critical_issues` (int): Number of critical issues found

**Example:**

```python
# After checkpoint runs
orchestrator.record_checkpoint(critical_issues=2)
```

---

## Configuration API

### `WorkflowConfig`

Configuration dataclass for the complete workflow.

#### Constructor

```python
from integration.workflow_orchestrator import WorkflowConfig

config = WorkflowConfig(
    # Phase toggles
    enable_design_iteration=True,
    enable_checkpoints=True,
    enable_ux_evaluation=True,
    enable_metrics=True,

    # Design iteration settings
    max_design_iterations=4,
    design_convergence_threshold=0.8,

    # Checkpoint settings
    checkpoint_frequency=10,
    auto_pause_on_critical=True,

    # UX evaluation settings
    run_ux_after_completion=True,
    ux_flows=['onboarding', 'dashboard', 'settings'],
    min_ux_score=7.0,

    # Metrics settings
    track_performance=True,
    generate_comparison=True,

    # Output settings
    output_directory=Path('./autocoder_output'),
    verbose_logging=True
)
```

#### Methods

##### `to_dict()`

Convert configuration to dictionary.

**Returns:** `Dict[str, Any]`

**Example:**

```python
config_dict = config.to_dict()
# Save to YAML
import yaml
with open('config.yaml', 'w') as f:
    yaml.dump(config_dict, f)
```

##### `from_dict(data)` (static method)

Create configuration from dictionary.

**Parameters:**
- `data` (Dict[str, Any]): Configuration dictionary

**Returns:** `WorkflowConfig`

**Example:**

```python
import yaml
with open('config.yaml', 'r') as f:
    data = yaml.safe_load(f)

config = WorkflowConfig.from_dict(data)
```

---

### `ConfigurationUI`

CLI interface for managing workflow configuration.

#### Constructor

```python
from pathlib import Path
from integration.config_ui import ConfigurationUI

ui = ConfigurationUI(project_dir=Path("my-project"))
```

#### Methods

##### `show_config()`

Display current configuration.

```python
ui.show_config()
```

##### `enable_feature(feature)`

Enable a feature.

**Parameters:**
- `feature` (str): Feature name ("design", "checkpoints", "ux", "metrics")

```python
ui.enable_feature('checkpoints')
```

##### `disable_feature(feature)`

Disable a feature.

**Parameters:**
- `feature` (str): Feature name

```python
ui.disable_feature('ux')
```

##### `set_threshold(name, value)`

Set a threshold value.

**Parameters:**
- `name` (str): Threshold name ("checkpoint_frequency", "max_design_iterations", "min_ux_score", etc.)
- `value` (Any): New value

```python
ui.set_threshold('checkpoint_frequency', 15)
ui.set_threshold('min_ux_score', 8.5)
```

##### `save_config()`

Save configuration to `autocoder_config.yaml`.

```python
ui.save_config()
```

##### `reset_config()`

Reset configuration to defaults.

```python
ui.reset_config()
```

##### `export_json(output_path)` / `import_json(input_path)`

Export/import configuration as JSON.

```python
ui.export_json(Path('my_config.json'))
ui.import_json(Path('my_config.json'))
```

---

## Design Iteration API

### `DesignReviewCLI`

CLI tool for running design review process.

#### Constructor

```python
from pathlib import Path
from design.review import DesignReviewCLI

cli = DesignReviewCLI(project_dir=Path("my-project"))
```

#### Methods

##### `run_auto_mode(initial_spec, max_iterations, convergence_threshold)`

Run design review in auto mode (runs until convergence).

**Parameters:**
- `initial_spec` (str): Initial design specification
- `max_iterations` (int): Maximum iterations (default: 4)
- `convergence_threshold` (float): Convergence threshold (default: 0.8)

**Returns:** `Path` - Path to final design spec

**Example:**

```python
final_spec_path = cli.run_auto_mode(
    initial_spec="Build a dashboard with...",
    max_iterations=4,
    convergence_threshold=0.8
)

print(f"Final spec saved to: {final_spec_path}")
```

##### `run_interactive_mode(initial_spec)`

Run design review in interactive mode (pause after each iteration).

**Parameters:**
- `initial_spec` (str): Initial design specification

**Returns:** `Path` - Path to final design spec

---

## Checkpoint API

### `CheckpointOrchestrator`

Orchestrates checkpoint execution.

#### Constructor

```python
from pathlib import Path
from checkpoint.orchestrator import CheckpointOrchestrator

orchestrator = CheckpointOrchestrator(project_dir=Path("my-project"))
```

#### Methods

##### `run_checkpoint(features_completed)`

Run checkpoint for current development state.

**Parameters:**
- `features_completed` (int): Number of features completed

**Returns:** `CheckpointDecision` - Decision (PAUSE, CONTINUE, CONTINUE_WITH_WARNINGS)

**Example:**

```python
decision = await orchestrator.run_checkpoint(features_completed=25)

if decision == CheckpointDecision.PAUSE:
    print("Critical issues found - pausing development")
elif decision == CheckpointDecision.CONTINUE_WITH_WARNINGS:
    print("Warnings found but continuing")
else:
    print("All checks passed")
```

---

### Convenience Function

```python
from checkpoint.orchestrator import run_checkpoint_if_needed

# Automatically checks if checkpoint should run based on config
decision = await run_checkpoint_if_needed(
    project_dir=Path("my-project"),
    features_completed=25
)
```

---

## UX Evaluation API

### `UXEvaluator`

Evaluates UX from screenshots.

#### Constructor

```python
from pathlib import Path
from ux_eval.ux_evaluator import UXEvaluator

evaluator = UXEvaluator(project_dir=Path("my-project"))
```

#### Methods

##### `evaluate(app_url)`

Run complete UX evaluation.

**Parameters:**
- `app_url` (str): URL of running application

**Returns:** `UXEvaluationResult` - Complete UX evaluation results

**Example:**

```python
result = await evaluator.evaluate("http://localhost:3000")

print(f"Overall Score: {result.overall_score}/10")
print(f"Accessibility: {result.accessibility_score}/10")
print(f"Mobile UX: {result.mobile_score}/10")
```

##### `generate_final_report(ux_result)`

Generate final UX report.

**Parameters:**
- `ux_result` (UXEvaluationResult): UX evaluation results

**Returns:** `FinalUXReport` - Comprehensive report

**Example:**

```python
final_report = evaluator.generate_final_report(result)

print(f"Strengths: {len(final_report.strengths)}")
print(f"Weaknesses: {len(final_report.weaknesses)}")
print(f"Feature Ideas: {len(final_report.feature_ideas)}")
```

##### `save_report(report, output_path)`

Save report to markdown file.

**Parameters:**
- `report` (FinalUXReport): Report to save
- `output_path` (Path): Path to output file

**Example:**

```python
evaluator.save_report(final_report, Path("UX_REPORT_FINAL.md"))
```

---

## Metrics API

### `MetricsCollector`

Collects performance metrics during development.

#### Constructor

```python
from metrics.collector import MetricsCollector

collector = MetricsCollector(project_name="my-project")
```

#### Methods

##### `track_feature_complete(feature, first_try, attempts)`

Track feature completion.

**Parameters:**
- `feature` (Dict): Feature data
- `first_try` (bool): Whether completed on first try
- `attempts` (int): Number of attempts needed

**Example:**

```python
collector.track_feature_complete(
    feature={'id': 15, 'name': 'User authentication'},
    first_try=True,
    attempts=1
)
```

##### `calculate_velocity()`

Calculate development velocity.

**Returns:** `float` - Features per hour

**Example:**

```python
velocity = collector.calculate_velocity()
print(f"Velocity: {velocity:.1f} features/hour")
```

##### `export_to_json(output_dir)`

Export metrics to JSON.

**Parameters:**
- `output_dir` (Path): Output directory

**Example:**

```python
collector.export_to_json(Path("benchmarks"))
```

---

### `PerformanceReportGenerator`

Generates comprehensive performance reports.

#### Constructor

```python
from pathlib import Path
from metrics.report_generator import PerformanceReportGenerator

generator = PerformanceReportGenerator(project_dir=Path("my-project"))
```

#### Methods

##### `generate(run_id)`

Generate performance report.

**Parameters:**
- `run_id` (int): Metrics run ID

**Returns:** `str` - Markdown report content

**Example:**

```python
report = generator.generate(run_id=1)

# Save to file
with open('PERFORMANCE_REPORT.md', 'w') as f:
    f.write(report)
```

---

## Integration Patterns

### Pattern 1: Complete Workflow

```python
from pathlib import Path
from integration.workflow_orchestrator import run_complete_workflow, WorkflowConfig
import asyncio

async def main():
    config = WorkflowConfig(
        enable_design_iteration=True,
        enable_checkpoints=True,
        enable_ux_evaluation=True,
        checkpoint_frequency=10,
        min_ux_score=7.0
    )

    result = await run_complete_workflow(
        project_dir=Path("my-project"),
        initial_spec="Build a task management dashboard...",
        config=config
    )

    if result.success:
        print(f"✅ Workflow complete!")
        print(f"   Design iterations: {result.design_iterations}")
        print(f"   Features completed: {result.features_completed}/{result.features_total}")
        print(f"   Checkpoints run: {result.checkpoints_run}")
        print(f"   UX score: {result.ux_score}/10")
        print(f"   Duration: {result.total_duration_seconds:.1f}s")

asyncio.run(main())
```

### Pattern 2: Development Only

```python
from pathlib import Path
from integration.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig
import asyncio

async def main():
    config = WorkflowConfig(
        enable_design_iteration=False,
        enable_checkpoints=True,
        enable_ux_evaluation=False
    )

    orchestrator = WorkflowOrchestrator(Path("my-project"), config)

    success = await orchestrator.run_development_with_checkpoints(
        features_total=50
    )

    if success:
        print("Development setup complete")

asyncio.run(main())
```

### Pattern 3: UX Evaluation Only

```python
from pathlib import Path
from ux_eval.ux_evaluator import UXEvaluator
import asyncio

async def main():
    evaluator = UXEvaluator(Path("my-project"))

    # Run evaluation
    result = await evaluator.evaluate("http://localhost:3000")

    # Generate report
    final_report = evaluator.generate_final_report(result)

    # Save
    evaluator.save_report(final_report, Path("UX_REPORT_FINAL.md"))

    print(f"Overall UX Score: {result.overall_score}/10")

asyncio.run(main())
```

### Pattern 4: Custom Configuration Management

```python
from pathlib import Path
from integration.config_ui import ConfigurationUI

# Load current config
ui = ConfigurationUI(Path("my-project"))

# Modify programmatically
ui.config.checkpoint_frequency = 5
ui.config.min_ux_score = 8.5
ui.enable_feature('design')

# Save
ui.save_config()

# Export for version control
ui.export_json(Path("configs/production.json"))
```

---

## Type Definitions

### `WorkflowPhase`

```python
from enum import Enum

class WorkflowPhase(Enum):
    DESIGN_ITERATION = "design_iteration"
    DEVELOPMENT = "development"
    CHECKPOINTS = "checkpoints"
    UX_EVALUATION = "ux_evaluation"
    COMPLETE = "complete"
```

### `WorkflowResult`

```python
@dataclass
class WorkflowResult:
    project_name: str
    start_time: datetime
    end_time: Optional[datetime]
    current_phase: WorkflowPhase

    # Phase results
    design_spec_path: Optional[Path]
    design_iterations: int
    development_complete: bool
    features_completed: int
    features_total: int
    checkpoints_run: int
    critical_issues_found: int
    ux_evaluation_complete: bool
    ux_score: Optional[float]
    ux_report_path: Optional[Path]

    # Metrics
    total_duration_seconds: Optional[float]
    api_cost: Optional[float]

    # Status
    success: bool
    error_message: Optional[str]
```

---

## Error Handling

All async methods can raise exceptions. Handle them appropriately:

```python
try:
    result = await orchestrator.run_complete_workflow(initial_spec="...")
except Exception as e:
    print(f"Workflow failed: {e}")
    # Check partial results
    if result.design_spec_path:
        print(f"Design was completed: {result.design_spec_path}")
```

---

## Next Steps

- **User Guide:** See [USER_GUIDE.md](USER_GUIDE.md)
- **Examples:** See [docs/examples/](examples/)
- **Troubleshooting:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**API Reference Version:** 2.0
**Last Updated:** January 2026
