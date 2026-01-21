#!/usr/bin/env python3
"""
Phase 3 Checkpoint System Tests
================================

Tests for the checkpoint configuration, orchestration, and agents.

Run with: pytest tests/test_phase3_checkpoints.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from checkpoint_config import (
    AutocoderConfig,
    CheckpointConfig,
    CheckpointTypes,
    CheckpointTrigger,
    get_config,
    set_config,
    reset_config
)
from checkpoint_orchestrator import (
    CheckpointOrchestrator,
    CheckpointDecision,
    CheckpointResult,
    CheckpointIssue,
    IssueSeverity,
    AggregatedCheckpointResult,
    run_checkpoint_if_needed
)
from checkpoint_report_writer import CheckpointReportWriter
from datetime import datetime as dt


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset config singleton between tests."""
    reset_config()
    yield
    reset_config()


# =============================================================================
# Task 3.1.1: autocoder_config.yaml Support
# =============================================================================

class TestConfigLoader:
    """Test configuration loading from YAML files."""

    def test_load_default_config_when_file_missing(self, temp_project_dir):
        """Should return default config when file doesn't exist."""
        config = AutocoderConfig.load_from_project(temp_project_dir)

        assert config.checkpoints.enabled is True
        assert config.checkpoints.frequency == 10
        assert config.checkpoints.types.code_review is True
        assert config.checkpoints.types.security_audit is True
        assert config.checkpoints.types.performance_check is True
        assert config.checkpoints.types.accessibility_check is False

    def test_load_config_from_yaml(self, temp_project_dir):
        """Should load configuration from YAML file."""
        config_file = temp_project_dir / 'autocoder_config.yaml'
        config_file.write_text("""
checkpoints:
  enabled: true
  frequency: 5
  types:
    code_review: true
    security_audit: false
    performance_check: true
    accessibility_check: true
  auto_pause_on_critical: false
output_directory: ./custom_output
verbose_logging: false
""")

        config = AutocoderConfig.load_from_project(temp_project_dir)

        assert config.checkpoints.enabled is True
        assert config.checkpoints.frequency == 5
        assert config.checkpoints.types.code_review is True
        assert config.checkpoints.types.security_audit is False
        assert config.checkpoints.types.performance_check is True
        assert config.checkpoints.types.accessibility_check is True
        assert config.checkpoints.auto_pause_on_critical is False
        assert config.output_directory == './custom_output'
        assert config.verbose_logging is False

    def test_load_empty_yaml_returns_defaults(self, temp_project_dir):
        """Should return defaults when YAML file is empty."""
        config_file = temp_project_dir / 'autocoder_config.yaml'
        config_file.write_text("")

        config = AutocoderConfig.load_from_project(temp_project_dir)

        assert config.checkpoints.enabled is True
        assert config.checkpoints.frequency == 10

    def test_load_partial_config(self, temp_project_dir):
        """Should merge partial config with defaults."""
        config_file = temp_project_dir / 'autocoder_config.yaml'
        config_file.write_text("""
checkpoints:
  frequency: 15
""")

        config = AutocoderConfig.load_from_project(temp_project_dir)

        # Override value
        assert config.checkpoints.frequency == 15

        # Default values
        assert config.checkpoints.enabled is True
        assert config.checkpoints.types.code_review is True

    def test_save_and_load_roundtrip(self, temp_project_dir):
        """Should preserve all settings in save/load cycle."""
        config_file = temp_project_dir / 'autocoder_config.yaml'

        # Create custom config
        original = AutocoderConfig(
            checkpoints=CheckpointConfig(
                enabled=True,
                frequency=7,
                types=CheckpointTypes(
                    code_review=False,
                    security_audit=True,
                    performance_check=False,
                    accessibility_check=True
                ),
                auto_pause_on_critical=False,
                triggers=[
                    CheckpointTrigger(feature_count=20),
                    CheckpointTrigger(milestone="authentication")
                ]
            ),
            output_directory="./test_output",
            verbose_logging=False
        )

        # Save
        original.save(config_file)

        # Load
        loaded = AutocoderConfig.load(config_file)

        # Verify
        assert loaded.checkpoints.enabled == original.checkpoints.enabled
        assert loaded.checkpoints.frequency == original.checkpoints.frequency
        assert loaded.checkpoints.types.code_review == original.checkpoints.types.code_review
        assert loaded.checkpoints.types.security_audit == original.checkpoints.types.security_audit
        assert loaded.checkpoints.types.performance_check == original.checkpoints.types.performance_check
        assert loaded.checkpoints.types.accessibility_check == original.checkpoints.types.accessibility_check
        assert loaded.checkpoints.auto_pause_on_critical == original.checkpoints.auto_pause_on_critical
        assert len(loaded.checkpoints.triggers) == 2
        assert loaded.output_directory == original.output_directory
        assert loaded.verbose_logging == original.verbose_logging


# =============================================================================
# Task 3.1.2: Checkpoint Frequency Settings
# =============================================================================

class TestCheckpointFrequency:
    """Test checkpoint frequency and trigger logic."""

    def test_should_run_checkpoint_at_frequency_intervals(self):
        """Should trigger checkpoint every N features."""
        config = CheckpointConfig(enabled=True, frequency=10)

        assert config.should_run_checkpoint(features_completed=0) is False
        assert config.should_run_checkpoint(features_completed=5) is False
        assert config.should_run_checkpoint(features_completed=10) is True
        assert config.should_run_checkpoint(features_completed=15) is False
        assert config.should_run_checkpoint(features_completed=20) is True
        assert config.should_run_checkpoint(features_completed=30) is True

    def test_should_not_run_when_disabled(self):
        """Should never trigger when checkpoints disabled."""
        config = CheckpointConfig(enabled=False, frequency=10)

        assert config.should_run_checkpoint(features_completed=10) is False
        assert config.should_run_checkpoint(features_completed=20) is False

    def test_different_frequency_values(self):
        """Should respect different frequency settings."""
        config = CheckpointConfig(enabled=True, frequency=5)

        assert config.should_run_checkpoint(features_completed=5) is True
        assert config.should_run_checkpoint(features_completed=10) is True
        assert config.should_run_checkpoint(features_completed=15) is True

        config = CheckpointConfig(enabled=True, frequency=25)

        assert config.should_run_checkpoint(features_completed=25) is True
        assert config.should_run_checkpoint(features_completed=50) is True
        assert config.should_run_checkpoint(features_completed=30) is False


# =============================================================================
# Task 3.1.3: Enable/Disable Checkpoint Types
# =============================================================================

class TestCheckpointTypes:
    """Test enabling and disabling specific checkpoint types."""

    def test_get_enabled_checkpoint_types(self):
        """Should return list of enabled checkpoint types."""
        types = CheckpointTypes(
            code_review=True,
            security_audit=True,
            performance_check=False,
            accessibility_check=True
        )

        enabled = types.get_enabled()

        assert 'code_review' in enabled
        assert 'security_audit' in enabled
        assert 'accessibility_check' in enabled
        assert 'performance_check' not in enabled
        assert len(enabled) == 3

    def test_all_checkpoints_enabled(self):
        """Should include all types when all enabled."""
        types = CheckpointTypes(
            code_review=True,
            security_audit=True,
            performance_check=True,
            accessibility_check=True
        )

        enabled = types.get_enabled()

        assert len(enabled) == 4
        assert 'code_review' in enabled
        assert 'security_audit' in enabled
        assert 'performance_check' in enabled
        assert 'accessibility_check' in enabled

    def test_no_checkpoints_enabled(self):
        """Should return empty list when all disabled."""
        types = CheckpointTypes(
            code_review=False,
            security_audit=False,
            performance_check=False,
            accessibility_check=False
        )

        enabled = types.get_enabled()

        assert len(enabled) == 0

    def test_default_checkpoint_types(self):
        """Should have sensible defaults."""
        types = CheckpointTypes()

        enabled = types.get_enabled()

        # Code review, security, and performance enabled by default
        assert 'code_review' in enabled
        assert 'security_audit' in enabled
        assert 'performance_check' in enabled

        # Accessibility check disabled by default (more specialized)
        assert 'accessibility_check' not in enabled


# =============================================================================
# Task 3.1.4: Manual Checkpoint Trigger
# =============================================================================

class TestCheckpointTriggers:
    """Test custom checkpoint triggers."""

    def test_feature_count_trigger(self):
        """Should trigger at specific feature counts."""
        trigger = CheckpointTrigger(feature_count=15)

        assert trigger.matches(features_completed=10, feature_name="Test") is False
        assert trigger.matches(features_completed=15, feature_name="Test") is True
        assert trigger.matches(features_completed=20, feature_name="Test") is False

    def test_milestone_trigger(self):
        """Should trigger based on feature milestone keywords."""
        trigger = CheckpointTrigger(milestone="authentication")

        assert trigger.matches(features_completed=5, feature_name="User login") is False
        assert trigger.matches(features_completed=8, feature_name="OAuth authentication") is True
        assert trigger.matches(features_completed=8, feature_name="Authentication system") is True
        assert trigger.matches(features_completed=12, feature_name="Dashboard layout") is False

    def test_milestone_case_insensitive(self):
        """Should match milestones case-insensitively."""
        trigger = CheckpointTrigger(milestone="Payment")

        assert trigger.matches(features_completed=10, feature_name="payment gateway") is True
        assert trigger.matches(features_completed=10, feature_name="PAYMENT processing") is True
        assert trigger.matches(features_completed=10, feature_name="Stripe payment") is True

    def test_multiple_custom_triggers(self):
        """Should support multiple custom triggers."""
        config = CheckpointConfig(
            enabled=True,
            frequency=10,  # Regular frequency
            triggers=[
                CheckpointTrigger(feature_count=5),  # Early checkpoint
                CheckpointTrigger(feature_count=15),  # Mid checkpoint
                CheckpointTrigger(milestone="authentication"),
                CheckpointTrigger(milestone="payments")
            ]
        )

        # Frequency-based triggers
        assert config.should_run_checkpoint(features_completed=10) is True
        assert config.should_run_checkpoint(features_completed=20) is True

        # Custom count triggers
        assert config.should_run_checkpoint(features_completed=5) is True
        assert config.should_run_checkpoint(features_completed=15) is True

        # Milestone triggers
        assert config.should_run_checkpoint(
            features_completed=8,
            feature_name="OAuth authentication"
        ) is True
        assert config.should_run_checkpoint(
            features_completed=12,
            feature_name="Payment processing"
        ) is True

        # No trigger
        assert config.should_run_checkpoint(features_completed=7) is False


# =============================================================================
# Task 3.1.5: Auto-Pause on Critical Issues
# =============================================================================

class TestAutoPauseConfiguration:
    """Test auto-pause configuration."""

    def test_auto_pause_enabled_by_default(self):
        """Should enable auto-pause by default."""
        config = CheckpointConfig()

        assert config.auto_pause_on_critical is True

    def test_auto_pause_can_be_disabled(self):
        """Should allow disabling auto-pause."""
        config = CheckpointConfig(auto_pause_on_critical=False)

        assert config.auto_pause_on_critical is False

    def test_auto_pause_setting_persists(self, temp_project_dir):
        """Should save and load auto-pause setting."""
        config_file = temp_project_dir / 'autocoder_config.yaml'

        config = AutocoderConfig(
            checkpoints=CheckpointConfig(auto_pause_on_critical=False)
        )
        config.save(config_file)

        loaded = AutocoderConfig.load(config_file)

        assert loaded.checkpoints.auto_pause_on_critical is False


# =============================================================================
# Singleton Configuration Access
# =============================================================================

class TestConfigSingleton:
    """Test singleton configuration access pattern."""

    def test_get_config_returns_default_on_first_call(self):
        """Should return default config on first call."""
        config = get_config()

        assert config is not None
        assert config.checkpoints.enabled is True

    def test_get_config_returns_same_instance(self):
        """Should return same instance on subsequent calls."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_set_config_changes_singleton(self):
        """Should allow setting custom config."""
        custom = AutocoderConfig(
            checkpoints=CheckpointConfig(frequency=5)
        )

        set_config(custom)

        config = get_config()

        assert config.checkpoints.frequency == 5

    def test_reset_config_clears_singleton(self):
        """Should clear singleton on reset."""
        # Get config
        config1 = get_config()

        # Reset
        reset_config()

        # Get again
        config2 = get_config()

        # Should be new instance
        assert config1 is not config2


# =============================================================================
# Integration Tests
# =============================================================================

class TestCheckpointConfigIntegration:
    """Integration tests for checkpoint configuration system."""

    def test_complete_workflow(self, temp_project_dir):
        """Test complete config workflow: create, save, load, use."""
        config_file = temp_project_dir / 'autocoder_config.yaml'

        # Create custom configuration
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(
                enabled=True,
                frequency=8,
                types=CheckpointTypes(
                    code_review=True,
                    security_audit=True,
                    performance_check=False,
                    accessibility_check=True
                ),
                triggers=[
                    CheckpointTrigger(feature_count=5),
                    CheckpointTrigger(milestone="security")
                ]
            )
        )

        # Save to file
        config.save(config_file)

        # Verify file exists
        assert config_file.exists()

        # Load from file
        loaded = AutocoderConfig.load_from_project(temp_project_dir)

        # Use configuration
        assert loaded.checkpoints.should_run_checkpoint(features_completed=8) is True
        assert loaded.checkpoints.should_run_checkpoint(features_completed=5) is True
        assert loaded.checkpoints.should_run_checkpoint(
            features_completed=10,
            feature_name="Security audit"
        ) is True

        enabled_types = loaded.checkpoints.types.get_enabled()
        assert len(enabled_types) == 3
        assert 'performance_check' not in enabled_types

    def test_config_with_real_yaml_content(self, temp_project_dir):
        """Test with realistic YAML configuration."""
        config_file = temp_project_dir / 'autocoder_config.yaml'
        config_file.write_text("""
# Autocoder Configuration
# =======================

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
    - milestone: "authentication"
    - milestone: "payments"

output_directory: ./autocoder_output
verbose_logging: true
""")

        config = AutocoderConfig.load_from_project(temp_project_dir)

        assert config.checkpoints.frequency == 10
        assert len(config.checkpoints.triggers) == 5

        # Test triggers work
        assert config.checkpoints.should_run_checkpoint(features_completed=10) is True
        assert config.checkpoints.should_run_checkpoint(features_completed=50) is True
        assert config.checkpoints.should_run_checkpoint(
            features_completed=15,
            feature_name="OAuth authentication setup"
        ) is True


# =============================================================================
# Task 3.2: Checkpoint Orchestration Engine
# =============================================================================


class TestCheckpointOrchestrator:
    """Test checkpoint orchestration engine."""

    def test_should_run_checkpoint_delegates_to_config(self, temp_project_dir):
        """Should delegate checkpoint detection to configuration."""
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(enabled=True, frequency=10)
        )

        orchestrator = CheckpointOrchestrator(temp_project_dir, config)

        assert orchestrator.should_run_checkpoint(features_completed=10) is True
        assert orchestrator.should_run_checkpoint(features_completed=5) is False
        assert orchestrator.should_run_checkpoint(features_completed=20) is True

    @pytest.mark.asyncio
    async def test_run_checkpoint_executes_enabled_checkpoints(self, temp_project_dir):
        """Should run all enabled checkpoint agents."""
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(
                enabled=True,
                frequency=10,
                types=CheckpointTypes(
                    code_review=True,
                    security_audit=True,
                    performance_check=False,
                    accessibility_check=False
                )
            )
        )

        orchestrator = CheckpointOrchestrator(temp_project_dir, config)
        result = await orchestrator.run_checkpoint(features_completed=10)

        # Should have results for enabled checkpoints only
        assert len(result.results) == 2
        checkpoint_types = [r.checkpoint_type for r in result.results]
        assert 'code_review' in checkpoint_types
        assert 'security_audit' in checkpoint_types
        assert 'performance_check' not in checkpoint_types

    @pytest.mark.asyncio
    async def test_run_checkpoint_when_no_checkpoints_enabled(self, temp_project_dir):
        """Should handle case when no checkpoints enabled."""
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(
                enabled=True,
                types=CheckpointTypes(
                    code_review=False,
                    security_audit=False,
                    performance_check=False,
                    accessibility_check=False
                )
            )
        )

        orchestrator = CheckpointOrchestrator(temp_project_dir, config)
        result = await orchestrator.run_checkpoint(features_completed=10)

        assert len(result.results) == 0
        assert result.decision == CheckpointDecision.CONTINUE


class TestResultAggregation:
    """Test checkpoint result aggregation."""

    @pytest.mark.asyncio
    async def test_aggregate_results_counts_issues(self, temp_project_dir):
        """Should correctly count issues by severity."""
        config = AutocoderConfig()
        orchestrator = CheckpointOrchestrator(temp_project_dir, config)

        # Mock some results
        results = [
            CheckpointResult(
                checkpoint_type='code_review',
                status='PASS_WITH_WARNINGS',
                issues=[
                    CheckpointIssue(
                        severity=IssueSeverity.WARNING,
                        checkpoint_type='code_review',
                        title='Duplicated code',
                        description='Found duplicate logic'
                    ),
                    CheckpointIssue(
                        severity=IssueSeverity.INFO,
                        checkpoint_type='code_review',
                        title='Good naming',
                        description='Naming conventions followed'
                    )
                ]
            ),
            CheckpointResult(
                checkpoint_type='security_audit',
                status='FAIL',
                issues=[
                    CheckpointIssue(
                        severity=IssueSeverity.CRITICAL,
                        checkpoint_type='security_audit',
                        title='SQL Injection',
                        description='Unescaped user input'
                    )
                ]
            )
        ]

        aggregated = orchestrator._aggregate_results(results, 10, 500.0)

        assert aggregated.total_critical == 1
        assert aggregated.total_warnings == 1
        assert aggregated.total_info == 1
        assert aggregated.features_completed == 10

    @pytest.mark.asyncio
    async def test_aggregate_empty_results(self, temp_project_dir):
        """Should handle empty results list."""
        config = AutocoderConfig()
        orchestrator = CheckpointOrchestrator(temp_project_dir, config)

        aggregated = orchestrator._aggregate_results([], 5, 0.0)

        assert aggregated.total_critical == 0
        assert aggregated.total_warnings == 0
        assert aggregated.total_info == 0


class TestDecisionLogic:
    """Test checkpoint decision-making logic."""

    def test_decision_pause_on_critical_issues(self, temp_project_dir):
        """Should pause when critical issues found and auto-pause enabled."""
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(auto_pause_on_critical=True)
        )
        orchestrator = CheckpointOrchestrator(temp_project_dir, config)

        aggregated = orchestrator._aggregate_results(
            [CheckpointResult(
                checkpoint_type='security_audit',
                status='FAIL',
                issues=[
                    CheckpointIssue(
                        severity=IssueSeverity.CRITICAL,
                        checkpoint_type='security_audit',
                        title='Critical security flaw',
                        description='Must fix immediately'
                    )
                ]
            )],
            10,
            100.0
        )

        decision = orchestrator._make_decision(aggregated)

        assert decision == CheckpointDecision.PAUSE

    def test_decision_continue_with_warnings_when_auto_pause_disabled(self, temp_project_dir):
        """Should continue with warnings when auto-pause disabled even with critical issues."""
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(auto_pause_on_critical=False)
        )
        orchestrator = CheckpointOrchestrator(temp_project_dir, config)

        aggregated = orchestrator._aggregate_results(
            [CheckpointResult(
                checkpoint_type='security_audit',
                status='FAIL',
                issues=[
                    CheckpointIssue(
                        severity=IssueSeverity.CRITICAL,
                        checkpoint_type='security_audit',
                        title='Issue',
                        description='Description'
                    )
                ]
            )],
            10,
            100.0
        )

        decision = orchestrator._make_decision(aggregated)

        assert decision == CheckpointDecision.CONTINUE_WITH_WARNINGS

    def test_decision_continue_with_warnings_on_warnings(self, temp_project_dir):
        """Should continue with warnings when only warnings present."""
        config = AutocoderConfig()
        orchestrator = CheckpointOrchestrator(temp_project_dir, config)

        aggregated = orchestrator._aggregate_results(
            [CheckpointResult(
                checkpoint_type='code_review',
                status='PASS_WITH_WARNINGS',
                issues=[
                    CheckpointIssue(
                        severity=IssueSeverity.WARNING,
                        checkpoint_type='code_review',
                        title='Minor issue',
                        description='Could be improved'
                    )
                ]
            )],
            10,
            100.0
        )

        decision = orchestrator._make_decision(aggregated)

        assert decision == CheckpointDecision.CONTINUE_WITH_WARNINGS

    def test_decision_continue_when_all_clear(self, temp_project_dir):
        """Should continue when no issues found."""
        config = AutocoderConfig()
        orchestrator = CheckpointOrchestrator(temp_project_dir, config)

        aggregated = orchestrator._aggregate_results(
            [CheckpointResult(
                checkpoint_type='code_review',
                status='PASS',
                issues=[]
            )],
            10,
            100.0
        )

        decision = orchestrator._make_decision(aggregated)

        assert decision == CheckpointDecision.CONTINUE


class TestConvenienceFunction:
    """Test convenience function for checkpoint execution."""

    @pytest.mark.asyncio
    async def test_run_checkpoint_if_needed_runs_when_conditions_met(self, temp_project_dir):
        """Should run checkpoint when conditions are met."""
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(enabled=True, frequency=10)
        )

        result = await run_checkpoint_if_needed(
            temp_project_dir,
            features_completed=10,
            config=config
        )

        assert result is not None
        assert result.features_completed == 10
        assert result.checkpoint_number == 1

    @pytest.mark.asyncio
    async def test_run_checkpoint_if_needed_skips_when_not_needed(self, temp_project_dir):
        """Should return None when checkpoint not needed."""
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(enabled=True, frequency=10)
        )

        result = await run_checkpoint_if_needed(
            temp_project_dir,
            features_completed=5,
            config=config
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_run_checkpoint_if_needed_with_milestone_trigger(self, temp_project_dir):
        """Should run checkpoint on milestone trigger."""
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(
                enabled=True,
                frequency=100,  # High frequency, won't trigger
                triggers=[CheckpointTrigger(milestone="authentication")]
            )
        )

        result = await run_checkpoint_if_needed(
            temp_project_dir,
            features_completed=5,
            feature_name="OAuth authentication",
            config=config
        )

        assert result is not None
        assert result.checkpoint_number == 1


class TestCheckpointCounter:
    """Test checkpoint numbering."""

    @pytest.mark.asyncio
    async def test_checkpoint_counter_increments(self, temp_project_dir):
        """Should increment checkpoint counter on each run."""
        config = AutocoderConfig()
        orchestrator = CheckpointOrchestrator(temp_project_dir, config)

        result1 = await orchestrator.run_checkpoint(features_completed=10)
        result2 = await orchestrator.run_checkpoint(features_completed=20)
        result3 = await orchestrator.run_checkpoint(features_completed=30)

        assert result1.checkpoint_number == 1
        assert result2.checkpoint_number == 2
        assert result3.checkpoint_number == 3


# =============================================================================
# Task 3.3: Checkpoint Report Storage
# =============================================================================


class TestCheckpointReportWriter:
    """Test checkpoint report writing to disk."""

    def test_save_report_creates_markdown_file(self, temp_project_dir):
        """Should create markdown file in checkpoints/ directory."""
        writer = CheckpointReportWriter(temp_project_dir)

        # Create a sample result
        result = AggregatedCheckpointResult(
            checkpoint_number=1,
            features_completed=10,
            timestamp=dt.now(),
            decision=CheckpointDecision.CONTINUE,
            results=[],
            total_critical=0,
            total_warnings=0,
            total_info=0,
            total_execution_time_ms=100.0
        )

        filepath = writer.save_report(result)

        assert filepath.exists()
        assert filepath.parent.name == "checkpoints"
        assert filepath.name == "checkpoint_01_10_features.md"

    def test_generate_filename_format(self, temp_project_dir):
        """Should generate correctly formatted filenames."""
        writer = CheckpointReportWriter(temp_project_dir)

        result1 = AggregatedCheckpointResult(
            checkpoint_number=1,
            features_completed=10,
            timestamp=dt.now(),
            decision=CheckpointDecision.CONTINUE
        )

        result2 = AggregatedCheckpointResult(
            checkpoint_number=15,
            features_completed=150,
            timestamp=dt.now(),
            decision=CheckpointDecision.CONTINUE
        )

        assert writer._generate_filename(result1) == "checkpoint_01_10_features.md"
        assert writer._generate_filename(result2) == "checkpoint_15_150_features.md"

    def test_markdown_includes_all_sections(self, temp_project_dir):
        """Should include all required sections in markdown."""
        writer = CheckpointReportWriter(temp_project_dir)

        result = AggregatedCheckpointResult(
            checkpoint_number=1,
            features_completed=10,
            timestamp=dt.now(),
            decision=CheckpointDecision.CONTINUE_WITH_WARNINGS,
            results=[
                CheckpointResult(
                    checkpoint_type='code_review',
                    status='PASS_WITH_WARNINGS',
                    issues=[
                        CheckpointIssue(
                            severity=IssueSeverity.WARNING,
                            checkpoint_type='code_review',
                            title='Test Warning',
                            description='This is a test warning',
                            location='test.py',
                            line_number=42,
                            suggestion='Fix this'
                        )
                    ],
                    execution_time_ms=50.0
                )
            ],
            total_critical=0,
            total_warnings=1,
            total_info=0,
            total_execution_time_ms=100.0
        )

        markdown = writer._generate_markdown(result, "Test Feature")

        # Check for key sections
        assert "# Checkpoint #1" in markdown
        assert "**Features Completed:** 10" in markdown
        assert "**Last Feature:** Test Feature" in markdown
        assert "## Decision:" in markdown
        assert "CONTINUE_WITH_WARNINGS" in markdown
        assert "## Summary" in markdown
        assert "**Critical Issues:** 0" in markdown
        assert "**Warnings:** 1" in markdown
        assert "## Checkpoint Results" in markdown
        assert "### ⚠️ code_review" in markdown
        assert "##### 🟡 Warnings" in markdown
        assert "**Test Warning**" in markdown
        assert "This is a test warning" in markdown
        assert "*Location:* `test.py`" in markdown
        assert "(Line 42)" in markdown
        assert "*Suggestion:* Fix this" in markdown

    def test_markdown_pause_decision_includes_action_required(self, temp_project_dir):
        """Should include action required section for PAUSE decision."""
        writer = CheckpointReportWriter(temp_project_dir)

        result = AggregatedCheckpointResult(
            checkpoint_number=1,
            features_completed=10,
            timestamp=dt.now(),
            decision=CheckpointDecision.PAUSE,
            total_critical=1
        )

        markdown = writer._generate_markdown(result)

        assert "## ⚠️ Action Required" in markdown
        assert "Development has been **paused**" in markdown
        assert "**Next Steps:**" in markdown

    def test_list_checkpoints_sorted(self, temp_project_dir):
        """Should list checkpoints sorted by number."""
        writer = CheckpointReportWriter(temp_project_dir)

        # Create multiple checkpoints
        for i in [3, 1, 2]:
            result = AggregatedCheckpointResult(
                checkpoint_number=i,
                features_completed=i * 10,
                timestamp=dt.now(),
                decision=CheckpointDecision.CONTINUE
            )
            writer.save_report(result)

        checkpoints = writer.list_checkpoints()

        assert len(checkpoints) == 3
        # Should be sorted by checkpoint number
        assert "checkpoint_01" in checkpoints[0].name
        assert "checkpoint_02" in checkpoints[1].name
        assert "checkpoint_03" in checkpoints[2].name

    def test_get_latest_checkpoint(self, temp_project_dir):
        """Should return most recently created checkpoint."""
        writer = CheckpointReportWriter(temp_project_dir)

        # Create checkpoints with delays
        import time

        result1 = AggregatedCheckpointResult(
            checkpoint_number=1,
            features_completed=10,
            timestamp=dt.now(),
            decision=CheckpointDecision.CONTINUE
        )
        writer.save_report(result1)

        time.sleep(0.01)

        result2 = AggregatedCheckpointResult(
            checkpoint_number=2,
            features_completed=20,
            timestamp=dt.now(),
            decision=CheckpointDecision.CONTINUE
        )
        writer.save_report(result2)

        latest = writer.get_latest_checkpoint_path()

        assert latest is not None
        assert "checkpoint_02" in latest.name

    def test_get_latest_checkpoint_when_none_exist(self, temp_project_dir):
        """Should return None when no checkpoints exist."""
        writer = CheckpointReportWriter(temp_project_dir)

        latest = writer.get_latest_checkpoint_path()

        assert latest is None

    def test_read_checkpoint(self, temp_project_dir):
        """Should read checkpoint by number."""
        writer = CheckpointReportWriter(temp_project_dir)

        result = AggregatedCheckpointResult(
            checkpoint_number=5,
            features_completed=50,
            timestamp=dt.now(),
            decision=CheckpointDecision.CONTINUE
        )
        writer.save_report(result, feature_name="Auth System")

        content = writer.read_checkpoint(5)

        assert content is not None
        assert "# Checkpoint #5" in content
        assert "**Features Completed:** 50" in content
        assert "**Last Feature:** Auth System" in content

    def test_read_nonexistent_checkpoint(self, temp_project_dir):
        """Should return None for nonexistent checkpoint."""
        writer = CheckpointReportWriter(temp_project_dir)

        content = writer.read_checkpoint(999)

        assert content is None

    def test_markdown_with_critical_issues(self, temp_project_dir):
        """Should properly format critical issues."""
        writer = CheckpointReportWriter(temp_project_dir)

        result = AggregatedCheckpointResult(
            checkpoint_number=1,
            features_completed=10,
            timestamp=dt.now(),
            decision=CheckpointDecision.PAUSE,
            results=[
                CheckpointResult(
                    checkpoint_type='security_audit',
                    status='FAIL',
                    issues=[
                        CheckpointIssue(
                            severity=IssueSeverity.CRITICAL,
                            checkpoint_type='security_audit',
                            title='SQL Injection Vulnerability',
                            description='Unescaped user input in query',
                            location='api/users.py',
                            line_number=145,
                            suggestion='Use parameterized queries'
                        )
                    ]
                )
            ],
            total_critical=1
        )

        markdown = writer._generate_markdown(result)

        assert "##### 🔴 Critical Issues" in markdown
        assert "**SQL Injection Vulnerability**" in markdown
        assert "Unescaped user input in query" in markdown
        assert "*Location:* `api/users.py`" in markdown
        assert "(Line 145)" in markdown
        assert "*Suggestion:* Use parameterized queries" in markdown

    def test_markdown_with_info_issues(self, temp_project_dir):
        """Should properly format info items."""
        writer = CheckpointReportWriter(temp_project_dir)

        result = AggregatedCheckpointResult(
            checkpoint_number=1,
            features_completed=10,
            timestamp=dt.now(),
            decision=CheckpointDecision.CONTINUE,
            results=[
                CheckpointResult(
                    checkpoint_type='code_review',
                    status='PASS',
                    issues=[
                        CheckpointIssue(
                            severity=IssueSeverity.INFO,
                            checkpoint_type='code_review',
                            title='Good naming conventions',
                            description='All variables follow snake_case'
                        )
                    ]
                )
            ],
            total_info=1
        )

        markdown = writer._generate_markdown(result)

        assert "##### 🔵 Informational" in markdown
        assert "**Good naming conventions**: All variables follow snake_case" in markdown


class TestCheckpointDatabaseStorage:
    """Test database storage for checkpoints."""

    def test_checkpoint_model_to_dict(self):
        """Should convert Checkpoint model to dictionary."""
        from api.database import Checkpoint

        checkpoint = Checkpoint(
            id=1,
            checkpoint_number=5,
            features_completed=50,
            timestamp=dt(2026, 1, 21, 12, 0, 0),
            decision="CONTINUE",
            total_critical=0,
            total_warnings=2,
            total_info=1,
            execution_time_ms=500.0,
            report_filepath="/path/to/report.md",
            result_json={"test": "data"}
        )

        result_dict = checkpoint.to_dict()

        assert result_dict["checkpoint_number"] == 5
        assert result_dict["features_completed"] == 50
        assert result_dict["decision"] == "CONTINUE"
        assert result_dict["total_warnings"] == 2
        assert result_dict["execution_time_ms"] == 500.0
        assert result_dict["report_filepath"] == "/path/to/report.md"


class TestCheckpointReportIntegration:
    """Integration tests for checkpoint report system."""

    @pytest.mark.asyncio
    async def test_complete_checkpoint_workflow_with_report(self, temp_project_dir):
        """Should run checkpoint and save report."""
        config = AutocoderConfig(
            checkpoints=CheckpointConfig(enabled=True, frequency=10)
        )

        orchestrator = CheckpointOrchestrator(temp_project_dir, config)
        result = await orchestrator.run_checkpoint(features_completed=10)

        # Save report
        writer = CheckpointReportWriter(temp_project_dir)
        filepath = writer.save_report(result, feature_name="Test Feature")

        # Verify file exists and contains expected content
        assert filepath.exists()
        content = filepath.read_text()
        assert "# Checkpoint #1" in content
        assert "**Features Completed:** 10" in content
        assert "**Last Feature:** Test Feature" in content
