#!/usr/bin/env python3
"""
Phase 2 Integration Tests
==========================

Integration tests for Phase 2: Benchmarking & Performance Metrics

Tests cover:
1. Metrics collection system
2. Real-time performance dashboard
3. Performance report generation
4. A/B testing framework
5. End-to-end workflows
"""

import pytest
import tempfile
import shutil
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

from metrics_collector import MetricsCollector, estimate_api_cost
from performance_dashboard import PerformanceDashboard
from report_generator import PerformanceReportGenerator
from benchmark_compare import BenchmarkComparator


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def metrics_collector(temp_project_dir):
    """Create a metrics collector for testing."""
    collector = MetricsCollector(temp_project_dir, "Test Project")
    yield collector
    collector.close()


class TestMetricsCollector:
    """Test metrics collection system."""

    def test_create_metrics_database(self, temp_project_dir):
        """Test database creation."""
        collector = MetricsCollector(temp_project_dir, "Test")

        # Check database was created
        db_path = temp_project_dir / "benchmarks" / "metrics.db"
        assert db_path.exists()

        # Check tables exist
        from sqlalchemy import inspect
        inspector = inspect(collector.engine)
        tables = inspector.get_table_names()

        assert "metrics_runs" in tables
        assert "metrics_sessions" in tables
        assert "metrics_features" in tables
        assert "metrics_interventions" in tables

        collector.close()

    def test_track_session(self, metrics_collector):
        """Test session tracking."""
        metrics_collector.start_session(1)

        assert metrics_collector.current_session is not None
        assert metrics_collector.current_session.session_number == 1
        assert metrics_collector.current_session.start_time is not None

        # Track some API calls
        metrics_collector.track_api_call(0.05)
        metrics_collector.track_api_call(0.03)

        # End session
        metrics_collector.end_session()

        assert metrics_collector.current_session.end_time is not None
        assert metrics_collector.current_session.api_calls == 2
        assert metrics_collector.current_session.api_cost == pytest.approx(0.08)

    def test_track_feature_completion(self, metrics_collector):
        """Test feature completion tracking."""
        metrics_collector.set_total_features(10)
        metrics_collector.start_session(1)

        # Track feature
        metrics_collector.start_feature(1)
        metrics_collector.track_feature_complete(
            feature_id=1,
            feature_name="Test Feature",
            first_try=True,
            attempts=1
        )

        # Check metrics
        assert metrics_collector.run.features_completed == 1
        assert metrics_collector.current_session.features_completed == 1

        features = list(metrics_collector.run.features)
        assert len(features) == 1
        assert features[0].feature_id == 1
        assert features[0].first_try_pass is True

    def test_track_intervention(self, metrics_collector):
        """Test intervention tracking."""
        metrics_collector.start_session(1)

        metrics_collector.track_intervention(
            intervention_type="blocker",
            description="Missing OAUTH_CLIENT_ID",
            resolution_time_seconds=120
        )

        interventions = list(metrics_collector.run.interventions)
        assert len(interventions) == 1
        assert interventions[0].intervention_type == "blocker"
        assert interventions[0].resolution_time_seconds == 120

    def test_calculate_velocity(self, metrics_collector):
        """Test velocity calculation."""
        metrics_collector.set_total_features(100)
        metrics_collector.start_session(1)

        # Simulate 10 features in quick succession
        for i in range(10):
            metrics_collector.start_feature(i)
            metrics_collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=True
            )

        velocity = metrics_collector.get_velocity()
        assert velocity > 0  # Should be high since we completed quickly

    def test_calculate_rates(self, metrics_collector):
        """Test success rate calculations."""
        metrics_collector.set_total_features(10)
        metrics_collector.start_session(1)

        # Track features: 6 first-try, 4 need fixes
        for i in range(10):
            first_try = i < 6
            metrics_collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=first_try,
                attempts=1 if first_try else 2
            )

        first_try_rate = metrics_collector.get_first_try_rate()
        assert first_try_rate == pytest.approx(60.0)

    def test_export_to_json(self, metrics_collector, temp_project_dir):
        """Test JSON export."""
        metrics_collector.set_total_features(5)
        metrics_collector.start_session(1)

        # Simulate some work
        for i in range(5):
            metrics_collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=True
            )

        metrics_collector.end_session()
        metrics_collector.complete_run()

        # Check JSON was created
        json_files = list((temp_project_dir / "benchmarks").glob("metrics_run_*.json"))
        assert len(json_files) == 1

        # Verify JSON content
        with open(json_files[0]) as f:
            data = json.load(f)

        assert "run" in data
        assert "sessions" in data
        assert "features" in data
        assert data["run"]["features_completed"] == 5

    def test_estimate_api_cost(self):
        """Test API cost estimation."""
        cost = estimate_api_cost("claude-sonnet-4-5", 1000, 500)
        assert cost > 0
        assert cost == pytest.approx(0.003 * 1 + 0.015 * 0.5)


class TestPerformanceDashboard:
    """Test real-time performance dashboard."""

    def test_create_dashboard(self, metrics_collector):
        """Test dashboard creation."""
        dashboard = PerformanceDashboard(metrics_collector)
        assert dashboard.metrics == metrics_collector

    def test_render_dashboard(self, metrics_collector):
        """Test dashboard rendering."""
        metrics_collector.set_total_features(10)
        metrics_collector.start_session(1)

        for i in range(5):
            metrics_collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=i % 2 == 0
            )

        dashboard = PerformanceDashboard(metrics_collector)
        table = dashboard.render()

        assert table is not None
        assert "AUTOCODER PERFORMANCE" in str(table)

    def test_render_compact(self, metrics_collector):
        """Test compact dashboard rendering."""
        metrics_collector.set_total_features(10)
        metrics_collector.start_session(1)

        for i in range(5):
            metrics_collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=True
            )

        dashboard = PerformanceDashboard(metrics_collector)
        panel = dashboard.render_compact()

        assert panel is not None

    def test_update_quality_metrics(self, metrics_collector):
        """Test updating quality metrics."""
        dashboard = PerformanceDashboard(metrics_collector)

        dashboard.update_quality_metrics(
            code_quality=87,
            test_coverage=82.5,
            accessibility="WCAG AA"
        )

        assert dashboard.code_quality_score == 87
        assert dashboard.test_coverage == 82.5
        assert dashboard.accessibility_score == "WCAG AA"


class TestReportGenerator:
    """Test performance report generation."""

    def test_generate_report(self, metrics_collector, temp_project_dir):
        """Test report generation."""
        # Simulate complete run
        metrics_collector.set_total_features(50)
        metrics_collector.start_session(1)

        for i in range(50):
            metrics_collector.start_feature(i)
            metrics_collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=(i % 2 == 0),
                attempts=1 if i % 2 == 0 else 2,
                was_skipped=(i % 10 == 0)
            )
            metrics_collector.track_api_call(0.05)

        metrics_collector.end_session()
        metrics_collector.complete_run()

        # Generate report
        generator = PerformanceReportGenerator(metrics_collector)
        report = generator.generate()

        # Verify report content
        assert "# Autocoder Performance Report" in report
        assert "## Summary" in report
        assert "## Comparison to Alternatives" in report
        assert "## ROI Analysis" in report
        assert "## Detailed Metrics" in report

    def test_save_report(self, metrics_collector, temp_project_dir):
        """Test saving report to file."""
        metrics_collector.set_total_features(10)
        metrics_collector.start_session(1)

        for i in range(10):
            metrics_collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=True
            )

        metrics_collector.end_session()
        metrics_collector.complete_run()

        # Generate and save report
        generator = PerformanceReportGenerator(metrics_collector)
        report_path = temp_project_dir / "benchmarks" / "report.md"
        generator.generate(report_path)

        # Verify file exists
        assert report_path.exists()
        content = report_path.read_text()
        assert "# Autocoder Performance Report" in content

    def test_calculate_roi(self, metrics_collector):
        """Test ROI calculation."""
        metrics_collector.set_total_features(50)
        metrics_collector.start_session(1)

        for i in range(50):
            metrics_collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=True
            )
            metrics_collector.track_api_call(0.05)

        metrics_collector.end_session()
        metrics_collector.complete_run()

        generator = PerformanceReportGenerator(metrics_collector)
        report = generator.generate()

        # Should include ROI section
        assert "ROI:" in report or "ROI Analysis" in report

    def test_identify_bottlenecks(self, metrics_collector):
        """Test bottleneck identification."""
        metrics_collector.set_total_features(50)
        metrics_collector.start_session(1)

        # Create scenario with many skips (bottleneck)
        for i in range(50):
            metrics_collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=(i < 10),  # Only 20% first-try
                was_skipped=(i >= 40)  # 20% skipped
            )

        metrics_collector.end_session()
        metrics_collector.complete_run()

        generator = PerformanceReportGenerator(metrics_collector)
        report = generator.generate()

        # Should identify bottlenecks
        assert "Bottleneck" in report or "high_skip_rate" in report or "low_first_try" in report


class TestBenchmarkComparator:
    """Test A/B testing framework."""

    def test_load_run_data(self, temp_project_dir):
        """Test loading run data from JSON."""
        # Create sample JSON
        data = {
            "run": {
                "id": 1,
                "project_name": "Test",
                "start_time": "2026-01-21T10:00:00",
                "end_time": "2026-01-21T12:00:00",
                "features_completed": 50,
                "total_features": 50,
            },
            "sessions": [{"api_cost": 2.5, "api_calls": 50}],
            "features": [{"first_try_pass": True, "was_skipped": False} for _ in range(50)],
            "interventions": [],
        }

        json_path = temp_project_dir / "test_run.json"
        json_path.write_text(json.dumps(data))

        comparator = BenchmarkComparator()
        loaded = comparator.load_run_data(json_path)

        assert loaded["run"]["features_completed"] == 50

    def test_calculate_metrics(self):
        """Test metrics calculation from run data."""
        data = {
            "run": {
                "start_time": "2026-01-21T10:00:00",
                "end_time": "2026-01-21T12:00:00",
                "features_completed": 50,
                "total_features": 50,
            },
            "sessions": [{"api_cost": 2.5, "api_calls": 50}],
            "features": [
                {"first_try_pass": i < 30, "was_skipped": i >= 45}
                for i in range(50)
            ],
            "interventions": [],
        }

        comparator = BenchmarkComparator()
        metrics = comparator.calculate_metrics(data)

        assert metrics["features_completed"] == 50
        assert metrics["runtime_hours"] == pytest.approx(2.0)
        assert metrics["velocity"] == pytest.approx(25.0)
        assert metrics["first_try_rate"] == pytest.approx(60.0)

    def test_estimate_baseline(self):
        """Test baseline estimation."""
        comparator = BenchmarkComparator()

        manual = comparator.estimate_baseline("manual", 50)
        assert manual["runtime_hours"] == pytest.approx(25.0)  # 50 features / 2 per hour
        assert manual["total_cost"] == 0.0
        assert manual["estimated"] is True

        claude_skill = comparator.estimate_baseline("claude_skill", 50)
        assert claude_skill["runtime_hours"] > manual["runtime_hours"]
        assert claude_skill["total_cost"] > 0

        cursor = comparator.estimate_baseline("cursor", 50)
        assert cursor["velocity"] > manual["velocity"]

    def test_compare_runs(self):
        """Test comparing two runs."""
        run1 = {
            "runtime_hours": 5.0,
            "features_completed": 50,
            "total_features": 50,
            "velocity": 10.0,
            "first_try_rate": 80.0,
            "skip_rate": 5.0,
            "total_cost": 25.0,
            "cost_per_feature": 0.5,
            "intervention_count": 3,
            "session_count": 2,
        }

        run2 = {
            "runtime_hours": 8.0,
            "features_completed": 50,
            "total_features": 50,
            "velocity": 6.25,
            "first_try_rate": 70.0,
            "skip_rate": 10.0,
            "total_cost": 30.0,
            "cost_per_feature": 0.6,
            "intervention_count": 5,
            "session_count": 3,
        }

        comparator = BenchmarkComparator()
        report = comparator.compare(run1, run2, "Autocoder", "Manual")

        assert "Autocoder vs Manual" in report
        assert "Winner:" in report

    def test_generate_markdown_comparison(self):
        """Test markdown comparison generation."""
        runs = [
            ("Autocoder", {
                "runtime_hours": 5.0,
                "total_cost": 25.0,
                "velocity": 10.0,
                "first_try_rate": 80.0,
                "skip_rate": 5.0,
                "intervention_count": 3,
            }),
            ("Manual", {
                "runtime_hours": 25.0,
                "total_cost": 0.0,
                "velocity": 2.0,
                "first_try_rate": 95.0,
                "skip_rate": 0.0,
                "intervention_count": 0,
            }),
        ]

        comparator = BenchmarkComparator()
        md = comparator.generate_markdown_comparison(runs)

        assert "# Benchmark Comparison" in md
        assert "| Metric |" in md
        assert "## Recommendation" in md


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_benchmarking_workflow(self, temp_project_dir):
        """Test complete workflow from collection to reporting."""
        # 1. Create collector and simulate run
        collector = MetricsCollector(temp_project_dir, "E2E Test")
        collector.set_total_features(20)

        # 2. Run session with features
        collector.start_session(1)

        for i in range(20):
            collector.start_feature(i)
            time.sleep(0.01)  # Small delay to test timing
            collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=(i % 3 != 0),  # 67% first-try
                attempts=1 if i % 3 != 0 else 2
            )
            collector.track_api_call(0.05)

        # Add an intervention
        collector.track_intervention(
            intervention_type="blocker",
            description="Test blocker",
            resolution_time_seconds=60
        )

        collector.end_session()
        collector.complete_run()

        # 3. Generate dashboard
        dashboard = PerformanceDashboard(collector)
        dashboard.update_quality_metrics(code_quality=88, test_coverage=85)
        table = dashboard.render()
        assert table is not None

        # 4. Generate report
        generator = PerformanceReportGenerator(collector)
        report_path = temp_project_dir / "benchmarks" / "REPORT.md"
        report = generator.generate(report_path)

        assert report_path.exists()
        assert "## ROI Analysis" in report

        # 5. Compare to baseline
        json_files = list((temp_project_dir / "benchmarks").glob("metrics_run_*.json"))
        assert len(json_files) == 1

        comparator = BenchmarkComparator()
        run_data = comparator.load_run_data(json_files[0])
        metrics = comparator.calculate_metrics(run_data)
        baseline = comparator.estimate_baseline("manual", 20)

        comparison = comparator.compare(metrics, baseline, "Autocoder", "Manual")
        assert "Winner:" in comparison

        collector.close()


def run_tests():
    """Run all tests with pytest."""
    import subprocess
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)
    return result.returncode == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
