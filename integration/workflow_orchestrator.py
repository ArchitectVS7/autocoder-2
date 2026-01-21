"""
Workflow Orchestrator for Phase 6: End-to-End Workflow Integration.

Connects all phases into a seamless workflow:
1. Design Iteration (Phase 4) - Pre-development design validation
2. Development with Checkpoints (Phases 1-3) - Code implementation with quality gates
3. UX Evaluation (Phase 5) - Post-development UX validation
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

# Phase imports
from design.iteration import DesignIterationAgent, DesignReviewPanel, DesignSynthesisAgent
from design.review import DesignReviewCLI
from checkpoint.orchestrator import CheckpointOrchestrator, run_checkpoint_if_needed
from checkpoint.config import CheckpointConfig
from ux_eval.playwright_generator import PlaywrightTestGenerator
from ux_eval.playwright_runner import PlaywrightTestRunner, run_ux_tests
from ux_eval.ux_evaluator import UXEvaluator
from metrics.collector import MetricsCollector
from metrics.report_generator import PerformanceReportGenerator


class WorkflowPhase(Enum):
    """Phases of the complete workflow."""
    DESIGN_ITERATION = "design_iteration"
    DEVELOPMENT = "development"
    CHECKPOINTS = "checkpoints"
    UX_EVALUATION = "ux_evaluation"
    COMPLETE = "complete"


@dataclass
class WorkflowConfig:
    """Configuration for the complete workflow."""

    # Phase toggles
    enable_design_iteration: bool = True
    enable_checkpoints: bool = True
    enable_ux_evaluation: bool = True
    enable_metrics: bool = True

    # Design iteration settings
    max_design_iterations: int = 4
    design_convergence_threshold: float = 0.8

    # Checkpoint settings (delegates to CheckpointConfig)
    checkpoint_frequency: int = 10
    auto_pause_on_critical: bool = True

    # UX evaluation settings
    run_ux_after_completion: bool = True
    ux_flows: List[str] = field(default_factory=lambda: ['onboarding', 'dashboard', 'settings'])
    min_ux_score: float = 7.0

    # Metrics settings
    track_performance: bool = True
    generate_comparison: bool = True

    # Output settings
    output_directory: Path = field(default_factory=lambda: Path('./autocoder_output'))
    verbose_logging: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'enable_design_iteration': self.enable_design_iteration,
            'enable_checkpoints': self.enable_checkpoints,
            'enable_ux_evaluation': self.enable_ux_evaluation,
            'enable_metrics': self.enable_metrics,
            'max_design_iterations': self.max_design_iterations,
            'design_convergence_threshold': self.design_convergence_threshold,
            'checkpoint_frequency': self.checkpoint_frequency,
            'auto_pause_on_critical': self.auto_pause_on_critical,
            'run_ux_after_completion': self.run_ux_after_completion,
            'ux_flows': self.ux_flows,
            'min_ux_score': self.min_ux_score,
            'track_performance': self.track_performance,
            'generate_comparison': self.generate_comparison,
            'output_directory': str(self.output_directory),
            'verbose_logging': self.verbose_logging
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'WorkflowConfig':
        """Create config from dictionary."""
        return WorkflowConfig(
            enable_design_iteration=data.get('enable_design_iteration', True),
            enable_checkpoints=data.get('enable_checkpoints', True),
            enable_ux_evaluation=data.get('enable_ux_evaluation', True),
            enable_metrics=data.get('enable_metrics', True),
            max_design_iterations=data.get('max_design_iterations', 4),
            design_convergence_threshold=data.get('design_convergence_threshold', 0.8),
            checkpoint_frequency=data.get('checkpoint_frequency', 10),
            auto_pause_on_critical=data.get('auto_pause_on_critical', True),
            run_ux_after_completion=data.get('run_ux_after_completion', True),
            ux_flows=data.get('ux_flows', ['onboarding', 'dashboard', 'settings']),
            min_ux_score=data.get('min_ux_score', 7.0),
            track_performance=data.get('track_performance', True),
            generate_comparison=data.get('generate_comparison', True),
            output_directory=Path(data.get('output_directory', './autocoder_output')),
            verbose_logging=data.get('verbose_logging', True)
        )


@dataclass
class WorkflowResult:
    """Result of running the complete workflow."""

    project_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    current_phase: WorkflowPhase = WorkflowPhase.DESIGN_ITERATION

    # Phase results
    design_spec_path: Optional[Path] = None
    design_iterations: int = 0

    development_complete: bool = False
    features_completed: int = 0
    features_total: int = 0

    checkpoints_run: int = 0
    critical_issues_found: int = 0

    ux_evaluation_complete: bool = False
    ux_score: Optional[float] = None
    ux_report_path: Optional[Path] = None

    # Metrics
    total_duration_seconds: Optional[float] = None
    api_cost: Optional[float] = None

    # Status
    success: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'project_name': self.project_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'current_phase': self.current_phase.value,
            'design_spec_path': str(self.design_spec_path) if self.design_spec_path else None,
            'design_iterations': self.design_iterations,
            'development_complete': self.development_complete,
            'features_completed': self.features_completed,
            'features_total': self.features_total,
            'checkpoints_run': self.checkpoints_run,
            'critical_issues_found': self.critical_issues_found,
            'ux_evaluation_complete': self.ux_evaluation_complete,
            'ux_score': self.ux_score,
            'ux_report_path': str(self.ux_report_path) if self.ux_report_path else None,
            'total_duration_seconds': self.total_duration_seconds,
            'api_cost': self.api_cost,
            'success': self.success,
            'error_message': self.error_message
        }


class WorkflowOrchestrator:
    """
    Orchestrates the complete workflow from design to UX evaluation.

    Phases:
    1. Design Iteration - Multi-persona design validation before coding
    2. Development - Feature implementation with checkpoints
    3. UX Evaluation - Automated UX testing and evaluation
    """

    def __init__(self, project_dir: Path, config: Optional[WorkflowConfig] = None):
        """
        Initialize the workflow orchestrator.

        Args:
            project_dir: Path to the project directory
            config: Workflow configuration (uses defaults if not provided)
        """
        self.project_dir = Path(project_dir)
        self.config = config or WorkflowConfig()

        # Ensure output directory exists
        self.output_dir = self.project_dir / self.config.output_directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize phase components
        self._init_design_phase()
        self._init_checkpoint_phase()
        self._init_ux_phase()
        self._init_metrics()

        # Workflow state
        self.result = WorkflowResult(
            project_name=self.project_dir.name,
            start_time=datetime.now()
        )

    def _init_design_phase(self):
        """Initialize design iteration components."""
        if self.config.enable_design_iteration:
            self.design_agent = DesignIterationAgent()
            self.design_review = DesignReviewPanel()
            self.design_synthesis = DesignSynthesisAgent()

    def _init_checkpoint_phase(self):
        """Initialize checkpoint components."""
        if self.config.enable_checkpoints:
            # Update checkpoint config
            checkpoint_config = CheckpointConfig.get_instance()
            checkpoint_config.enabled = True
            checkpoint_config.frequency = self.config.checkpoint_frequency
            checkpoint_config.auto_pause_on_critical = self.config.auto_pause_on_critical

            self.checkpoint_orchestrator = CheckpointOrchestrator(self.project_dir)

    def _init_ux_phase(self):
        """Initialize UX evaluation components."""
        if self.config.enable_ux_evaluation:
            self.playwright_generator = PlaywrightTestGenerator(self.project_dir)
            self.playwright_runner = PlaywrightTestRunner(self.project_dir)
            self.ux_evaluator = UXEvaluator(self.project_dir)

    def _init_metrics(self):
        """Initialize metrics collection."""
        if self.config.enable_metrics:
            self.metrics_collector = MetricsCollector(self.project_dir.name)
            self.report_generator = PerformanceReportGenerator(self.project_dir)

    async def run_design_iteration(self, initial_spec: str) -> Optional[Path]:
        """
        Run design iteration phase.

        Args:
            initial_spec: Initial design specification

        Returns:
            Path to final design spec, or None if skipped/failed
        """
        if not self.config.enable_design_iteration:
            self._log("Design iteration disabled, skipping...")
            return None

        self._log("=" * 60)
        self._log("PHASE 1: DESIGN ITERATION")
        self._log("=" * 60)

        self.result.current_phase = WorkflowPhase.DESIGN_ITERATION

        try:
            # Create CLI for design review
            cli = DesignReviewCLI(self.project_dir)

            # Run design review (auto mode)
            final_design_path = cli.run_auto_mode(
                initial_spec=initial_spec,
                max_iterations=self.config.max_design_iterations,
                convergence_threshold=self.config.design_convergence_threshold
            )

            self.result.design_spec_path = final_design_path
            self.result.design_iterations = cli.iteration_count if hasattr(cli, 'iteration_count') else 0

            self._log(f"✅ Design iteration complete after {self.result.design_iterations} iterations")
            self._log(f"   Final spec saved to: {final_design_path}")

            return final_design_path

        except Exception as e:
            self._log(f"❌ Design iteration failed: {e}")
            self.result.error_message = f"Design iteration failed: {e}"
            return None

    async def run_development_with_checkpoints(
        self,
        features_total: int,
        on_checkpoint: Optional[callable] = None
    ) -> bool:
        """
        Run development phase with checkpoints.

        Args:
            features_total: Total number of features to implement
            on_checkpoint: Optional callback when checkpoint runs

        Returns:
            True if development completed successfully
        """
        self._log("=" * 60)
        self._log("PHASE 2: DEVELOPMENT WITH CHECKPOINTS")
        self._log("=" * 60)

        self.result.current_phase = WorkflowPhase.DEVELOPMENT
        self.result.features_total = features_total

        try:
            # Note: Actual development loop happens in autonomous_agent_demo.py
            # This orchestrator integrates with existing development flow

            # Checkpoints are triggered via run_checkpoint_if_needed()
            # during development (called from agent.py or autonomous_agent_demo.py)

            self._log("Development and checkpoint integration ready")
            self._log(f"Checkpoints will run every {self.config.checkpoint_frequency} features")

            return True

        except Exception as e:
            self._log(f"❌ Development setup failed: {e}")
            self.result.error_message = f"Development setup failed: {e}"
            return False

    async def run_ux_evaluation(self, app_url: str = "http://localhost:3000") -> Optional[float]:
        """
        Run UX evaluation phase.

        Args:
            app_url: URL of the running application

        Returns:
            Overall UX score, or None if failed
        """
        if not self.config.enable_ux_evaluation:
            self._log("UX evaluation disabled, skipping...")
            return None

        self._log("=" * 60)
        self._log("PHASE 3: UX EVALUATION")
        self._log("=" * 60)

        self.result.current_phase = WorkflowPhase.UX_EVALUATION

        try:
            # 1. Generate Playwright tests
            self._log("Generating Playwright tests...")
            for flow_name in self.config.ux_flows:
                test_path = self.playwright_generator.save_test(
                    self.playwright_generator.create_flow(flow_name)
                )
                self._log(f"   ✓ Generated test for: {flow_name}")

            # 2. Run Playwright tests
            self._log("Running Playwright tests...")
            test_result = await run_ux_tests(self.project_dir, app_url)

            if not test_result.success:
                self._log(f"⚠️  Some tests failed: {test_result.failed}/{test_result.total}")
            else:
                self._log(f"✅ All tests passed: {test_result.passed}/{test_result.total}")

            # 3. Run UX evaluation
            self._log("Evaluating UX from screenshots...")
            ux_result = await self.ux_evaluator.evaluate(app_url)

            overall_score = ux_result.overall_score
            self.result.ux_score = overall_score
            self.result.ux_evaluation_complete = True

            # 4. Generate final report
            self._log("Generating final UX report...")
            final_report = self.ux_evaluator.generate_final_report(ux_result)

            report_path = self.output_dir / "UX_REPORT_FINAL.md"
            self.ux_evaluator.save_report(final_report, report_path)
            self.result.ux_report_path = report_path

            # Check if meets minimum score
            if overall_score >= self.config.min_ux_score:
                self._log(f"✅ UX evaluation passed: {overall_score:.1f}/10 (min: {self.config.min_ux_score})")
            else:
                self._log(f"⚠️  UX score below threshold: {overall_score:.1f}/10 (min: {self.config.min_ux_score})")

            self._log(f"   Report saved to: {report_path}")

            return overall_score

        except Exception as e:
            self._log(f"❌ UX evaluation failed: {e}")
            self.result.error_message = f"UX evaluation failed: {e}"
            return None

    async def run_complete_workflow(
        self,
        initial_spec: Optional[str] = None,
        app_url: str = "http://localhost:3000"
    ) -> WorkflowResult:
        """
        Run the complete workflow from design to UX evaluation.

        Args:
            initial_spec: Initial design specification (for design iteration phase)
            app_url: URL of the running application (for UX evaluation)

        Returns:
            WorkflowResult with complete status
        """
        self._log("🚀 Starting complete autocoder workflow")
        self._log(f"   Project: {self.project_dir.name}")
        self._log(f"   Output: {self.output_dir}")

        try:
            # Phase 1: Design Iteration (optional)
            if self.config.enable_design_iteration and initial_spec:
                design_spec = await self.run_design_iteration(initial_spec)
                if not design_spec:
                    self._log("⚠️  Design iteration failed, but continuing...")

            # Phase 2: Development with Checkpoints
            # Note: This is handled by autonomous_agent_demo.py
            # The orchestrator just sets up the configuration
            dev_ready = await self.run_development_with_checkpoints(
                features_total=0  # Will be set by agent
            )

            if not dev_ready:
                raise Exception("Development setup failed")

            # Phase 3: UX Evaluation (runs after development completes)
            if self.config.run_ux_after_completion:
                ux_score = await self.run_ux_evaluation(app_url)
                if ux_score is None:
                    self._log("⚠️  UX evaluation failed, but workflow complete")

            # Mark workflow as complete
            self.result.current_phase = WorkflowPhase.COMPLETE
            self.result.success = True
            self.result.end_time = datetime.now()
            self.result.total_duration_seconds = (
                self.result.end_time - self.result.start_time
            ).total_seconds()

            self._log("=" * 60)
            self._log("✅ WORKFLOW COMPLETE")
            self._log("=" * 60)
            self._log(f"   Duration: {self.result.total_duration_seconds:.1f}s")
            if self.result.ux_score:
                self._log(f"   UX Score: {self.result.ux_score:.1f}/10")

            return self.result

        except Exception as e:
            self._log(f"❌ Workflow failed: {e}")
            self.result.error_message = str(e)
            self.result.success = False
            self.result.end_time = datetime.now()
            return self.result

    def update_development_progress(self, features_completed: int):
        """
        Update development progress.

        Args:
            features_completed: Number of features completed
        """
        self.result.features_completed = features_completed

        if self.config.verbose_logging:
            progress = (features_completed / self.result.features_total * 100) if self.result.features_total > 0 else 0
            self._log(f"📊 Progress: {features_completed}/{self.result.features_total} features ({progress:.1f}%)")

    def record_checkpoint(self, critical_issues: int):
        """
        Record checkpoint execution.

        Args:
            critical_issues: Number of critical issues found
        """
        self.result.checkpoints_run += 1
        self.result.critical_issues_found += critical_issues

        if critical_issues > 0:
            self._log(f"⚠️  Checkpoint {self.result.checkpoints_run}: {critical_issues} critical issues found")
        else:
            self._log(f"✅ Checkpoint {self.result.checkpoints_run}: All clear")

    def _log(self, message: str):
        """Log message if verbose logging enabled."""
        if self.config.verbose_logging:
            print(message)


# Convenience function
async def run_complete_workflow(
    project_dir: Path,
    initial_spec: Optional[str] = None,
    config: Optional[WorkflowConfig] = None
) -> WorkflowResult:
    """
    Convenience function to run complete workflow.

    Args:
        project_dir: Path to project directory
        initial_spec: Initial design specification
        config: Workflow configuration

    Returns:
        WorkflowResult with complete status
    """
    orchestrator = WorkflowOrchestrator(project_dir, config)
    return await orchestrator.run_complete_workflow(initial_spec)
