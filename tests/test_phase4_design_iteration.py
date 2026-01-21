"""
Test suite for Phase 4: Design Iteration System (Tasks 4.2-4.6)

Tests cover:
- Task 4.2: Design Iteration Agent
- Task 4.3: Persona Review Panel
- Task 4.4: Design Synthesis Agent
- Task 4.5: Convergence Detection
- Task 4.6: Design Review CLI
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from design.iteration import (
    DesignDocument,
    DesignIterationAgent,
    PersonaReviewPanel,
    PersonaFeedback,
    FeedbackSentiment,
    DesignSynthesisAgent,
    SynthesizedFeedback,
    ConvergenceDetector,
    MockupDescription,
    UserFlow,
    ComponentHierarchy
)
from design.persona_system import Persona, PersonaLoader, EvaluationCriterion


# ============================================================================
# Task 4.2: Design Iteration Agent
# ============================================================================

class TestDesignIterationAgent:
    """Test the Design Iteration Agent (Task 4.2)."""

    def test_create_agent_default_directory(self):
        """Test creating agent with default output directory."""
        agent = DesignIterationAgent()
        assert agent.output_dir.name == "design_iterations"

    def test_create_agent_custom_directory(self):
        """Test creating agent with custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DesignIterationAgent(Path(tmpdir))
            assert agent.output_dir == Path(tmpdir)

    def test_create_initial_design(self):
        """Test creating initial design from rough spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DesignIterationAgent(Path(tmpdir))
            design = agent.create_initial_design("Build a task management app", iteration=1)

            assert design.iteration == 1
            assert "Design Iteration 1" in design.title
            assert design.description
            assert len(design.mockups) > 0
            assert len(design.user_flows) > 0
            assert design.component_hierarchy is not None
            assert len(design.design_principles) > 0
            assert len(design.accessibility_considerations) > 0

    def test_create_next_iteration(self):
        """Test creating next iteration based on feedback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DesignIterationAgent(Path(tmpdir))

            # Create initial design
            design1 = agent.create_initial_design("Build a dashboard", iteration=1)

            # Create mock synthesized feedback
            synthesized = SynthesizedFeedback(
                iteration=1,
                common_themes={"positive": [], "concerns": [], "suggestions": []},
                conflicting_feedback=[],
                priority_changes=["Improve accessibility", "Add dark mode"],
                average_scores={"usability": 7.0},
                consensus_level=0.75
            )

            # Create next iteration
            design2 = agent.create_next_iteration(design1, synthesized)

            assert design2.iteration == 2
            assert design2.iteration > design1.iteration
            assert "Improve accessibility" in design2.description

    def test_save_and_load_design(self):
        """Test saving and loading design documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DesignIterationAgent(Path(tmpdir))

            # Create and save design
            original = agent.create_initial_design("Test spec", iteration=1)
            saved_path = agent.save_design(original)

            assert saved_path.exists()
            assert saved_path.name == "design_iteration_1.json"

            # Load design
            loaded = agent.load_design(1)

            assert loaded.iteration == original.iteration
            assert loaded.title == original.title
            assert len(loaded.mockups) == len(original.mockups)
            assert len(loaded.user_flows) == len(original.user_flows)

    def test_load_nonexistent_design(self):
        """Test loading non-existent design raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DesignIterationAgent(Path(tmpdir))

            with pytest.raises(FileNotFoundError, match="Design iteration 999 not found"):
                agent.load_design(999)

    def test_design_has_mockups(self):
        """Test that created designs include mockup descriptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DesignIterationAgent(Path(tmpdir))
            design = agent.create_initial_design("E-commerce site", iteration=1)

            assert len(design.mockups) > 0

            mockup = design.mockups[0]
            assert mockup.screen_name
            assert mockup.description
            assert mockup.layout
            assert len(mockup.components) > 0
            assert len(mockup.interactions) > 0

    def test_design_has_user_flows(self):
        """Test that created designs include user flow diagrams."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DesignIterationAgent(Path(tmpdir))
            design = agent.create_initial_design("Social media app", iteration=1)

            assert len(design.user_flows) > 0

            flow = design.user_flows[0]
            assert flow.name
            assert flow.description
            assert len(flow.steps) > 0
            assert isinstance(flow.decision_points, list)
            assert isinstance(flow.error_states, list)

    def test_design_has_component_hierarchy(self):
        """Test that created designs define component hierarchy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DesignIterationAgent(Path(tmpdir))
            design = agent.create_initial_design("Blog platform", iteration=1)

            assert design.component_hierarchy is not None
            assert design.component_hierarchy.name
            assert design.component_hierarchy.type
            assert isinstance(design.component_hierarchy.children, list)


# ============================================================================
# Task 4.3: Persona Review Panel
# ============================================================================

class TestPersonaReviewPanel:
    """Test the Persona Review Panel (Task 4.3)."""

    def test_create_review_panel(self):
        """Test creating review panel."""
        panel = PersonaReviewPanel()
        assert panel.persona_loader is not None

    def test_create_review_panel_with_custom_loader(self):
        """Test creating review panel with custom persona loader."""
        loader = PersonaLoader()
        panel = PersonaReviewPanel(loader)
        assert panel.persona_loader is loader

    def test_collect_feedback_with_default_personas(self):
        """Test collecting feedback from all default personas."""
        panel = PersonaReviewPanel()

        # Create sample design
        design = DesignDocument(
            iteration=1,
            title="Test Design",
            description="Test design with accessibility considerations",
            mockups=[],
            user_flows=[],
            component_hierarchy=ComponentHierarchy("App", "page"),
            design_principles=["Accessibility first"],
            accessibility_considerations=["WCAG 2.1 AA compliance", "Keyboard navigation"]
        )

        # Collect feedback
        feedback_list = panel.collect_feedback(design)

        # Should get feedback from all 7 built-in personas
        assert len(feedback_list) == 7

        for feedback in feedback_list:
            assert feedback.persona_id
            assert feedback.persona_name
            assert isinstance(feedback.sentiment, FeedbackSentiment)
            assert isinstance(feedback.likes, list)
            assert isinstance(feedback.concerns, list)
            assert isinstance(feedback.suggestions, list)
            assert isinstance(feedback.scores, dict)

    def test_collect_feedback_with_specific_personas(self):
        """Test collecting feedback from specific personas."""
        loader = PersonaLoader()
        panel = PersonaReviewPanel(loader)

        # Load specific personas
        personas = [
            loader.load_persona("accessibility_advocate"),
            loader.load_persona("power_user")
        ]

        design = DesignDocument(
            iteration=1,
            title="Test",
            description="Test",
            mockups=[],
            user_flows=[],
            component_hierarchy=ComponentHierarchy("App", "page"),
            design_principles=[],
            accessibility_considerations=[]
        )

        feedback_list = panel.collect_feedback(design, personas)

        assert len(feedback_list) == 2
        assert any(f.persona_id == "accessibility_advocate" for f in feedback_list)
        assert any(f.persona_id == "power_user" for f in feedback_list)

    def test_persona_feedback_has_scores(self):
        """Test that persona feedback includes criterion scores."""
        panel = PersonaReviewPanel()

        design = DesignDocument(
            iteration=1,
            title="Test",
            description="Test design",
            mockups=[],
            user_flows=[],
            component_hierarchy=ComponentHierarchy("App", "page"),
            design_principles=[],
            accessibility_considerations=[]
        )

        feedback_list = panel.collect_feedback(design)

        for feedback in feedback_list:
            assert len(feedback.scores) > 0
            for criterion, score in feedback.scores.items():
                assert isinstance(score, float)
                assert 0.0 <= score <= 10.0

    def test_save_feedback(self):
        """Test saving feedback to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            panel = PersonaReviewPanel()

            feedback_list = [
                PersonaFeedback(
                    persona_id="test_persona",
                    persona_name="Test User",
                    sentiment=FeedbackSentiment.POSITIVE,
                    likes=["Great design"],
                    concerns=[],
                    suggestions=["Keep going"],
                    scores={"usability": 8.5}
                )
            ]

            output_dir = Path(tmpdir)
            saved_path = panel.save_feedback(feedback_list, iteration=1, output_dir=output_dir)

            assert saved_path.exists()
            assert saved_path.name == "design_iteration_1_feedback.json"

            # Load and verify
            with open(saved_path, 'r') as f:
                data = json.load(f)

            assert data["iteration"] == 1
            assert len(data["feedback"]) == 1
            assert data["feedback"][0]["persona_id"] == "test_persona"

    def test_feedback_sentiment_reflects_concerns(self):
        """Test that feedback sentiment reflects number of concerns."""
        panel = PersonaReviewPanel()

        # Design without addressing concerns
        design = DesignDocument(
            iteration=1,
            title="Test",
            description="Basic design",
            mockups=[],
            user_flows=[],
            component_hierarchy=ComponentHierarchy("App", "page"),
            design_principles=[],
            accessibility_considerations=[]
        )

        feedback_list = panel.collect_feedback(design)

        # At least some personas should have concerns
        has_concerns = any(len(f.concerns) > 0 for f in feedback_list)
        assert has_concerns


# ============================================================================
# Task 4.4: Design Synthesis Agent
# ============================================================================

class TestDesignSynthesisAgent:
    """Test the Design Synthesis Agent (Task 4.4)."""

    def test_create_synthesis_agent(self):
        """Test creating synthesis agent."""
        agent = DesignSynthesisAgent()
        assert agent is not None

    def test_synthesize_feedback(self):
        """Test synthesizing feedback from multiple personas."""
        agent = DesignSynthesisAgent()

        feedback_list = [
            PersonaFeedback(
                persona_id="persona1",
                persona_name="Persona 1",
                sentiment=FeedbackSentiment.POSITIVE,
                likes=["Good accessibility"],
                concerns=["Slow performance"],
                suggestions=["Optimize images"],
                scores={"accessibility": 9.0, "performance": 6.0}
            ),
            PersonaFeedback(
                persona_id="persona2",
                persona_name="Persona 2",
                sentiment=FeedbackSentiment.NEUTRAL,
                likes=["Clean design"],
                concerns=["Slow performance", "Confusing navigation"],
                suggestions=["Improve performance", "Simplify menu"],
                scores={"accessibility": 7.0, "performance": 5.5}
            )
        ]

        synthesis = agent.synthesize_feedback(feedback_list, iteration=1)

        assert synthesis.iteration == 1
        assert "positive" in synthesis.common_themes
        assert "concerns" in synthesis.common_themes
        assert "suggestions" in synthesis.common_themes
        assert isinstance(synthesis.average_scores, dict)
        assert isinstance(synthesis.priority_changes, list)
        assert 0.0 <= synthesis.consensus_level <= 1.0

    def test_calculate_average_scores(self):
        """Test calculating average scores across personas."""
        agent = DesignSynthesisAgent()

        feedback_list = [
            PersonaFeedback(
                persona_id="p1",
                persona_name="P1",
                sentiment=FeedbackSentiment.POSITIVE,
                likes=[],
                concerns=[],
                suggestions=[],
                scores={"usability": 8.0, "aesthetics": 7.0}
            ),
            PersonaFeedback(
                persona_id="p2",
                persona_name="P2",
                sentiment=FeedbackSentiment.POSITIVE,
                likes=[],
                concerns=[],
                suggestions=[],
                scores={"usability": 6.0, "aesthetics": 9.0}
            )
        ]

        synthesis = agent.synthesize_feedback(feedback_list, iteration=1)

        assert synthesis.average_scores["usability"] == 7.0  # (8 + 6) / 2
        assert synthesis.average_scores["aesthetics"] == 8.0  # (7 + 9) / 2

    def test_consensus_level_high_agreement(self):
        """Test consensus level when personas agree."""
        agent = DesignSynthesisAgent()

        # All personas positive
        feedback_list = [
            PersonaFeedback(
                persona_id=f"p{i}",
                persona_name=f"P{i}",
                sentiment=FeedbackSentiment.POSITIVE,
                likes=["Great"],
                concerns=[],
                suggestions=[],
                scores={"test": 8.0}
            )
            for i in range(5)
        ]

        synthesis = agent.synthesize_feedback(feedback_list, iteration=1)

        # All personas agree (all positive) = high consensus
        assert synthesis.consensus_level == 1.0

    def test_consensus_level_disagreement(self):
        """Test consensus level when personas disagree."""
        agent = DesignSynthesisAgent()

        feedback_list = [
            PersonaFeedback(
                persona_id="p1",
                persona_name="P1",
                sentiment=FeedbackSentiment.POSITIVE,
                likes=[],
                concerns=[],
                suggestions=[],
                scores={}
            ),
            PersonaFeedback(
                persona_id="p2",
                persona_name="P2",
                sentiment=FeedbackSentiment.NEGATIVE,
                likes=[],
                concerns=[],
                suggestions=[],
                scores={}
            ),
            PersonaFeedback(
                persona_id="p3",
                persona_name="P3",
                sentiment=FeedbackSentiment.NEUTRAL,
                likes=[],
                concerns=[],
                suggestions=[],
                scores={}
            )
        ]

        synthesis = agent.synthesize_feedback(feedback_list, iteration=1)

        # Mixed sentiments = lower consensus
        assert synthesis.consensus_level < 1.0

    def test_identify_conflicts(self):
        """Test identifying conflicting feedback."""
        agent = DesignSynthesisAgent()

        # Create conflicting feedback
        feedback_list = [
            PersonaFeedback(
                persona_id="p1",
                persona_name="P1",
                sentiment=FeedbackSentiment.POSITIVE,
                likes=["Love it"],
                concerns=[],
                suggestions=[],
                scores={}
            ),
            PersonaFeedback(
                persona_id="p2",
                persona_name="P2",
                sentiment=FeedbackSentiment.NEGATIVE,
                likes=[],
                concerns=["Hate it"],
                suggestions=[],
                scores={}
            )
        ]

        synthesis = agent.synthesize_feedback(feedback_list, iteration=1)

        # Should detect sentiment divergence
        assert len(synthesis.conflicting_feedback) > 0
        assert any(
            "sentiment_divergence" in conflict.get("type", "")
            for conflict in synthesis.conflicting_feedback
        )

    def test_priority_changes_include_low_scores(self):
        """Test that priority changes include criteria with low scores."""
        agent = DesignSynthesisAgent()

        feedback_list = [
            PersonaFeedback(
                persona_id="p1",
                persona_name="P1",
                sentiment=FeedbackSentiment.NEUTRAL,
                likes=[],
                concerns=["Performance is slow"],
                suggestions=[],
                scores={"performance": 5.0, "usability": 9.0}  # Low performance score
            )
        ]

        synthesis = agent.synthesize_feedback(feedback_list, iteration=1)

        # Priority changes should include low-scoring criteria
        assert any(
            "performance" in change.lower()
            for change in synthesis.priority_changes
        )


# ============================================================================
# Task 4.5: Convergence Detection
# ============================================================================

class TestConvergenceDetector:
    """Test the Convergence Detector (Task 4.5)."""

    def test_create_detector_default_thresholds(self):
        """Test creating detector with default thresholds."""
        detector = ConvergenceDetector()
        assert detector.consensus_threshold == 0.8
        assert detector.min_score_threshold == 7.5
        assert detector.max_iterations == 4

    def test_create_detector_custom_thresholds(self):
        """Test creating detector with custom thresholds."""
        detector = ConvergenceDetector(
            consensus_threshold=0.9,
            min_score_threshold=8.0,
            max_iterations=5
        )
        assert detector.consensus_threshold == 0.9
        assert detector.min_score_threshold == 8.0
        assert detector.max_iterations == 5

    def test_converged_high_consensus_and_scores(self):
        """Test convergence with high consensus and scores."""
        detector = ConvergenceDetector()

        synthesis = SynthesizedFeedback(
            iteration=2,
            common_themes={"positive": [], "concerns": [], "suggestions": []},
            conflicting_feedback=[],
            priority_changes=[],
            average_scores={
                "usability": 8.5,
                "aesthetics": 8.0,
                "performance": 7.8
            },
            consensus_level=0.9  # High consensus
        )

        has_converged, reason = detector.has_converged(synthesis, iteration=2)

        assert has_converged
        assert "High consensus" in reason

    def test_not_converged_low_consensus(self):
        """Test not converged with low consensus."""
        detector = ConvergenceDetector()

        synthesis = SynthesizedFeedback(
            iteration=2,
            common_themes={"positive": [], "concerns": [], "suggestions": []},
            conflicting_feedback=[],
            priority_changes=["Fix navigation"],
            average_scores={"usability": 8.0},
            consensus_level=0.5  # Low consensus
        )

        has_converged, reason = detector.has_converged(synthesis, iteration=2)

        assert not has_converged
        assert "Consensus" in reason

    def test_not_converged_low_scores(self):
        """Test not converged with low scores despite high consensus."""
        detector = ConvergenceDetector()

        synthesis = SynthesizedFeedback(
            iteration=2,
            common_themes={"positive": [], "concerns": [], "suggestions": []},
            conflicting_feedback=[],
            priority_changes=["Improve performance"],
            average_scores={
                "usability": 6.0,  # Below threshold
                "performance": 5.5  # Below threshold
            },
            consensus_level=0.9  # High consensus
        )

        has_converged, reason = detector.has_converged(synthesis, iteration=2)

        # High consensus but low scores = not converged
        assert not has_converged

    def test_converged_max_iterations(self):
        """Test forced convergence at max iterations."""
        detector = ConvergenceDetector(max_iterations=4)

        synthesis = SynthesizedFeedback(
            iteration=4,
            common_themes={"positive": [], "concerns": [], "suggestions": []},
            conflicting_feedback=[],
            priority_changes=["Still need work"],
            average_scores={"usability": 6.0},
            consensus_level=0.5
        )

        has_converged, reason = detector.has_converged(synthesis, iteration=4)

        assert has_converged
        assert "Maximum iterations" in reason

    def test_converged_no_priority_changes(self):
        """Test convergence when no priority changes suggested."""
        detector = ConvergenceDetector()

        synthesis = SynthesizedFeedback(
            iteration=2,
            common_themes={"positive": [], "concerns": [], "suggestions": []},
            conflicting_feedback=[],
            priority_changes=[],  # No changes needed
            average_scores={"usability": 7.0},
            consensus_level=0.7
        )

        has_converged, reason = detector.has_converged(synthesis, iteration=2)

        assert has_converged
        assert "No priority changes" in reason or "stable" in reason.lower()

    def test_suggest_next_steps_converged(self):
        """Test suggesting next steps when converged."""
        detector = ConvergenceDetector()

        next_steps = detector.suggest_next_steps(has_converged=True, reason="High consensus")

        assert len(next_steps) > 0
        assert any("ready" in step.lower() for step in next_steps)
        assert any("development" in step.lower() for step in next_steps)

    def test_suggest_next_steps_not_converged(self):
        """Test suggesting next steps when not converged."""
        detector = ConvergenceDetector()

        next_steps = detector.suggest_next_steps(
            has_converged=False,
            reason="Need improvements"
        )

        assert len(next_steps) > 0
        assert any("iteration" in step.lower() or "continue" in step.lower() for step in next_steps)


# ============================================================================
# Task 4.6: Design Review CLI
# ============================================================================

class TestDesignReviewCLI:
    """Test the Design Review CLI tool (Task 4.6)."""

    def test_cli_imports(self):
        """Test that design_review module can be imported."""
        import design_review
        assert design_review.DesignReviewCLI is not None

    def test_create_cli_default_settings(self):
        """Test creating CLI with default settings."""
        from design_review import DesignReviewCLI

        with tempfile.TemporaryDirectory() as tmpdir:
            cli = DesignReviewCLI(output_dir=Path(tmpdir))

            assert cli.output_dir == Path(tmpdir)
            assert not cli.interactive
            assert not cli.auto

    def test_create_cli_interactive_mode(self):
        """Test creating CLI in interactive mode."""
        from design_review import DesignReviewCLI

        with tempfile.TemporaryDirectory() as tmpdir:
            cli = DesignReviewCLI(
                output_dir=Path(tmpdir),
                interactive=True
            )

            assert cli.interactive
            assert not cli.auto

    def test_create_cli_auto_mode(self):
        """Test creating CLI in auto mode."""
        from design_review import DesignReviewCLI

        with tempfile.TemporaryDirectory() as tmpdir:
            cli = DesignReviewCLI(
                output_dir=Path(tmpdir),
                auto=True
            )

            assert cli.auto
            assert not cli.interactive

    def test_cli_components_initialized(self):
        """Test that CLI initializes all required components."""
        from design_review import DesignReviewCLI

        with tempfile.TemporaryDirectory() as tmpdir:
            cli = DesignReviewCLI(output_dir=Path(tmpdir))

            assert cli.design_agent is not None
            assert cli.review_panel is not None
            assert cli.synthesis_agent is not None
            assert cli.convergence_detector is not None


# ============================================================================
# Data Structure Tests
# ============================================================================

class TestDataStructures:
    """Test data structures used in design iteration."""

    def test_mockup_description(self):
        """Test MockupDescription dataclass."""
        mockup = MockupDescription(
            screen_name="Dashboard",
            description="Main dashboard",
            layout="Grid layout",
            components=["Header", "Sidebar"],
            interactions=["Click", "Scroll"]
        )

        assert mockup.screen_name == "Dashboard"
        assert len(mockup.components) == 2

    def test_user_flow(self):
        """Test UserFlow dataclass."""
        flow = UserFlow(
            name="Login Flow",
            description="User login process",
            steps=["Enter email", "Enter password", "Click login"],
            decision_points=["Remember me?"],
            error_states=["Invalid credentials"]
        )

        assert flow.name == "Login Flow"
        assert len(flow.steps) == 3

    def test_component_hierarchy_to_dict(self):
        """Test ComponentHierarchy serialization."""
        hierarchy = ComponentHierarchy(
            name="App",
            type="page",
            children=[
                ComponentHierarchy(name="Header", type="component")
            ],
            props={"theme": "dark"}
        )

        data = hierarchy.to_dict()

        assert data["name"] == "App"
        assert data["type"] == "page"
        assert len(data["children"]) == 1
        assert data["props"]["theme"] == "dark"

    def test_component_hierarchy_from_dict(self):
        """Test ComponentHierarchy deserialization."""
        data = {
            "name": "Layout",
            "type": "layout",
            "children": [
                {"name": "Sidebar", "type": "component", "children": [], "props": {}}
            ],
            "props": {"width": "100%"}
        }

        hierarchy = ComponentHierarchy.from_dict(data)

        assert hierarchy.name == "Layout"
        assert hierarchy.type == "layout"
        assert len(hierarchy.children) == 1
        assert hierarchy.children[0].name == "Sidebar"

    def test_design_document_serialization(self):
        """Test DesignDocument to_dict and from_dict roundtrip."""
        original = DesignDocument(
            iteration=1,
            title="Test Design",
            description="Test",
            mockups=[
                MockupDescription(
                    screen_name="Home",
                    description="Homepage",
                    layout="Flex",
                    components=["Header"],
                    interactions=["Click"]
                )
            ],
            user_flows=[
                UserFlow(
                    name="Test Flow",
                    description="Test",
                    steps=["Step 1"],
                    decision_points=[],
                    error_states=[]
                )
            ],
            component_hierarchy=ComponentHierarchy("App", "page"),
            design_principles=["Principle 1"],
            accessibility_considerations=["Consideration 1"]
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = DesignDocument.from_dict(data)

        assert restored.iteration == original.iteration
        assert restored.title == original.title
        assert len(restored.mockups) == len(original.mockups)
        assert len(restored.user_flows) == len(original.user_flows)
        assert restored.component_hierarchy.name == original.component_hierarchy.name

    def test_persona_feedback_serialization(self):
        """Test PersonaFeedback to_dict and from_dict roundtrip."""
        original = PersonaFeedback(
            persona_id="test_id",
            persona_name="Test Name",
            sentiment=FeedbackSentiment.POSITIVE,
            likes=["Like 1"],
            concerns=["Concern 1"],
            suggestions=["Suggestion 1"],
            scores={"usability": 8.5}
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = PersonaFeedback.from_dict(data)

        assert restored.persona_id == original.persona_id
        assert restored.persona_name == original.persona_name
        assert restored.sentiment == original.sentiment
        assert restored.likes == original.likes
        assert restored.scores == original.scores


# ============================================================================
# Integration Tests
# ============================================================================

class TestDesignIterationIntegration:
    """Integration tests for complete design iteration workflow."""

    def test_complete_single_iteration(self):
        """Test complete workflow for single design iteration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # 1. Create initial design
            design_agent = DesignIterationAgent(output_dir / "designs")
            design = design_agent.create_initial_design("Build a todo app", iteration=1)
            design_agent.save_design(design)

            # 2. Collect persona feedback
            review_panel = PersonaReviewPanel()
            feedback_list = review_panel.collect_feedback(design)
            review_panel.save_feedback(feedback_list, iteration=1, output_dir=output_dir / "feedback")

            # 3. Synthesize feedback
            synthesis_agent = DesignSynthesisAgent()
            synthesis = synthesis_agent.synthesize_feedback(feedback_list, iteration=1)

            # 4. Check convergence
            convergence_detector = ConvergenceDetector()
            has_converged, reason = convergence_detector.has_converged(synthesis, iteration=1)

            # Verify all steps completed successfully
            assert design.iteration == 1
            assert len(feedback_list) == 7  # All built-in personas
            assert synthesis.iteration == 1
            assert isinstance(has_converged, bool)

    def test_multi_iteration_workflow(self):
        """Test workflow across multiple iterations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            design_agent = DesignIterationAgent(output_dir / "designs")
            review_panel = PersonaReviewPanel()
            synthesis_agent = DesignSynthesisAgent()
            convergence_detector = ConvergenceDetector(max_iterations=2)

            # Iteration 1
            design1 = design_agent.create_initial_design("E-commerce site", iteration=1)
            feedback1 = review_panel.collect_feedback(design1)
            synthesis1 = synthesis_agent.synthesize_feedback(feedback1, iteration=1)

            has_converged1, _ = convergence_detector.has_converged(synthesis1, iteration=1)

            # Iteration 2
            design2 = design_agent.create_next_iteration(design1, synthesis1)
            feedback2 = review_panel.collect_feedback(design2)
            synthesis2 = synthesis_agent.synthesize_feedback(feedback2, iteration=2)

            has_converged2, reason2 = convergence_detector.has_converged(synthesis2, iteration=2)

            # At iteration 2 with max_iterations=2, should converge
            assert has_converged2
            assert "Maximum iterations" in reason2
