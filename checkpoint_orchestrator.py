"""
Checkpoint Orchestration Engine
================================

Orchestrates checkpoint execution, result aggregation, and decision-making.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from checkpoint_config import get_config, AutocoderConfig


class CheckpointDecision(Enum):
    """Decision outcomes from checkpoint execution."""

    PAUSE = "PAUSE"  # Critical issues found, development should pause
    CONTINUE = "CONTINUE"  # All checks passed, continue development
    CONTINUE_WITH_WARNINGS = "CONTINUE_WITH_WARNINGS"  # Warnings found, but can continue


class IssueSeverity(Enum):
    """Severity levels for checkpoint issues."""

    CRITICAL = "critical"  # Must be fixed before continuing
    WARNING = "warning"  # Should be fixed, but not blocking
    INFO = "info"  # Informational, no action required


@dataclass
class CheckpointIssue:
    """Represents a single issue found during checkpoint."""

    severity: IssueSeverity
    checkpoint_type: str  # e.g., "code_review", "security_audit"
    title: str
    description: str
    location: Optional[str] = None  # File path or location
    suggestion: Optional[str] = None  # How to fix
    line_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'severity': self.severity.value,
            'checkpoint_type': self.checkpoint_type,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'suggestion': self.suggestion,
            'line_number': self.line_number
        }


@dataclass
class CheckpointResult:
    """Result from a single checkpoint agent."""

    checkpoint_type: str
    status: str  # "PASS", "PASS_WITH_WARNINGS", "FAIL"
    issues: List[CheckpointIssue] = field(default_factory=list)
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_critical_count(self) -> int:
        """Get count of critical issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.CRITICAL)

    def get_warning_count(self) -> int:
        """Get count of warnings."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.WARNING)

    def get_info_count(self) -> int:
        """Get count of info items."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.INFO)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'checkpoint_type': self.checkpoint_type,
            'status': self.status,
            'issues': [issue.to_dict() for issue in self.issues],
            'execution_time_ms': self.execution_time_ms,
            'metadata': self.metadata,
            'critical_count': self.get_critical_count(),
            'warning_count': self.get_warning_count(),
            'info_count': self.get_info_count()
        }


@dataclass
class AggregatedCheckpointResult:
    """Aggregated results from all checkpoint agents."""

    checkpoint_number: int
    features_completed: int
    timestamp: datetime
    decision: CheckpointDecision
    results: List[CheckpointResult] = field(default_factory=list)
    total_critical: int = 0
    total_warnings: int = 0
    total_info: int = 0
    total_execution_time_ms: float = 0.0

    @property
    def issues(self) -> List[CheckpointIssue]:
        """Get all issues from all checkpoint results."""
        all_issues = []
        for result in self.results:
            all_issues.extend(result.issues)
        return all_issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'checkpoint_number': self.checkpoint_number,
            'features_completed': self.features_completed,
            'timestamp': self.timestamp.isoformat(),
            'decision': self.decision.value,
            'results': [r.to_dict() for r in self.results],
            'total_critical': self.total_critical,
            'total_warnings': self.total_warnings,
            'total_info': self.total_info,
            'total_execution_time_ms': self.total_execution_time_ms
        }


class CheckpointOrchestrator:
    """Orchestrates checkpoint execution and decision-making."""

    def __init__(self, project_dir: Path, config: Optional[AutocoderConfig] = None):
        """
        Initialize the checkpoint orchestrator.

        Args:
            project_dir: Path to the project directory
            config: Optional configuration (will load from project if None)
        """
        self.project_dir = project_dir
        self.config = config or get_config(project_dir)
        self.checkpoint_counter = 0

    def should_run_checkpoint(
        self,
        features_completed: int,
        feature_name: str = ""
    ) -> bool:
        """
        Determine if checkpoint should run.

        This delegates to the configuration object.

        Args:
            features_completed: Number of features completed so far
            feature_name: Name of current/last completed feature

        Returns:
            True if checkpoint should run, False otherwise
        """
        return self.config.checkpoints.should_run_checkpoint(
            features_completed,
            feature_name
        )

    async def run_checkpoint(
        self,
        features_completed: int,
        feature_name: str = ""
    ) -> AggregatedCheckpointResult:
        """
        Run all enabled checkpoint agents in parallel.

        Args:
            features_completed: Number of features completed
            feature_name: Name of last completed feature

        Returns:
            Aggregated checkpoint result with decision
        """
        self.checkpoint_counter += 1

        print(f"\n🚧 CHECKPOINT #{self.checkpoint_counter}: {features_completed} features complete\n")

        # Get enabled checkpoints
        enabled_checkpoints = self.config.checkpoints.types.get_enabled()

        if not enabled_checkpoints:
            print("⚠️  No checkpoints enabled, skipping")
            return self._create_empty_result(features_completed)

        # Run all checkpoints in parallel
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*[
            self._run_checkpoint_agent(checkpoint_type)
            for checkpoint_type in enabled_checkpoints
        ], return_exceptions=True)
        end_time = asyncio.get_event_loop().time()
        total_time_ms = (end_time - start_time) * 1000

        # Filter out exceptions and convert to CheckpointResult objects
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                checkpoint_type = enabled_checkpoints[i]
                print(f"❌ Checkpoint '{checkpoint_type}' failed: {result}")
                # Create failed result
                valid_results.append(CheckpointResult(
                    checkpoint_type=checkpoint_type,
                    status="FAIL",
                    issues=[CheckpointIssue(
                        severity=IssueSeverity.CRITICAL,
                        checkpoint_type=checkpoint_type,
                        title="Checkpoint execution failed",
                        description=str(result)
                    )]
                ))
            else:
                valid_results.append(result)

        # Aggregate results
        aggregated = self._aggregate_results(
            valid_results,
            features_completed,
            total_time_ms
        )

        # Make decision
        decision = self._make_decision(aggregated)
        aggregated.decision = decision

        # Print summary
        self._print_summary(aggregated)

        return aggregated

    async def _run_checkpoint_agent(
        self,
        checkpoint_type: str
    ) -> CheckpointResult:
        """
        Run a single checkpoint agent.

        This is a placeholder that will be overridden or call actual agents.

        Args:
            checkpoint_type: Type of checkpoint to run

        Returns:
            CheckpointResult from the agent
        """
        print(f"🔍 Running {checkpoint_type} checkpoint...")

        # Simulate checkpoint execution
        await asyncio.sleep(0.1)  # Placeholder for actual agent execution

        # For now, return a placeholder result
        # Real implementation will invoke actual checkpoint agents
        return CheckpointResult(
            checkpoint_type=checkpoint_type,
            status="PASS",
            issues=[],
            execution_time_ms=100.0,
            metadata={'note': 'Placeholder implementation'}
        )

    def _aggregate_results(
        self,
        results: List[CheckpointResult],
        features_completed: int,
        total_time_ms: float
    ) -> AggregatedCheckpointResult:
        """
        Aggregate results from all checkpoint agents.

        Args:
            results: List of checkpoint results
            features_completed: Number of features completed
            total_time_ms: Total execution time in milliseconds

        Returns:
            Aggregated result
        """
        total_critical = sum(r.get_critical_count() for r in results)
        total_warnings = sum(r.get_warning_count() for r in results)
        total_info = sum(r.get_info_count() for r in results)

        return AggregatedCheckpointResult(
            checkpoint_number=self.checkpoint_counter,
            features_completed=features_completed,
            timestamp=datetime.now(),
            decision=CheckpointDecision.CONTINUE,  # Will be set by _make_decision
            results=results,
            total_critical=total_critical,
            total_warnings=total_warnings,
            total_info=total_info,
            total_execution_time_ms=total_time_ms
        )

    def _make_decision(
        self,
        aggregated: AggregatedCheckpointResult
    ) -> CheckpointDecision:
        """
        Make decision based on aggregated results.

        Args:
            aggregated: Aggregated checkpoint result

        Returns:
            Decision (PAUSE, CONTINUE, CONTINUE_WITH_WARNINGS)
        """
        # Check if we should auto-pause on critical issues
        if aggregated.total_critical > 0:
            if self.config.checkpoints.auto_pause_on_critical:
                return CheckpointDecision.PAUSE
            else:
                # Even if auto-pause disabled, still indicate critical issues
                return CheckpointDecision.CONTINUE_WITH_WARNINGS

        # Check for warnings
        if aggregated.total_warnings > 0:
            return CheckpointDecision.CONTINUE_WITH_WARNINGS

        # All clear
        return CheckpointDecision.CONTINUE

    def _create_empty_result(
        self,
        features_completed: int
    ) -> AggregatedCheckpointResult:
        """Create empty result when no checkpoints are enabled."""
        return AggregatedCheckpointResult(
            checkpoint_number=self.checkpoint_counter,
            features_completed=features_completed,
            timestamp=datetime.now(),
            decision=CheckpointDecision.CONTINUE,
            results=[],
            total_critical=0,
            total_warnings=0,
            total_info=0,
            total_execution_time_ms=0.0
        )

    def _print_summary(self, aggregated: AggregatedCheckpointResult) -> None:
        """
        Print checkpoint summary to console.

        Args:
            aggregated: Aggregated checkpoint result
        """
        print(f"\n{'='*60}")
        print(f"CHECKPOINT #{aggregated.checkpoint_number} SUMMARY")
        print(f"{'='*60}")
        print(f"Features Completed: {aggregated.features_completed}")
        print(f"Execution Time: {aggregated.total_execution_time_ms:.0f}ms")
        print()

        # Print per-checkpoint results
        for result in aggregated.results:
            status_emoji = {
                "PASS": "✅",
                "PASS_WITH_WARNINGS": "⚠️",
                "FAIL": "❌"
            }.get(result.status, "❓")

            print(f"{status_emoji} {result.checkpoint_type}: {result.status}")

            if result.issues:
                for issue in result.issues:
                    severity_emoji = {
                        IssueSeverity.CRITICAL: "🔴",
                        IssueSeverity.WARNING: "🟡",
                        IssueSeverity.INFO: "🔵"
                    }.get(issue.severity, "⚪")

                    print(f"  {severity_emoji} {issue.title}")
                    if issue.location:
                        print(f"     Location: {issue.location}")

        print()

        # Print totals
        if aggregated.total_critical > 0:
            print(f"🔴 Critical Issues: {aggregated.total_critical}")
        if aggregated.total_warnings > 0:
            print(f"🟡 Warnings: {aggregated.total_warnings}")
        if aggregated.total_info > 0:
            print(f"🔵 Info: {aggregated.total_info}")

        print()

        # Print decision
        decision_message = {
            CheckpointDecision.PAUSE: "❌ CRITICAL ISSUES - Pausing development",
            CheckpointDecision.CONTINUE_WITH_WARNINGS: f"⚠️  {aggregated.total_warnings} warnings - Continuing",
            CheckpointDecision.CONTINUE: "✅ All checks passed"
        }.get(aggregated.decision, "❓ Unknown decision")

        print(decision_message)
        print(f"{'='*60}\n")


# Convenience function for easy usage
async def run_checkpoint_if_needed(
    project_dir: Path,
    features_completed: int,
    feature_name: str = "",
    config: Optional[AutocoderConfig] = None
) -> Optional[AggregatedCheckpointResult]:
    """
    Run checkpoint if conditions are met.

    Args:
        project_dir: Path to project directory
        features_completed: Number of features completed
        feature_name: Name of last completed feature
        config: Optional configuration

    Returns:
        AggregatedCheckpointResult if checkpoint ran, None otherwise
    """
    orchestrator = CheckpointOrchestrator(project_dir, config)

    if orchestrator.should_run_checkpoint(features_completed, feature_name):
        return await orchestrator.run_checkpoint(features_completed, feature_name)

    return None
