"""
Tests for Phase 6: Integration & Polish

Test coverage:
- Task 6.1: End-to-End Workflow Integration
- Task 6.2: Configuration UI
- Task 6.3: Documentation (validation only)
- Task 6.4: Sample Project (validation only)
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json

from integration.workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowConfig,
    WorkflowPhase,
    WorkflowResult,
    run_complete_workflow
)


# ============================================================================
# Task 6.1: End-to-End Workflow Integration
# ============================================================================

class TestWorkflowConfig:
    """Test WorkflowConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = WorkflowConfig()

        assert config.enable_design_iteration is True
        assert config.enable_checkpoints is True
        assert config.enable_ux_evaluation is True
        assert config.enable_metrics is True
        assert config.max_design_iterations == 4
        assert config.checkpoint_frequency == 10
        assert config.min_ux_score == 7.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = WorkflowConfig(
            enable_design_iteration=False,
            checkpoint_frequency=5,
            min_ux_score=8.5
        )

        assert config.enable_design_iteration is False
        assert config.checkpoint_frequency == 5
        assert config.min_ux_score == 8.5

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = WorkflowConfig(checkpoint_frequency=15)
        data = config.to_dict()

        assert isinstance(data, dict)
        assert data['checkpoint_frequency'] == 15
        assert data['enable_checkpoints'] is True

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            'checkpoint_frequency': 20,
            'min_ux_score': 8.0,
            'enable_design_iteration': False
        }
        config = WorkflowConfig.from_dict(data)

        assert config.checkpoint_frequency == 20
        assert config.min_ux_score == 8.0
        assert config.enable_design_iteration is False

    def test_config_roundtrip(self):
        """Test config serialization roundtrip."""
        original = WorkflowConfig(
            checkpoint_frequency=25,
            ux_flows=['onboarding', 'checkout']
        )

        data = original.to_dict()
        restored = WorkflowConfig.from_dict(data)

        assert restored.checkpoint_frequency == original.checkpoint_frequency
        assert restored.ux_flows == original.ux_flows


class TestWorkflowResult:
    """Test WorkflowResult dataclass."""

    def test_default_result(self):
        """Test default result values."""
        result = WorkflowResult(
            project_name="test-project",
            start_time=datetime.now()
        )

        assert result.project_name == "test-project"
        assert result.current_phase == WorkflowPhase.DESIGN_ITERATION
        assert result.success is False
        assert result.features_completed == 0

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        start = datetime.now()
        result = WorkflowResult(
            project_name="test-project",
            start_time=start,
            features_completed=10
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data['project_name'] == "test-project"
        assert data['features_completed'] == 10
        assert data['current_phase'] == WorkflowPhase.DESIGN_ITERATION.value

    def test_result_with_all_phases(self):
        """Test result with all phases completed."""
        result = WorkflowResult(
            project_name="test-project",
            start_time=datetime.now()
        )

        result.design_spec_path = Path("/tmp/spec.md")
        result.design_iterations = 3
        result.development_complete = True
        result.features_completed = 50
        result.features_total = 50
        result.ux_evaluation_complete = True
        result.ux_score = 8.5
        result.current_phase = WorkflowPhase.COMPLETE
        result.success = True

        assert result.design_iterations == 3
        assert result.ux_score == 8.5
        assert result.current_phase == WorkflowPhase.COMPLETE
        assert result.success is True


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator class."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_orchestrator_initialization(self, temp_project_dir):
        """Test orchestrator initialization."""
        orchestrator = WorkflowOrchestrator(temp_project_dir)

        assert orchestrator.project_dir == temp_project_dir
        assert isinstance(orchestrator.config, WorkflowConfig)
        assert orchestrator.result.project_name == temp_project_dir.name

    def test_orchestrator_with_custom_config(self, temp_project_dir):
        """Test orchestrator with custom configuration."""
        config = WorkflowConfig(
            enable_design_iteration=False,
            checkpoint_frequency=5
        )
        orchestrator = WorkflowOrchestrator(temp_project_dir, config)

        assert orchestrator.config.enable_design_iteration is False
        assert orchestrator.config.checkpoint_frequency == 5

    def test_output_directory_created(self, temp_project_dir):
        """Test that output directory is created."""
        orchestrator = WorkflowOrchestrator(temp_project_dir)

        assert orchestrator.output_dir.exists()
        assert orchestrator.output_dir.is_dir()

    def test_update_development_progress(self, temp_project_dir):
        """Test updating development progress."""
        orchestrator = WorkflowOrchestrator(temp_project_dir)
        orchestrator.result.features_total = 100

        orchestrator.update_development_progress(25)

        assert orchestrator.result.features_completed == 25

        orchestrator.update_development_progress(50)

        assert orchestrator.result.features_completed == 50

    def test_record_checkpoint(self, temp_project_dir):
        """Test recording checkpoint execution."""
        orchestrator = WorkflowOrchestrator(temp_project_dir)

        orchestrator.record_checkpoint(critical_issues=0)

        assert orchestrator.result.checkpoints_run == 1
        assert orchestrator.result.critical_issues_found == 0

        orchestrator.record_checkpoint(critical_issues=3)

        assert orchestrator.result.checkpoints_run == 2
        assert orchestrator.result.critical_issues_found == 3

    @pytest.mark.asyncio
    async def test_run_development_with_checkpoints(self, temp_project_dir):
        """Test development phase setup."""
        orchestrator = WorkflowOrchestrator(temp_project_dir)

        success = await orchestrator.run_development_with_checkpoints(features_total=50)

        assert success is True
        assert orchestrator.result.features_total == 50
        assert orchestrator.result.current_phase == WorkflowPhase.DEVELOPMENT

    @pytest.mark.asyncio
    async def test_run_development_with_checkpoints_disabled(self, temp_project_dir):
        """Test development phase with checkpoints disabled."""
        config = WorkflowConfig(enable_checkpoints=False)
        orchestrator = WorkflowOrchestrator(temp_project_dir, config)

        success = await orchestrator.run_development_with_checkpoints(features_total=50)

        assert success is True


# Regression tests for Phase 3
class TestPhase3Regression:
    """Regression tests for Phase 3: Checkpoint System."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_checkpoint_config_integration(self, temp_project_dir):
        """Test that WorkflowConfig correctly sets CheckpointConfig."""
        from checkpoint.config import CheckpointConfig

        config = WorkflowConfig(
            checkpoint_frequency=15,
            auto_pause_on_critical=False
        )
        orchestrator = WorkflowOrchestrator(temp_project_dir, config)

        checkpoint_config = CheckpointConfig.get_instance()

        # WorkflowOrchestrator should update checkpoint config
        assert checkpoint_config.enabled is True
        assert checkpoint_config.frequency == 15
        assert checkpoint_config.auto_pause_on_critical is False


# Regression tests for Phase 4
class TestPhase4Regression:
    """Regression tests for Phase 4: Design Iteration."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_design_iteration_components_initialized(self, temp_project_dir):
        """Test that design components are initialized correctly."""
        config = WorkflowConfig(enable_design_iteration=True)
        orchestrator = WorkflowOrchestrator(temp_project_dir, config)

        assert hasattr(orchestrator, 'design_agent')
        assert hasattr(orchestrator, 'design_review')
        assert hasattr(orchestrator, 'design_synthesis')

    def test_design_iteration_disabled(self, temp_project_dir):
        """Test that design components are not initialized when disabled."""
        config = WorkflowConfig(enable_design_iteration=False)
        orchestrator = WorkflowOrchestrator(temp_project_dir, config)

        # Components should not be initialized
        assert not hasattr(orchestrator, 'design_agent')


# Regression tests for Phase 5
class TestPhase5Regression:
    """Regression tests for Phase 5: UX Evaluation."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_ux_evaluation_components_initialized(self, temp_project_dir):
        """Test that UX evaluation components are initialized correctly."""
        config = WorkflowConfig(enable_ux_evaluation=True)
        orchestrator = WorkflowOrchestrator(temp_project_dir, config)

        assert hasattr(orchestrator, 'playwright_generator')
        assert hasattr(orchestrator, 'playwright_runner')
        assert hasattr(orchestrator, 'ux_evaluator')

    def test_ux_evaluation_disabled(self, temp_project_dir):
        """Test that UX components are not initialized when disabled."""
        config = WorkflowConfig(enable_ux_evaluation=False)
        orchestrator = WorkflowOrchestrator(temp_project_dir, config)

        # Components should not be initialized
        assert not hasattr(orchestrator, 'playwright_generator')


# ============================================================================
# Task 6.2: Configuration UI
# ============================================================================

class TestConfigurationUI:
    """Tests for configuration UI (Task 6.2)."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_config_ui_initialization(self, temp_project_dir):
        """Test ConfigurationUI initialization."""
        from integration.config_ui import ConfigurationUI

        ui = ConfigurationUI(temp_project_dir)

        assert ui.project_dir == temp_project_dir
        assert isinstance(ui.config, WorkflowConfig)

    def test_save_and_load_config(self, temp_project_dir):
        """Test saving and loading configuration."""
        from integration.config_ui import ConfigurationUI

        ui = ConfigurationUI(temp_project_dir)

        # Modify config
        ui.config.checkpoint_frequency = 15
        ui.config.min_ux_score = 8.5

        # Save
        ui.save_config()

        # Create new UI instance (should load saved config)
        ui2 = ConfigurationUI(temp_project_dir)

        assert ui2.config.checkpoint_frequency == 15
        assert ui2.config.min_ux_score == 8.5

    def test_enable_feature(self, temp_project_dir):
        """Test enabling a feature."""
        from integration.config_ui import ConfigurationUI

        ui = ConfigurationUI(temp_project_dir)
        ui.config.enable_checkpoints = False

        ui.enable_feature('checkpoints')

        assert ui.config.enable_checkpoints is True

    def test_disable_feature(self, temp_project_dir):
        """Test disabling a feature."""
        from integration.config_ui import ConfigurationUI

        ui = ConfigurationUI(temp_project_dir)
        ui.config.enable_ux_evaluation = True

        ui.disable_feature('ux')

        assert ui.config.enable_ux_evaluation is False

    def test_set_threshold_int(self, temp_project_dir):
        """Test setting integer threshold."""
        from integration.config_ui import ConfigurationUI

        ui = ConfigurationUI(temp_project_dir)

        ui.set_threshold('checkpoint_frequency', '20')

        assert ui.config.checkpoint_frequency == 20

    def test_set_threshold_float(self, temp_project_dir):
        """Test setting float threshold."""
        from integration.config_ui import ConfigurationUI

        ui = ConfigurationUI(temp_project_dir)

        ui.set_threshold('min_ux_score', '8.5')

        assert ui.config.min_ux_score == 8.5

    def test_reset_config(self, temp_project_dir):
        """Test resetting configuration to defaults."""
        from integration.config_ui import ConfigurationUI

        ui = ConfigurationUI(temp_project_dir)

        # Modify config
        ui.config.checkpoint_frequency = 99
        ui.config.min_ux_score = 1.0

        # Reset
        ui.reset_config()

        # Should be back to defaults
        default_config = WorkflowConfig()
        assert ui.config.checkpoint_frequency == default_config.checkpoint_frequency
        assert ui.config.min_ux_score == default_config.min_ux_score

    def test_export_json(self, temp_project_dir):
        """Test exporting configuration to JSON."""
        from integration.config_ui import ConfigurationUI

        ui = ConfigurationUI(temp_project_dir)
        ui.config.checkpoint_frequency = 25

        export_path = temp_project_dir / "exported_config.json"
        ui.export_json(export_path)

        assert export_path.exists()

        # Verify JSON content
        with open(export_path, 'r') as f:
            data = json.load(f)

        assert data['checkpoint_frequency'] == 25

    def test_import_json(self, temp_project_dir):
        """Test importing configuration from JSON."""
        from integration.config_ui import ConfigurationUI

        # Create JSON config file
        config_data = {
            'checkpoint_frequency': 30,
            'min_ux_score': 9.0,
            'enable_checkpoints': False
        }

        import_path = temp_project_dir / "import_config.json"
        with open(import_path, 'w') as f:
            json.dump(config_data, f)

        # Import
        ui = ConfigurationUI(temp_project_dir)
        ui.import_json(import_path)

        assert ui.config.checkpoint_frequency == 30
        assert ui.config.min_ux_score == 9.0
        assert ui.config.enable_checkpoints is False


# ============================================================================
# Task 6.3: Documentation (validation tests)
# ============================================================================

class TestDocumentation:
    """Tests for documentation validation (Task 6.3)."""

    def test_user_guide_exists(self):
        """Test that USER_GUIDE.md exists."""
        user_guide = Path("/home/user/autocoder-2/docs/USER_GUIDE.md")
        assert user_guide.exists(), "USER_GUIDE.md should exist"

    def test_api_documentation_exists(self):
        """Test that API_DOCUMENTATION.md exists."""
        api_docs = Path("/home/user/autocoder-2/docs/API_DOCUMENTATION.md")
        assert api_docs.exists(), "API_DOCUMENTATION.md should exist"

    def test_example_exists(self):
        """Test that example file exists."""
        example = Path("/home/user/autocoder-2/docs/examples/COMPLETE_WORKFLOW_EXAMPLE.md")
        assert example.exists(), "COMPLETE_WORKFLOW_EXAMPLE.md should exist"

    def test_troubleshooting_updated(self):
        """Test that TROUBLESHOOTING.md was updated with Phase 6 content."""
        troubleshooting = Path("/home/user/autocoder-2/docs/TROUBLESHOOTING.md")
        assert troubleshooting.exists(), "TROUBLESHOOTING.md should exist"

        # Check for Phase 6 content
        content = troubleshooting.read_text()
        assert "Phase 6: Workflow Integration Issues" in content
        assert "Workflow Orchestrator Import Error" in content
        assert "Configuration File Not Found" in content
        assert "Design Iteration Not Running" in content
        assert "UX Evaluation Failing" in content

    def test_documentation_completeness(self):
        """Test that all documentation sections are present."""
        user_guide = Path("/home/user/autocoder-2/docs/USER_GUIDE.md")
        content = user_guide.read_text()

        # Check key sections
        required_sections = [
            "Introduction",
            "Getting Started",
            "Complete Workflow",
            "Phase-by-Phase Guide",
            "Configuration",
            "Best Practices",
            "Troubleshooting"
        ]

        for section in required_sections:
            assert section in content, f"USER_GUIDE.md should have {section} section"


# ============================================================================
# Task 6.4: Sample Project
# ============================================================================

class TestSampleProject:
    """Tests for sample project (Task 6.4)."""

    def test_sample_project_readme_exists(self):
        """Test that sample project README exists."""
        readme = Path("/home/user/autocoder-2/sample_project/README.md")
        assert readme.exists(), "sample_project/README.md should exist"

    def test_sample_project_initial_spec_exists(self):
        """Test that initial spec exists."""
        spec = Path("/home/user/autocoder-2/sample_project/initial_spec.md")
        assert spec.exists(), "sample_project/initial_spec.md should exist"

    def test_sample_project_config_exists(self):
        """Test that config file exists."""
        config = Path("/home/user/autocoder-2/sample_project/autocoder_config.yaml")
        assert config.exists(), "sample_project/autocoder_config.yaml should exist"

    def test_sample_project_runner_exists(self):
        """Test that workflow runner exists."""
        runner = Path("/home/user/autocoder-2/sample_project/run_workflow.py")
        assert runner.exists(), "sample_project/run_workflow.py should exist"

    def test_sample_project_config_valid(self):
        """Test that sample project config is valid YAML."""
        import yaml

        config_path = Path("/home/user/autocoder-2/sample_project/autocoder_config.yaml")
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Check key settings
        assert config_data['enable_design_iteration'] is True
        assert config_data['enable_checkpoints'] is True
        assert config_data['checkpoint_frequency'] == 5  # Optimized for small project

    def test_sample_project_readme_complete(self):
        """Test that README has all required sections."""
        readme = Path("/home/user/autocoder-2/sample_project/README.md")
        content = readme.read_text()

        required_sections = [
            "Project Overview",
            "What This Demonstrates",
            "Quick Start",
            "Configuration",
            "Expected Features",
            "Expected Timeline",
            "Learning Objectives",
            "Common Issues"
        ]

        for section in required_sections:
            assert section in content, f"README should have {section} section"

    def test_sample_project_spec_complete(self):
        """Test that initial spec has all required sections."""
        spec = Path("/home/user/autocoder-2/sample_project/initial_spec.md")
        content = spec.read_text()

        required_sections = [
            "Overview",
            "Target Users",
            "Core Features",
            "Design Requirements",
            "Technical Stack"
        ]

        for section in required_sections:
            assert section in content, f"Spec should have {section} section"


# ============================================================================
# Integration Tests
# ============================================================================

class TestWorkflowIntegration:
    """Integration tests for complete workflow."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_minimal_workflow(self, temp_project_dir):
        """Test minimal workflow with all phases disabled except development."""
        config = WorkflowConfig(
            enable_design_iteration=False,
            enable_checkpoints=False,
            enable_ux_evaluation=False,
            enable_metrics=False
        )

        orchestrator = WorkflowOrchestrator(temp_project_dir, config)

        # Run just development setup
        success = await orchestrator.run_development_with_checkpoints(features_total=10)

        assert success is True
        assert orchestrator.result.features_total == 10

    def test_workflow_result_persistence(self, temp_project_dir):
        """Test that workflow results can be saved and loaded."""
        orchestrator = WorkflowOrchestrator(temp_project_dir)
        orchestrator.update_development_progress(25)
        orchestrator.result.features_total = 100
        orchestrator.result.ux_score = 8.5

        # Save result to JSON
        result_path = temp_project_dir / "workflow_result.json"
        with open(result_path, 'w') as f:
            json.dump(orchestrator.result.to_dict(), f, indent=2)

        # Load and verify
        with open(result_path, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data['project_name'] == temp_project_dir.name
        assert loaded_data['features_completed'] == 25
        assert loaded_data['features_total'] == 100
        assert loaded_data['ux_score'] == 8.5
