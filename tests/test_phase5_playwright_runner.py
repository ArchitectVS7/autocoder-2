"""
Tests for Phase 5 - Task 5.2: Automated Test Execution

This test suite validates the Playwright test runner functionality,
ensuring proper test execution, screenshot capture, and result tracking.
"""

import pytest
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime, timedelta

from ux_eval.playwright_runner import (
    PlaywrightTestRunner,
    TestExecutionResult,
    TestSuiteResult,
    run_ux_tests
)


class TestTestExecutionResult:
    """Test the TestExecutionResult dataclass."""

    def test_create_execution_result(self):
        """Test creating a TestExecutionResult instance."""
        result = TestExecutionResult(
            test_file="test_onboarding.py",
            test_name="onboarding",
            result="passed",
            duration_ms=1500
        )

        assert result.test_file == "test_onboarding.py"
        assert result.test_name == "onboarding"
        assert result.result == "passed"
        assert result.duration_ms == 1500
        assert result.error_message is None
        assert len(result.screenshots_captured) == 0

    def test_execution_result_with_error(self):
        """Test creating a result with error message."""
        result = TestExecutionResult(
            test_file="test_checkout.py",
            test_name="checkout",
            result="failed",
            duration_ms=2000,
            error_message="Button not found"
        )

        assert result.result == "failed"
        assert result.error_message == "Button not found"

    def test_execution_result_with_screenshots(self):
        """Test result with screenshot paths."""
        screenshots = [
            Path("/screenshots/flow/step1.png"),
            Path("/screenshots/flow/step2.png")
        ]

        result = TestExecutionResult(
            test_file="test_flow.py",
            test_name="flow",
            result="passed",
            duration_ms=1000,
            screenshots_captured=screenshots
        )

        assert len(result.screenshots_captured) == 2
        assert result.screenshots_captured[0].name == "step1.png"

    def test_execution_result_to_dict(self):
        """Test converting execution result to dictionary."""
        result = TestExecutionResult(
            test_file="test_flow.py",
            test_name="flow",
            result="passed",
            duration_ms=1000,
            screenshots_captured=[Path("/screenshots/step1.png")]
        )

        result_dict = result.to_dict()

        assert result_dict["test_file"] == "test_flow.py"
        assert result_dict["test_name"] == "flow"
        assert result_dict["result"] == "passed"
        assert result_dict["duration_ms"] == 1000
        assert len(result_dict["screenshots_captured"]) == 1
        assert "timestamp" in result_dict

    def test_execution_result_with_video(self):
        """Test result with video path."""
        result = TestExecutionResult(
            test_file="test_flow.py",
            test_name="flow",
            result="passed",
            duration_ms=1000,
            video_path=Path("/videos/flow.webm")
        )

        assert result.video_path == Path("/videos/flow.webm")
        assert result.to_dict()["video_path"] == "/videos/flow.webm"


class TestTestSuiteResult:
    """Test the TestSuiteResult dataclass."""

    def test_create_suite_result(self):
        """Test creating a TestSuiteResult instance."""
        suite = TestSuiteResult(suite_name="UX Tests")

        assert suite.suite_name == "UX Tests"
        assert suite.total_tests == 0
        assert suite.passed == 0
        assert suite.failed == 0
        assert len(suite.test_results) == 0

    def test_add_passing_result(self):
        """Test adding a passing test result."""
        suite = TestSuiteResult(suite_name="UX Tests")

        result = TestExecutionResult(
            test_file="test_flow.py",
            test_name="flow",
            result="passed",
            duration_ms=1000
        )

        suite.add_result(result)

        assert suite.total_tests == 1
        assert suite.passed == 1
        assert suite.failed == 0
        assert suite.total_duration_ms == 1000

    def test_add_failing_result(self):
        """Test adding a failing test result."""
        suite = TestSuiteResult(suite_name="UX Tests")

        result = TestExecutionResult(
            test_file="test_flow.py",
            test_name="flow",
            result="failed",
            duration_ms=1500,
            error_message="Test failed"
        )

        suite.add_result(result)

        assert suite.total_tests == 1
        assert suite.passed == 0
        assert suite.failed == 1

    def test_add_multiple_results(self):
        """Test adding multiple test results."""
        suite = TestSuiteResult(suite_name="UX Tests")

        suite.add_result(TestExecutionResult(
            test_file="test1.py",
            test_name="test1",
            result="passed",
            duration_ms=1000
        ))

        suite.add_result(TestExecutionResult(
            test_file="test2.py",
            test_name="test2",
            result="failed",
            duration_ms=1500
        ))

        suite.add_result(TestExecutionResult(
            test_file="test3.py",
            test_name="test3",
            result="passed",
            duration_ms=1200
        ))

        assert suite.total_tests == 3
        assert suite.passed == 2
        assert suite.failed == 1
        assert suite.total_duration_ms == 3700

    def test_pass_rate_calculation(self):
        """Test pass rate calculation."""
        suite = TestSuiteResult(suite_name="UX Tests")

        suite.add_result(TestExecutionResult(
            test_file="test1.py",
            test_name="test1",
            result="passed",
            duration_ms=1000
        ))

        suite.add_result(TestExecutionResult(
            test_file="test2.py",
            test_name="test2",
            result="failed",
            duration_ms=1000
        ))

        assert suite.pass_rate == 50.0

    def test_pass_rate_zero_tests(self):
        """Test pass rate with zero tests."""
        suite = TestSuiteResult(suite_name="UX Tests")

        assert suite.pass_rate == 0.0

    def test_pass_rate_all_passed(self):
        """Test pass rate with all tests passing."""
        suite = TestSuiteResult(suite_name="UX Tests")

        for i in range(5):
            suite.add_result(TestExecutionResult(
                test_file=f"test{i}.py",
                test_name=f"test{i}",
                result="passed",
                duration_ms=1000
            ))

        assert suite.pass_rate == 100.0

    def test_suite_result_to_dict(self):
        """Test converting suite result to dictionary."""
        suite = TestSuiteResult(suite_name="UX Tests")

        suite.add_result(TestExecutionResult(
            test_file="test1.py",
            test_name="test1",
            result="passed",
            duration_ms=1000
        ))

        suite_dict = suite.to_dict()

        assert suite_dict["suite_name"] == "UX Tests"
        assert suite_dict["summary"]["total_tests"] == 1
        assert suite_dict["summary"]["passed"] == 1
        assert suite_dict["summary"]["pass_rate"] == 100.0
        assert len(suite_dict["test_results"]) == 1

    def test_suite_with_skipped_and_errors(self):
        """Test suite with skipped tests and errors."""
        suite = TestSuiteResult(suite_name="UX Tests")

        suite.add_result(TestExecutionResult(
            test_file="test1.py",
            test_name="test1",
            result="skipped",
            duration_ms=0
        ))

        suite.add_result(TestExecutionResult(
            test_file="test2.py",
            test_name="test2",
            result="error",
            duration_ms=500,
            error_message="Timeout"
        ))

        assert suite.skipped == 1
        assert suite.errors == 1
        assert suite.total_tests == 2


class TestPlaywrightTestRunner:
    """Test the PlaywrightTestRunner class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directories for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def runner(self, temp_dir):
        """Create a PlaywrightTestRunner instance."""
        tests_dir = temp_dir / "tests"
        screenshots_dir = temp_dir / "screenshots"
        videos_dir = temp_dir / "videos"

        tests_dir.mkdir()

        return PlaywrightTestRunner(
            tests_dir=tests_dir,
            screenshots_dir=screenshots_dir,
            videos_dir=videos_dir,
            enable_video=False
        )

    def test_runner_initialization(self, runner, temp_dir):
        """Test initializing PlaywrightTestRunner."""
        assert runner.tests_dir == temp_dir / "tests"
        assert runner.screenshots_dir == temp_dir / "screenshots"
        assert runner.videos_dir == temp_dir / "videos"
        assert not runner.enable_video

        # Check directories were created
        assert runner.screenshots_dir.exists()
        assert not runner.videos_dir.exists()  # Not created when video disabled

    def test_runner_with_video_enabled(self, temp_dir):
        """Test runner initialization with video enabled."""
        runner = PlaywrightTestRunner(
            tests_dir=temp_dir / "tests",
            screenshots_dir=temp_dir / "screenshots",
            videos_dir=temp_dir / "videos",
            enable_video=True
        )

        assert runner.enable_video
        assert runner.videos_dir.exists()

    def test_get_screenshots_by_flow(self, runner):
        """Test getting screenshots for a specific flow."""
        # Create mock screenshots
        flow_dir = runner.screenshots_dir / "onboarding"
        flow_dir.mkdir(parents=True)

        (flow_dir / "step1.png").touch()
        (flow_dir / "step2.png").touch()
        (flow_dir / "step3.png").touch()

        screenshots = runner.get_screenshots_by_flow("onboarding")

        assert len(screenshots) == 3
        assert all(p.suffix == ".png" for p in screenshots)
        assert screenshots[0].name == "step1.png"

    def test_get_screenshots_for_nonexistent_flow(self, runner):
        """Test getting screenshots for flow that doesn't exist."""
        screenshots = runner.get_screenshots_by_flow("nonexistent")

        assert len(screenshots) == 0

    def test_organize_screenshots(self, runner):
        """Test organizing screenshots by flow ID."""
        # Create mock screenshots for multiple flows
        for flow_id in ["onboarding", "dashboard", "settings"]:
            flow_dir = runner.screenshots_dir / flow_id
            flow_dir.mkdir(parents=True)

            (flow_dir / "step1.png").touch()
            (flow_dir / "step2.png").touch()

        organized = runner.organize_screenshots()

        assert len(organized) == 3
        assert "onboarding" in organized
        assert "dashboard" in organized
        assert "settings" in organized
        assert len(organized["onboarding"]) == 2

    def test_organize_screenshots_empty(self, runner):
        """Test organizing when no screenshots exist."""
        organized = runner.organize_screenshots()

        assert len(organized) == 0

    def test_save_results(self, runner, temp_dir):
        """Test saving test results to JSON."""
        suite = TestSuiteResult(suite_name="UX Tests")

        suite.add_result(TestExecutionResult(
            test_file="test_flow.py",
            test_name="flow",
            result="passed",
            duration_ms=1000
        ))

        output_file = temp_dir / "results.json"
        saved_path = runner.save_results(suite, output_file)

        assert saved_path.exists()

        with open(saved_path, 'r') as f:
            data = json.load(f)

        assert data["suite_name"] == "UX Tests"
        assert data["summary"]["total_tests"] == 1

    def test_cleanup_old_results(self, runner):
        """Test cleaning up old test results."""
        # Create mock screenshots with old timestamps
        flow_dir = runner.screenshots_dir / "old-flow"
        flow_dir.mkdir(parents=True)

        old_file = flow_dir / "old_screenshot.png"
        old_file.touch()

        # Set file modification time to 10 days ago
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        import os
        os.utime(old_file, (old_time, old_time))

        # Clean files older than 7 days
        removed_count = runner.cleanup_old_results(days_old=7)

        assert removed_count == 1
        assert not old_file.exists()

    def test_cleanup_keeps_recent_files(self, runner):
        """Test that cleanup keeps recent files."""
        # Create recent screenshot
        flow_dir = runner.screenshots_dir / "recent-flow"
        flow_dir.mkdir(parents=True)

        recent_file = flow_dir / "recent_screenshot.png"
        recent_file.touch()

        # Clean files older than 7 days
        removed_count = runner.cleanup_old_results(days_old=7)

        assert removed_count == 0
        assert recent_file.exists()


class TestRunUxTests:
    """Test the run_ux_tests convenience function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directories for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_run_ux_tests_basic(self, temp_dir):
        """Test basic run_ux_tests functionality."""
        tests_dir = temp_dir / "tests"
        screenshots_dir = temp_dir / "screenshots"
        videos_dir = temp_dir / "videos"

        tests_dir.mkdir()

        # Run with no tests (should not error)
        result = run_ux_tests(
            tests_dir=tests_dir,
            screenshots_dir=screenshots_dir,
            videos_dir=videos_dir,
            enable_video=False,
            headless=True,
            save_results=False
        )

        assert result.suite_name == "Playwright UX Tests"
        assert result.total_tests == 0

    def test_run_ux_tests_with_video(self, temp_dir):
        """Test running tests with video enabled."""
        tests_dir = temp_dir / "tests"
        screenshots_dir = temp_dir / "screenshots"
        videos_dir = temp_dir / "videos"

        tests_dir.mkdir()

        result = run_ux_tests(
            tests_dir=tests_dir,
            screenshots_dir=screenshots_dir,
            videos_dir=videos_dir,
            enable_video=True,
            headless=True,
            save_results=False
        )

        assert result.videos_dir == videos_dir


class TestIntegration:
    """Integration tests for the full test execution workflow."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directories for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_full_workflow(self, temp_dir):
        """Test complete workflow from setup to result saving."""
        tests_dir = temp_dir / "tests"
        screenshots_dir = temp_dir / "screenshots"
        videos_dir = temp_dir / "videos"

        tests_dir.mkdir()

        # Initialize runner
        runner = PlaywrightTestRunner(
            tests_dir=tests_dir,
            screenshots_dir=screenshots_dir,
            videos_dir=videos_dir,
            enable_video=False
        )

        # Create mock screenshots
        for flow_id in ["flow1", "flow2"]:
            flow_dir = screenshots_dir / flow_id
            flow_dir.mkdir(parents=True)
            (flow_dir / "step1.png").touch()
            (flow_dir / "step2.png").touch()

        # Create mock test results
        suite = TestSuiteResult(suite_name="Integration Test")

        suite.add_result(TestExecutionResult(
            test_file="test_flow1.py",
            test_name="flow1",
            result="passed",
            duration_ms=1000,
            screenshots_captured=runner.get_screenshots_by_flow("flow1")
        ))

        suite.add_result(TestExecutionResult(
            test_file="test_flow2.py",
            test_name="flow2",
            result="passed",
            duration_ms=1200,
            screenshots_captured=runner.get_screenshots_by_flow("flow2")
        ))

        # Save results
        results_file = runner.save_results(suite, temp_dir / "results.json")

        # Verify everything
        assert results_file.exists()
        assert suite.total_tests == 2
        assert suite.passed == 2
        assert suite.pass_rate == 100.0

        # Verify screenshots are organized
        organized = runner.organize_screenshots()
        assert len(organized) == 2
        assert len(organized["flow1"]) == 2
        assert len(organized["flow2"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
