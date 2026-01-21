"""
Tests for Phase 5 - Tasks 5.3, 5.4, 5.5, and 5.6

This test suite validates:
- Task 5.3: Visual QA Agent
- Task 5.4: Screenshot-Based UX Evaluation
- Task 5.5: Persona User Testing
- Task 5.6: UX Report Generator
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from PIL import Image

from ux_eval.visual_qa_agent import (
    VisualQAAgent,
    VisualIssue,
    ViewportAnalysis,
    VisualQAReport,
    analyze_screenshots
)

from ux_eval.ux_evaluator import (
    UXEvaluator,
    SpecialistFeedback,
    PersonaTestResult,
    UXEvaluationResult,
    FinalUXReport,
    AccessibilityAuditor,
    BrandConsistencyChecker,
    MobileUXSpecialist,
    OnboardingFlowAnalyst,
    run_complete_ux_evaluation
)


# ============================================================================
# Task 5.3: Visual QA Agent Tests
# ============================================================================

class TestVisualIssue:
    """Test the VisualIssue dataclass."""

    def test_create_visual_issue(self):
        """Test creating a VisualIssue instance."""
        issue = VisualIssue(
            issue_type="alignment",
            severity="warning",
            description="Button not aligned",
            screenshot_path=Path("/screenshots/step1.png")
        )

        assert issue.issue_type == "alignment"
        assert issue.severity == "warning"
        assert issue.description == "Button not aligned"

    def test_visual_issue_to_dict(self):
        """Test converting VisualIssue to dictionary."""
        issue = VisualIssue(
            issue_type="overflow",
            severity="critical",
            description="Content overflow detected",
            screenshot_path=Path("/screenshots/step1.png"),
            suggested_fix="Add overflow: hidden"
        )

        issue_dict = issue.to_dict()

        assert issue_dict["issue_type"] == "overflow"
        assert issue_dict["severity"] == "critical"
        assert issue_dict["suggested_fix"] == "Add overflow: hidden"


class TestViewportAnalysis:
    """Test the ViewportAnalysis dataclass."""

    def test_create_viewport_analysis(self):
        """Test creating ViewportAnalysis instance."""
        analysis = ViewportAnalysis(
            viewport_name="desktop",
            width=1920,
            height=1080
        )

        assert analysis.viewport_name == "desktop"
        assert analysis.width == 1920
        assert len(analysis.issues_found) == 0

    def test_add_issue_to_viewport(self):
        """Test adding issues to viewport analysis."""
        analysis = ViewportAnalysis(
            viewport_name="mobile",
            width=375,
            height=667
        )

        issue = VisualIssue(
            issue_type="spacing",
            severity="warning",
            description="Inconsistent spacing",
            screenshot_path=Path("/test.png")
        )

        analysis.add_issue(issue)

        assert len(analysis.issues_found) == 1
        assert analysis.issues_found[0].issue_type == "spacing"

    def test_critical_issues_property(self):
        """Test getting critical issues."""
        analysis = ViewportAnalysis(
            viewport_name="desktop",
            width=1920,
            height=1080
        )

        analysis.add_issue(VisualIssue(
            issue_type="overflow",
            severity="critical",
            description="Critical issue",
            screenshot_path=Path("/test.png")
        ))

        analysis.add_issue(VisualIssue(
            issue_type="spacing",
            severity="warning",
            description="Warning issue",
            screenshot_path=Path("/test.png")
        ))

        assert len(analysis.critical_issues) == 1
        assert len(analysis.warnings) == 1


class TestVisualQAReport:
    """Test the VisualQAReport dataclass."""

    def test_create_visual_qa_report(self):
        """Test creating a VisualQAReport."""
        report = VisualQAReport(flow_id="onboarding")

        assert report.flow_id == "onboarding"
        assert len(report.viewport_analyses) == 0

    def test_add_viewport_analysis(self):
        """Test adding viewport analysis to report."""
        report = VisualQAReport(flow_id="checkout")

        analysis = ViewportAnalysis(
            viewport_name="desktop",
            width=1920,
            height=1080
        )

        report.add_viewport_analysis(analysis)

        assert len(report.viewport_analyses) == 1

    def test_total_critical_issues(self):
        """Test counting total critical issues."""
        report = VisualQAReport(flow_id="test")

        analysis = ViewportAnalysis(
            viewport_name="desktop",
            width=1920,
            height=1080
        )

        analysis.add_issue(VisualIssue(
            issue_type="overflow",
            severity="critical",
            description="Critical",
            screenshot_path=Path("/test.png")
        ))

        report.add_viewport_analysis(analysis)

        assert report.total_critical_issues == 1


class TestVisualQAAgent:
    """Test the VisualQAAgent class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def agent(self, temp_dir):
        """Create VisualQAAgent instance."""
        return VisualQAAgent(screenshots_dir=temp_dir)

    @pytest.fixture
    def test_screenshot(self, temp_dir):
        """Create a test screenshot."""
        img = Image.new('RGB', (1920, 1080), color='white')
        screenshot_path = temp_dir / "test_screenshot.png"
        img.save(screenshot_path)
        return screenshot_path

    def test_agent_initialization(self, agent, temp_dir):
        """Test VisualQAAgent initialization."""
        assert agent.screenshots_dir == temp_dir

    def test_analyze_screenshot(self, agent, test_screenshot):
        """Test analyzing a single screenshot."""
        issues = agent.analyze_screenshot(test_screenshot, "desktop")

        assert isinstance(issues, list)

    def test_analyze_oversized_screenshot(self, agent, temp_dir):
        """Test detecting oversized screenshots."""
        # Create oversized image
        img = Image.new('RGB', (3000, 1080), color='white')
        screenshot_path = temp_dir / "oversized.png"
        img.save(screenshot_path)

        issues = agent.analyze_screenshot(screenshot_path, "desktop")

        # Should detect overflow
        overflow_issues = [i for i in issues if i.issue_type == "overflow"]
        assert len(overflow_issues) > 0

    def test_analyze_tiny_screenshot(self, agent, temp_dir):
        """Test detecting tiny screenshots (possible rendering failure)."""
        img = Image.new('RGB', (50, 50), color='white')
        screenshot_path = temp_dir / "tiny.png"
        img.save(screenshot_path)

        issues = agent.analyze_screenshot(screenshot_path, "desktop")

        # Should detect layout issue
        layout_issues = [i for i in issues if i.issue_type == "layout"]
        assert len(layout_issues) > 0
        assert any(i.severity == "critical" for i in layout_issues)

    def test_analyze_flow(self, agent, temp_dir):
        """Test analyzing complete user flow."""
        # Create flow directory with screenshots
        flow_dir = temp_dir / "test-flow"
        flow_dir.mkdir()

        for i in range(3):
            img = Image.new('RGB', (1920, 1080), color='white')
            img.save(flow_dir / f"step{i}.png")

        report = agent.analyze_flow("test-flow")

        assert report.flow_id == "test-flow"
        assert len(report.viewport_analyses) > 0

    def test_analyze_all_flows(self, agent, temp_dir):
        """Test analyzing all flows in directory."""
        # Create multiple flow directories
        for flow_id in ["flow1", "flow2"]:
            flow_dir = temp_dir / flow_id
            flow_dir.mkdir()
            img = Image.new('RGB', (1920, 1080), color='white')
            img.save(flow_dir / "step1.png")

        reports = agent.analyze_all_flows()

        assert len(reports) == 2
        assert "flow1" in reports
        assert "flow2" in reports

    def test_generate_report_markdown(self, agent):
        """Test generating markdown report."""
        report = VisualQAReport(flow_id="test")

        analysis = ViewportAnalysis(
            viewport_name="desktop",
            width=1920,
            height=1080,
            screenshots_analyzed=3
        )

        analysis.add_issue(VisualIssue(
            issue_type="spacing",
            severity="warning",
            description="Spacing issue",
            screenshot_path=Path("/test.png")
        ))

        report.add_viewport_analysis(analysis)

        markdown = agent.generate_report_markdown(report)

        assert "# Visual QA Report: test" in markdown
        assert "Desktop Viewport" in markdown
        assert "Spacing issue" in markdown

    def test_save_report(self, agent, temp_dir):
        """Test saving visual QA report."""
        report = VisualQAReport(flow_id="test")

        output_file = temp_dir / "visual_qa_report.md"
        saved_path = agent.save_report(report, output_file)

        assert saved_path.exists()
        content = saved_path.read_text()
        assert "# Visual QA Report" in content


# ============================================================================
# Task 5.4: Screenshot-Based UX Evaluation Tests
# ============================================================================

class TestSpecialistFeedback:
    """Test the SpecialistFeedback dataclass."""

    def test_create_specialist_feedback(self):
        """Test creating SpecialistFeedback."""
        feedback = SpecialistFeedback(
            specialist_type="accessibility",
            score=8,
            strengths=["Good contrast"],
            concerns=["Missing labels"],
            suggestions=["Add ARIA labels"]
        )

        assert feedback.specialist_type == "accessibility"
        assert feedback.score == 8
        assert len(feedback.strengths) == 1

    def test_specialist_feedback_to_dict(self):
        """Test converting feedback to dictionary."""
        feedback = SpecialistFeedback(
            specialist_type="mobile_ux",
            score=7
        )

        feedback_dict = feedback.to_dict()

        assert feedback_dict["specialist_type"] == "mobile_ux"
        assert feedback_dict["score"] == 7


class TestAccessibilityAuditor:
    """Test the AccessibilityAuditor specialist."""

    def test_evaluate_accessibility(self):
        """Test accessibility evaluation."""
        auditor = AccessibilityAuditor()

        screenshots = [Path("/screenshot1.png"), Path("/screenshot2.png")]
        feedback = auditor.evaluate(screenshots)

        assert feedback.specialist_type == "accessibility"
        assert 1 <= feedback.score <= 10
        assert isinstance(feedback.strengths, list)
        assert isinstance(feedback.concerns, list)


class TestBrandConsistencyChecker:
    """Test the BrandConsistencyChecker specialist."""

    def test_evaluate_brand_consistency(self):
        """Test brand consistency evaluation."""
        checker = BrandConsistencyChecker()

        screenshots = [Path("/screenshot1.png")]
        feedback = checker.evaluate(screenshots)

        assert feedback.specialist_type == "brand_consistency"
        assert 1 <= feedback.score <= 10


class TestMobileUXSpecialist:
    """Test the MobileUXSpecialist."""

    def test_evaluate_mobile_ux(self):
        """Test mobile UX evaluation."""
        specialist = MobileUXSpecialist()

        screenshots = [Path("/screenshot1.png")]
        feedback = specialist.evaluate(screenshots)

        assert feedback.specialist_type == "mobile_ux"
        assert 1 <= feedback.score <= 10


class TestOnboardingFlowAnalyst:
    """Test the OnboardingFlowAnalyst."""

    def test_evaluate_onboarding(self):
        """Test onboarding flow evaluation."""
        analyst = OnboardingFlowAnalyst()

        screenshots = [Path("/screenshot1.png")]
        feedback = analyst.evaluate(screenshots)

        assert feedback.specialist_type == "onboarding"
        assert 1 <= feedback.score <= 10


# ============================================================================
# Task 5.5: Persona User Testing Tests
# ============================================================================

class TestPersonaTestResult:
    """Test the PersonaTestResult dataclass."""

    def test_create_persona_result(self):
        """Test creating PersonaTestResult."""
        result = PersonaTestResult(
            persona_name="Sarah Chen",
            persona_role="Accessibility Advocate",
            would_use=True,
            reasoning="Good accessibility features"
        )

        assert result.persona_name == "Sarah Chen"
        assert result.would_use is True

    def test_persona_result_with_full_data(self):
        """Test PersonaTestResult with all fields."""
        result = PersonaTestResult(
            persona_name="Marcus Rodriguez",
            persona_role="Power User",
            would_use=True,
            reasoning="Fast and efficient",
            likes=["Speed", "Clean UI"],
            dislikes=["Missing shortcuts"],
            feature_requests=["Keyboard shortcuts"],
            ease_of_use_score=8,
            visual_appeal_score=9
        )

        assert len(result.likes) == 2
        assert result.ease_of_use_score == 8

    def test_persona_result_to_dict(self):
        """Test converting persona result to dictionary."""
        result = PersonaTestResult(
            persona_name="Elena Martinez",
            persona_role="Novice User",
            would_use=True,
            reasoning="Easy to learn"
        )

        result_dict = result.to_dict()

        assert result_dict["persona_name"] == "Elena Martinez"
        assert result_dict["would_use"] is True
        assert "scores" in result_dict


# ============================================================================
# Task 5.6: UX Report Generator Tests
# ============================================================================

class TestUXEvaluationResult:
    """Test the UXEvaluationResult dataclass."""

    def test_create_ux_evaluation_result(self):
        """Test creating UXEvaluationResult."""
        result = UXEvaluationResult(flow_id="onboarding")

        assert result.flow_id == "onboarding"
        assert len(result.specialist_feedback) == 0

    def test_add_specialist_feedback(self):
        """Test adding specialist feedback."""
        result = UXEvaluationResult(flow_id="test")

        feedback = SpecialistFeedback(
            specialist_type="accessibility",
            score=8
        )

        result.add_specialist_feedback(feedback)

        assert len(result.specialist_feedback) == 1

    def test_average_score_calculation(self):
        """Test calculating average score."""
        result = UXEvaluationResult(flow_id="test")

        result.add_specialist_feedback(SpecialistFeedback(
            specialist_type="accessibility",
            score=8
        ))

        result.add_specialist_feedback(SpecialistFeedback(
            specialist_type="mobile_ux",
            score=6
        ))

        assert result.average_score == 7.0

    def test_would_use_percentage(self):
        """Test calculating would-use percentage."""
        result = UXEvaluationResult(flow_id="test")

        result.add_persona_result(PersonaTestResult(
            persona_name="Test1",
            persona_role="User",
            would_use=True,
            reasoning="Good"
        ))

        result.add_persona_result(PersonaTestResult(
            persona_name="Test2",
            persona_role="User",
            would_use=False,
            reasoning="Not good"
        ))

        assert result.would_use_percentage == 50.0


class TestFinalUXReport:
    """Test the FinalUXReport dataclass."""

    def test_create_final_report(self):
        """Test creating FinalUXReport."""
        report = FinalUXReport(
            project_name="Test Project",
            executive_summary="Summary text"
        )

        assert report.project_name == "Test Project"
        assert report.executive_summary == "Summary text"

    def test_final_report_to_dict(self):
        """Test converting final report to dictionary."""
        report = FinalUXReport(
            project_name="Test",
            executive_summary="Summary",
            strengths=["Strength 1"],
            weaknesses=["Weakness 1"]
        )

        report_dict = report.to_dict()

        assert report_dict["project_name"] == "Test"
        assert len(report_dict["strengths"]) == 1


class TestUXEvaluator:
    """Test the UXEvaluator class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def evaluator(self, temp_dir):
        """Create UXEvaluator instance."""
        return UXEvaluator(screenshots_dir=temp_dir)

    def test_evaluator_initialization(self, evaluator, temp_dir):
        """Test UXEvaluator initialization."""
        assert evaluator.screenshots_dir == temp_dir
        assert evaluator.accessibility_auditor is not None
        assert evaluator.brand_checker is not None

    def test_evaluate_flow(self, evaluator, temp_dir):
        """Test evaluating a user flow."""
        # Create flow with screenshots
        flow_dir = temp_dir / "test-flow"
        flow_dir.mkdir()

        img = Image.new('RGB', (1920, 1080), color='white')
        img.save(flow_dir / "step1.png")

        result = evaluator.evaluate_flow("test-flow")

        assert result.flow_id == "test-flow"
        assert len(result.specialist_feedback) > 0

    def test_run_persona_testing(self, evaluator):
        """Test running persona testing."""
        screenshots = [Path("/screenshot1.png")]
        personas = evaluator.run_persona_testing("test-flow", screenshots)

        assert len(personas) > 0
        assert all(isinstance(p, PersonaTestResult) for p in personas)

    def test_generate_final_report(self, evaluator):
        """Test generating final UX report."""
        # Create mock evaluations
        evaluations = {
            "flow1": UXEvaluationResult(flow_id="flow1")
        }

        evaluations["flow1"].add_specialist_feedback(SpecialistFeedback(
            specialist_type="accessibility",
            score=8,
            strengths=["Good contrast"],
            concerns=["Missing labels"],
            suggestions=["Add ARIA labels"]
        ))

        evaluations["flow1"].add_persona_result(PersonaTestResult(
            persona_name="Test",
            persona_role="User",
            would_use=True,
            reasoning="Good",
            feature_requests=["Feature 1"]
        ))

        report = evaluator.generate_final_report(evaluations, "Test Project")

        assert report.project_name == "Test Project"
        assert report.overall_score > 0
        assert len(report.strengths) > 0

    def test_save_report_markdown(self, evaluator, temp_dir):
        """Test saving final report as markdown."""
        report = FinalUXReport(
            project_name="Test",
            executive_summary="Summary",
            overall_score=8.5
        )

        output_file = temp_dir / "report.md"
        saved_path = evaluator.save_report_markdown(report, output_file)

        assert saved_path.exists()
        content = saved_path.read_text()
        assert "# UX Evaluation Report" in content


class TestIntegration:
    """Integration tests for complete UX evaluation workflow."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_complete_evaluation_workflow(self, temp_dir):
        """Test complete UX evaluation from screenshots to final report."""
        # Create screenshots
        screenshots_dir = temp_dir / "screenshots"
        flow_dir = screenshots_dir / "onboarding"
        flow_dir.mkdir(parents=True)

        for i in range(3):
            img = Image.new('RGB', (1920, 1080), color='white')
            img.save(flow_dir / f"step{i}.png")

        # Run complete evaluation
        output_dir = temp_dir / "reports"
        report = run_complete_ux_evaluation(
            screenshots_dir=screenshots_dir,
            output_dir=output_dir,
            project_name="Test Project"
        )

        # Verify report
        assert report.project_name == "Test Project"
        assert report.overall_score > 0

        # Verify files created
        assert (output_dir / "UX_REPORT_FINAL.md").exists()
        assert (output_dir / "UX_REPORT_FINAL.json").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
