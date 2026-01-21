"""
Playwright Test Runner for Phase 5 - Visual UX Evaluation

This module executes Playwright tests and captures screenshots/videos
for later analysis by UX evaluation agents.

Features:
- Runs Playwright tests after development completes
- Captures screenshots automatically during test execution
- Organizes screenshots by flow (screenshots/flow-id/step.png)
- Optionally records videos of test execution
- Provides detailed execution reports
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Literal
import subprocess
import json
import time
from datetime import datetime


TestResult = Literal["passed", "failed", "skipped", "error"]


@dataclass
class TestExecutionResult:
    """Result of executing a single Playwright test."""
    test_file: str
    test_name: str
    result: TestResult
    duration_ms: int
    error_message: Optional[str] = None
    screenshots_captured: List[Path] = field(default_factory=list)
    video_path: Optional[Path] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "test_file": self.test_file,
            "test_name": self.test_name,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "screenshots_captured": [str(p) for p in self.screenshots_captured],
            "video_path": str(self.video_path) if self.video_path else None,
            "timestamp": self.timestamp
        }


@dataclass
class TestSuiteResult:
    """Result of executing a complete test suite."""
    suite_name: str
    test_results: List[TestExecutionResult] = field(default_factory=list)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total_duration_ms: int = 0
    screenshots_dir: Optional[Path] = None
    videos_dir: Optional[Path] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_result(self, result: TestExecutionResult) -> None:
        """Add a test result and update counts."""
        self.test_results.append(result)
        self.total_tests += 1
        self.total_duration_ms += result.duration_ms

        if result.result == "passed":
            self.passed += 1
        elif result.result == "failed":
            self.failed += 1
        elif result.result == "skipped":
            self.skipped += 1
        elif result.result == "error":
            self.errors += 1

    @property
    def pass_rate(self) -> float:
        """Calculate test pass rate as percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "suite_name": self.suite_name,
            "test_results": [r.to_dict() for r in self.test_results],
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "errors": self.errors,
                "pass_rate": round(self.pass_rate, 2),
                "total_duration_ms": self.total_duration_ms
            },
            "screenshots_dir": str(self.screenshots_dir) if self.screenshots_dir else None,
            "videos_dir": str(self.videos_dir) if self.videos_dir else None,
            "timestamp": self.timestamp
        }


class PlaywrightTestRunner:
    """
    Executes Playwright tests and captures visual artifacts.

    This runner provides a high-level interface for running Playwright tests
    with screenshot and video capture, organizing outputs systematically.
    """

    def __init__(
        self,
        tests_dir: Path = Path("tests/ux_flows"),
        screenshots_dir: Path = Path("screenshots"),
        videos_dir: Path = Path("videos"),
        enable_video: bool = False
    ):
        """
        Initialize the Playwright test runner.

        Args:
            tests_dir: Directory containing Playwright test files
            screenshots_dir: Directory for screenshot output
            videos_dir: Directory for video recordings
            enable_video: Whether to record videos during test execution
        """
        self.tests_dir = Path(tests_dir)
        self.screenshots_dir = Path(screenshots_dir)
        self.videos_dir = Path(videos_dir)
        self.enable_video = enable_video

        # Create output directories
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        if self.enable_video:
            self.videos_dir.mkdir(parents=True, exist_ok=True)

    def run_test(self, test_file: Path, headless: bool = True) -> TestExecutionResult:
        """
        Run a single Playwright test file.

        Args:
            test_file: Path to the test file
            headless: Whether to run browser in headless mode

        Returns:
            TestExecutionResult with execution details
        """
        test_name = test_file.stem.replace("test_", "")
        start_time = time.time()

        # Build pytest command
        cmd = [
            "python",
            "-m",
            "pytest",
            str(test_file),
            "-v",
            "--tb=short"
        ]

        # Add headless mode if needed (would be via env var for Playwright)
        env = {"HEADLESS": "true" if headless else "false"}

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env={**subprocess.os.environ, **env}
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Parse test result
            if result.returncode == 0:
                test_result = "passed"
                error_message = None
            else:
                test_result = "failed"
                error_message = result.stdout + "\n" + result.stderr

            # Find screenshots created by this test
            flow_screenshots_dir = self.screenshots_dir / test_name
            screenshots = []
            if flow_screenshots_dir.exists():
                screenshots = sorted(flow_screenshots_dir.glob("*.png"))

            # Find video if enabled
            video_path = None
            if self.enable_video:
                video_file = self.videos_dir / f"{test_name}.webm"
                if video_file.exists():
                    video_path = video_file

            return TestExecutionResult(
                test_file=str(test_file),
                test_name=test_name,
                result=test_result,
                duration_ms=duration_ms,
                error_message=error_message,
                screenshots_captured=screenshots,
                video_path=video_path
            )

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestExecutionResult(
                test_file=str(test_file),
                test_name=test_name,
                result="error",
                duration_ms=duration_ms,
                error_message="Test execution timed out after 5 minutes"
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestExecutionResult(
                test_file=str(test_file),
                test_name=test_name,
                result="error",
                duration_ms=duration_ms,
                error_message=f"Unexpected error: {str(e)}"
            )

    def run_all_tests(
        self,
        pattern: str = "test_*.py",
        headless: bool = True
    ) -> TestSuiteResult:
        """
        Run all Playwright tests matching the given pattern.

        Args:
            pattern: Glob pattern for test files
            headless: Whether to run browsers in headless mode

        Returns:
            TestSuiteResult with all execution results
        """
        suite_result = TestSuiteResult(
            suite_name="Playwright UX Tests",
            screenshots_dir=self.screenshots_dir,
            videos_dir=self.videos_dir if self.enable_video else None
        )

        # Find all test files
        test_files = sorted(self.tests_dir.glob(pattern))

        print(f"\n🎭 Running {len(test_files)} Playwright tests...\n")

        for test_file in test_files:
            print(f"  Running: {test_file.name}")
            result = self.run_test(test_file, headless=headless)
            suite_result.add_result(result)

            # Print result status
            if result.result == "passed":
                print(f"    ✅ PASSED ({result.duration_ms}ms)")
                print(f"       Screenshots: {len(result.screenshots_captured)}")
            else:
                print(f"    ❌ {result.result.upper()} ({result.duration_ms}ms)")
                if result.error_message:
                    print(f"       Error: {result.error_message[:100]}...")

        print(f"\n📊 Test Results:")
        print(f"   Total: {suite_result.total_tests}")
        print(f"   Passed: {suite_result.passed} ({suite_result.pass_rate:.1f}%)")
        print(f"   Failed: {suite_result.failed}")
        print(f"   Errors: {suite_result.errors}")
        print(f"   Duration: {suite_result.total_duration_ms / 1000:.2f}s")

        return suite_result

    def save_results(
        self,
        suite_result: TestSuiteResult,
        output_file: Path = Path("test_results.json")
    ) -> Path:
        """
        Save test suite results to JSON file.

        Args:
            suite_result: TestSuiteResult to save
            output_file: Path to output JSON file

        Returns:
            Path to the saved results file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(suite_result.to_dict(), f, indent=2)

        return output_file

    def get_screenshots_by_flow(self, flow_id: str) -> List[Path]:
        """
        Get all screenshots for a specific flow.

        Args:
            flow_id: ID of the flow

        Returns:
            List of screenshot paths sorted by name
        """
        flow_dir = self.screenshots_dir / flow_id
        if not flow_dir.exists():
            return []

        return sorted(flow_dir.glob("*.png"))

    def organize_screenshots(self) -> Dict[str, List[Path]]:
        """
        Organize all screenshots by flow ID.

        Returns:
            Dictionary mapping flow IDs to screenshot paths
        """
        organized = {}

        for flow_dir in self.screenshots_dir.iterdir():
            if flow_dir.is_dir():
                flow_id = flow_dir.name
                screenshots = sorted(flow_dir.glob("*.png"))
                if screenshots:
                    organized[flow_id] = screenshots

        return organized

    def cleanup_old_results(self, days_old: int = 7) -> int:
        """
        Remove screenshots and videos older than specified days.

        Args:
            days_old: Number of days to keep results

        Returns:
            Number of files removed
        """
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(days=days_old)
        removed_count = 0

        # Clean screenshots
        for file in self.screenshots_dir.rglob("*"):
            if file.is_file():
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if file_time < cutoff_time:
                    file.unlink()
                    removed_count += 1

        # Clean videos
        if self.enable_video and self.videos_dir.exists():
            for file in self.videos_dir.rglob("*"):
                if file.is_file():
                    file_time = datetime.fromtimestamp(file.stat().st_mtime)
                    if file_time < cutoff_time:
                        file.unlink()
                        removed_count += 1

        return removed_count


def run_ux_tests(
    tests_dir: Path = Path("tests/ux_flows"),
    screenshots_dir: Path = Path("screenshots"),
    videos_dir: Path = Path("videos"),
    enable_video: bool = False,
    headless: bool = True,
    save_results: bool = True
) -> TestSuiteResult:
    """
    Convenience function to run all UX tests.

    Args:
        tests_dir: Directory containing test files
        screenshots_dir: Directory for screenshots
        videos_dir: Directory for videos
        enable_video: Whether to record videos
        headless: Whether to run headless
        save_results: Whether to save results to JSON

    Returns:
        TestSuiteResult with execution results
    """
    runner = PlaywrightTestRunner(
        tests_dir=tests_dir,
        screenshots_dir=screenshots_dir,
        videos_dir=videos_dir,
        enable_video=enable_video
    )

    suite_result = runner.run_all_tests(headless=headless)

    if save_results:
        results_file = runner.save_results(suite_result)
        print(f"\n💾 Results saved to: {results_file}")

    return suite_result


if __name__ == "__main__":
    # Example usage
    result = run_ux_tests(
        enable_video=False,
        headless=True,
        save_results=True
    )

    print(f"\n✨ Test suite completed!")
    print(f"   Pass rate: {result.pass_rate:.1f}%")
