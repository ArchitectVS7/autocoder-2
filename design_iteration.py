"""
Design Iteration System for Pre-Development Design Validation

Implements Phase 4 Tasks 4.2-4.5:
- Task 4.2: Design Iteration Agent (creates detailed design from rough spec)
- Task 4.3: Persona Review Panel (collects persona feedback)
- Task 4.4: Design Synthesis Agent (aggregates feedback, creates next iteration)
- Task 4.5: Convergence Detection (detects when design is ready)

Based on IMPLEMENTATION_PLAN.md Phase 4: Persona-Based Design Iteration
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from enum import Enum
import json
from datetime import datetime

from persona_system import Persona, PersonaLoader


class FeedbackSentiment(Enum):
    """Sentiment of persona feedback."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class PersonaFeedback:
    """Feedback from a single persona on a design iteration."""
    persona_id: str
    persona_name: str
    sentiment: FeedbackSentiment
    likes: List[str]  # What the persona likes
    concerns: List[str]  # What concerns the persona
    suggestions: List[str]  # Specific suggestions for improvement
    scores: Dict[str, float]  # Scores for each evaluation criterion (0.0-10.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "sentiment": self.sentiment.value,
            "likes": self.likes,
            "concerns": self.concerns,
            "suggestions": self.suggestions,
            "scores": self.scores
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonaFeedback":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            persona_id=data["persona_id"],
            persona_name=data["persona_name"],
            sentiment=FeedbackSentiment(data["sentiment"]),
            likes=data["likes"],
            concerns=data["concerns"],
            suggestions=data["suggestions"],
            scores=data["scores"]
        )


@dataclass
class UserFlow:
    """Represents a user flow diagram."""
    name: str
    description: str
    steps: List[str]  # Ordered list of steps
    decision_points: List[str]  # Where users make choices
    error_states: List[str]  # Possible error states


@dataclass
class ComponentHierarchy:
    """Defines component hierarchy for the design."""
    name: str
    type: str  # "page", "layout", "component", "utility"
    children: List["ComponentHierarchy"] = field(default_factory=list)
    props: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "type": self.type,
            "children": [child.to_dict() for child in self.children],
            "props": self.props
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComponentHierarchy":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            type=data["type"],
            children=[cls.from_dict(child) for child in data.get("children", [])],
            props=data.get("props", {})
        )


@dataclass
class MockupDescription:
    """Describes a mockup/wireframe."""
    screen_name: str
    description: str
    layout: str  # Text description of layout
    components: List[str]  # List of components on this screen
    interactions: List[str]  # User interactions available


@dataclass
class DesignDocument:
    """
    Complete design document for a single iteration.

    This represents the output of the Design Iteration Agent (Task 4.2).
    """
    iteration: int
    title: str
    description: str
    mockups: List[MockupDescription]
    user_flows: List[UserFlow]
    component_hierarchy: ComponentHierarchy
    design_principles: List[str]
    accessibility_considerations: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "iteration": self.iteration,
            "title": self.title,
            "description": self.description,
            "mockups": [
                {
                    "screen_name": m.screen_name,
                    "description": m.description,
                    "layout": m.layout,
                    "components": m.components,
                    "interactions": m.interactions
                }
                for m in self.mockups
            ],
            "user_flows": [
                {
                    "name": uf.name,
                    "description": uf.description,
                    "steps": uf.steps,
                    "decision_points": uf.decision_points,
                    "error_states": uf.error_states
                }
                for uf in self.user_flows
            ],
            "component_hierarchy": self.component_hierarchy.to_dict(),
            "design_principles": self.design_principles,
            "accessibility_considerations": self.accessibility_considerations,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DesignDocument":
        """Create from dictionary."""
        return cls(
            iteration=data["iteration"],
            title=data["title"],
            description=data["description"],
            mockups=[
                MockupDescription(
                    screen_name=m["screen_name"],
                    description=m["description"],
                    layout=m["layout"],
                    components=m["components"],
                    interactions=m["interactions"]
                )
                for m in data["mockups"]
            ],
            user_flows=[
                UserFlow(
                    name=uf["name"],
                    description=uf["description"],
                    steps=uf["steps"],
                    decision_points=uf["decision_points"],
                    error_states=uf["error_states"]
                )
                for uf in data["user_flows"]
            ],
            component_hierarchy=ComponentHierarchy.from_dict(data["component_hierarchy"]),
            design_principles=data["design_principles"],
            accessibility_considerations=data["accessibility_considerations"],
            created_at=data.get("created_at", datetime.now().isoformat())
        )


@dataclass
class DesignIterationResult:
    """Result from a complete design iteration (design + feedback)."""
    iteration: int
    design: DesignDocument
    feedback: List[PersonaFeedback]
    synthesized_feedback: Optional["SynthesizedFeedback"] = None


@dataclass
class SynthesizedFeedback:
    """Aggregated feedback from all personas (Task 4.4 output)."""
    iteration: int
    common_themes: Dict[str, List[str]]  # "positive", "concerns", "suggestions"
    conflicting_feedback: List[Dict[str, Any]]  # Conflicts and resolutions
    priority_changes: List[str]  # High-priority changes for next iteration
    average_scores: Dict[str, float]  # Average scores across all personas
    consensus_level: float  # 0.0-1.0, how much personas agree

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "iteration": self.iteration,
            "common_themes": self.common_themes,
            "conflicting_feedback": self.conflicting_feedback,
            "priority_changes": self.priority_changes,
            "average_scores": self.average_scores,
            "consensus_level": self.consensus_level
        }


class DesignIterationAgent:
    """
    Task 4.2: Design Iteration Agent

    Takes a rough spec and creates a detailed design document with:
    - Mockup descriptions
    - User flow diagrams
    - Component hierarchy
    - Design principles
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the Design Iteration Agent.

        Args:
            output_dir: Directory to save design documents (default: ./design_iterations/)
        """
        if output_dir is None:
            output_dir = Path("./design_iterations")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_initial_design(self, rough_spec: str, iteration: int = 1) -> DesignDocument:
        """
        Create initial detailed design from rough specification.

        This is a simplified version. In a real implementation, this would use
        an AI agent to generate the design based on the spec.

        Args:
            rough_spec: Rough specification text
            iteration: Iteration number (default: 1)

        Returns:
            DesignDocument with detailed design
        """
        # Parse rough spec (simplified - in reality would use AI agent)
        title = f"Design Iteration {iteration}"
        description = f"Detailed design based on: {rough_spec[:100]}..."

        # Create sample mockups
        mockups = [
            MockupDescription(
                screen_name="Dashboard",
                description="Main dashboard view showing key metrics",
                layout="Header with logo, sidebar navigation, main content area with cards",
                components=["Header", "Sidebar", "MetricCard", "ChartWidget"],
                interactions=["Navigate to different sections", "Filter data", "Export reports"]
            )
        ]

        # Create sample user flows
        user_flows = [
            UserFlow(
                name="User Onboarding",
                description="New user first-time experience",
                steps=[
                    "1. User arrives at landing page",
                    "2. User clicks 'Get Started'",
                    "3. User fills out registration form",
                    "4. User verifies email",
                    "5. User completes profile setup",
                    "6. User sees dashboard for first time"
                ],
                decision_points=["Choose plan type", "Skip profile setup"],
                error_states=["Email already exists", "Invalid email format", "Verification link expired"]
            )
        ]

        # Create component hierarchy
        component_hierarchy = ComponentHierarchy(
            name="App",
            type="page",
            children=[
                ComponentHierarchy(
                    name="Layout",
                    type="layout",
                    children=[
                        ComponentHierarchy(name="Header", type="component"),
                        ComponentHierarchy(name="Sidebar", type="component"),
                        ComponentHierarchy(name="MainContent", type="layout")
                    ]
                )
            ]
        )

        # Design principles
        design_principles = [
            "Mobile-first responsive design",
            "Consistent visual hierarchy",
            "Clear call-to-action buttons",
            "Minimal cognitive load"
        ]

        # Accessibility considerations
        accessibility_considerations = [
            "WCAG 2.1 AA compliance",
            "Keyboard navigation support",
            "Screen reader optimization",
            "Sufficient color contrast (4.5:1 minimum)"
        ]

        design = DesignDocument(
            iteration=iteration,
            title=title,
            description=description,
            mockups=mockups,
            user_flows=user_flows,
            component_hierarchy=component_hierarchy,
            design_principles=design_principles,
            accessibility_considerations=accessibility_considerations
        )

        return design

    def create_next_iteration(
        self,
        previous_design: DesignDocument,
        synthesized_feedback: SynthesizedFeedback
    ) -> DesignDocument:
        """
        Create next design iteration based on synthesized feedback.

        Args:
            previous_design: Previous design document
            synthesized_feedback: Aggregated feedback from personas

        Returns:
            New DesignDocument with improvements
        """
        # In real implementation, would use AI to incorporate feedback
        # For now, create modified version with feedback incorporated

        new_iteration = previous_design.iteration + 1

        # Incorporate priority changes into description
        improvements = ", ".join(synthesized_feedback.priority_changes[:3])
        description = f"{previous_design.description}\n\nImprovements in this iteration: {improvements}"

        # Create updated design (simplified)
        design = DesignDocument(
            iteration=new_iteration,
            title=f"Design Iteration {new_iteration}",
            description=description,
            mockups=previous_design.mockups,  # Would be updated in real implementation
            user_flows=previous_design.user_flows,
            component_hierarchy=previous_design.component_hierarchy,
            design_principles=previous_design.design_principles,
            accessibility_considerations=previous_design.accessibility_considerations
        )

        return design

    def save_design(self, design: DesignDocument) -> Path:
        """
        Save design document to file.

        Args:
            design: DesignDocument to save

        Returns:
            Path to saved file
        """
        filename = f"design_iteration_{design.iteration}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(design.to_dict(), f, indent=2, ensure_ascii=False)

        return filepath

    def load_design(self, iteration: int) -> DesignDocument:
        """
        Load design document from file.

        Args:
            iteration: Iteration number to load

        Returns:
            DesignDocument

        Raises:
            FileNotFoundError: If design file doesn't exist
        """
        filename = f"design_iteration_{iteration}.json"
        filepath = self.output_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Design iteration {iteration} not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return DesignDocument.from_dict(data)


class PersonaReviewPanel:
    """
    Task 4.3: Persona Review Panel

    Each persona reviews the current design iteration and provides feedback.
    """

    def __init__(self, persona_loader: Optional[PersonaLoader] = None):
        """
        Initialize the Persona Review Panel.

        Args:
            persona_loader: PersonaLoader instance (creates new if None)
        """
        if persona_loader is None:
            persona_loader = PersonaLoader()
        self.persona_loader = persona_loader

    def collect_feedback(
        self,
        design: DesignDocument,
        personas: Optional[List[Persona]] = None
    ) -> List[PersonaFeedback]:
        """
        Collect feedback from all personas on the design.

        In a real implementation, this would use AI agents to simulate
        each persona reviewing the design and providing feedback.

        Args:
            design: DesignDocument to review
            personas: List of personas (uses all built-in if None)

        Returns:
            List of PersonaFeedback from each persona
        """
        if personas is None:
            personas = self.persona_loader.load_all_personas()

        feedback_list = []

        for persona in personas:
            feedback = self._simulate_persona_review(design, persona)
            feedback_list.append(feedback)

        return feedback_list

    def _simulate_persona_review(self, design: DesignDocument, persona: Persona) -> PersonaFeedback:
        """
        Simulate a persona reviewing the design.

        In real implementation, would use AI agent with persona characteristics.
        For now, generates template feedback based on persona concerns.

        Args:
            design: Design to review
            persona: Persona doing the review

        Returns:
            PersonaFeedback
        """
        # Simulate feedback based on persona's typical concerns
        likes = []
        concerns = []
        suggestions = []
        scores = {}

        # Check if design addresses persona's concerns
        design_text = f"{design.description} {design.design_principles} {design.accessibility_considerations}"

        for concern in persona.typical_concerns[:3]:  # Check first 3 concerns
            if any(keyword in design_text.lower() for keyword in concern.lower().split()):
                likes.append(f"Good consideration of {concern.lower()}")
            else:
                concerns.append(f"Missing attention to {concern.lower()}")
                suggestions.append(f"Add more focus on {concern.lower()}")

        # Generate scores based on evaluation rubric
        for criterion_name, criterion in persona.evaluation_rubric.items():
            # Simplified scoring (real implementation would use AI)
            if any(keyword in design_text.lower() for keyword in criterion_name.split('_')):
                scores[criterion_name] = 8.0  # Good score if mentioned
            else:
                scores[criterion_name] = 6.0  # Average score if not mentioned

        # Determine sentiment
        if len(concerns) == 0:
            sentiment = FeedbackSentiment.POSITIVE
        elif len(concerns) > len(likes):
            sentiment = FeedbackSentiment.NEGATIVE
        else:
            sentiment = FeedbackSentiment.NEUTRAL

        return PersonaFeedback(
            persona_id=persona.id,
            persona_name=persona.name,
            sentiment=sentiment,
            likes=likes if likes else ["Design shows promise"],
            concerns=concerns if concerns else [],
            suggestions=suggestions if suggestions else ["Keep up the good work"],
            scores=scores
        )

    def save_feedback(self, feedback_list: List[PersonaFeedback], iteration: int, output_dir: Path) -> Path:
        """
        Save persona feedback to JSON file.

        Args:
            feedback_list: List of PersonaFeedback
            iteration: Design iteration number
            output_dir: Directory to save feedback

        Returns:
            Path to saved file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"design_iteration_{iteration}_feedback.json"
        filepath = output_dir / filename

        data = {
            "iteration": iteration,
            "feedback": [f.to_dict() for f in feedback_list],
            "timestamp": datetime.now().isoformat()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath


class DesignSynthesisAgent:
    """
    Task 4.4: Design Synthesis Agent

    Aggregates feedback from all personas, identifies common themes,
    resolves conflicts, and creates priority list for next iteration.
    """

    def synthesize_feedback(self, feedback_list: List[PersonaFeedback], iteration: int) -> SynthesizedFeedback:
        """
        Aggregate and synthesize feedback from all personas.

        Args:
            feedback_list: List of PersonaFeedback from all personas
            iteration: Current iteration number

        Returns:
            SynthesizedFeedback with aggregated insights
        """
        # Aggregate common themes
        all_likes = []
        all_concerns = []
        all_suggestions = []

        for feedback in feedback_list:
            all_likes.extend(feedback.likes)
            all_concerns.extend(feedback.concerns)
            all_suggestions.extend(feedback.suggestions)

        common_themes = {
            "positive": self._find_common_items(all_likes),
            "concerns": self._find_common_items(all_concerns),
            "suggestions": self._find_common_items(all_suggestions)
        }

        # Calculate average scores across all personas
        average_scores = self._calculate_average_scores(feedback_list)

        # Identify conflicting feedback
        conflicting_feedback = self._identify_conflicts(feedback_list)

        # Prioritize changes for next iteration
        priority_changes = self._prioritize_changes(common_themes, average_scores)

        # Calculate consensus level
        consensus_level = self._calculate_consensus(feedback_list)

        return SynthesizedFeedback(
            iteration=iteration,
            common_themes=common_themes,
            conflicting_feedback=conflicting_feedback,
            priority_changes=priority_changes,
            average_scores=average_scores,
            consensus_level=consensus_level
        )

    def _find_common_items(self, items: List[str], min_occurrences: int = 2) -> List[str]:
        """Find items that appear multiple times."""
        # Simplified: just take unique items for now
        # Real implementation would do semantic similarity matching
        unique_items = list(set(items))
        return unique_items[:5]  # Return top 5

    def _calculate_average_scores(self, feedback_list: List[PersonaFeedback]) -> Dict[str, float]:
        """Calculate average scores across all personas."""
        all_scores: Dict[str, List[float]] = {}

        for feedback in feedback_list:
            for criterion, score in feedback.scores.items():
                if criterion not in all_scores:
                    all_scores[criterion] = []
                all_scores[criterion].append(score)

        average_scores = {
            criterion: sum(scores) / len(scores)
            for criterion, scores in all_scores.items()
        }

        return average_scores

    def _identify_conflicts(self, feedback_list: List[PersonaFeedback]) -> List[Dict[str, Any]]:
        """Identify conflicting feedback from different personas."""
        conflicts = []

        # Simplified: check if some personas are positive while others are negative
        positive_count = sum(1 for f in feedback_list if f.sentiment == FeedbackSentiment.POSITIVE)
        negative_count = sum(1 for f in feedback_list if f.sentiment == FeedbackSentiment.NEGATIVE)

        if positive_count > 0 and negative_count > 0:
            conflicts.append({
                "type": "sentiment_divergence",
                "description": f"{positive_count} personas positive, {negative_count} negative",
                "resolution": "Prioritize feedback from personas most relevant to core use case"
            })

        return conflicts

    def _prioritize_changes(self, common_themes: Dict[str, List[str]], average_scores: Dict[str, float]) -> List[str]:
        """Prioritize changes for next iteration based on feedback."""
        priority_changes = []

        # Add top concerns as priority changes
        priority_changes.extend(common_themes["concerns"][:3])

        # Add suggestions for low-scoring criteria
        low_scoring = [
            f"Improve {criterion} (score: {score:.1f}/10)"
            for criterion, score in average_scores.items()
            if score < 7.0
        ]
        priority_changes.extend(low_scoring[:2])

        return priority_changes

    def _calculate_consensus(self, feedback_list: List[PersonaFeedback]) -> float:
        """
        Calculate consensus level (0.0-1.0) based on feedback agreement.

        Higher consensus = more personas agree on the design.
        """
        if not feedback_list:
            return 0.0

        # Calculate based on sentiment agreement
        sentiment_counts = {}
        for feedback in feedback_list:
            sentiment = feedback.sentiment
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

        max_agreement = max(sentiment_counts.values())
        consensus = max_agreement / len(feedback_list)

        return consensus


class ConvergenceDetector:
    """
    Task 4.5: Convergence Detection

    Detects when feedback becomes minimal and design is ready for development.
    Typically 2-4 iterations to convergence.
    """

    def __init__(
        self,
        consensus_threshold: float = 0.8,
        min_score_threshold: float = 7.5,
        max_iterations: int = 4
    ):
        """
        Initialize convergence detector.

        Args:
            consensus_threshold: Minimum consensus level to consider converged (default: 0.8)
            min_score_threshold: Minimum average score to consider converged (default: 7.5)
            max_iterations: Maximum iterations before forcing convergence (default: 4)
        """
        self.consensus_threshold = consensus_threshold
        self.min_score_threshold = min_score_threshold
        self.max_iterations = max_iterations

    def has_converged(
        self,
        synthesized_feedback: SynthesizedFeedback,
        iteration: int
    ) -> tuple[bool, str]:
        """
        Check if design has converged and is ready for development.

        Args:
            synthesized_feedback: Latest synthesized feedback
            iteration: Current iteration number

        Returns:
            Tuple of (has_converged, reason)
        """
        # Check max iterations
        if iteration >= self.max_iterations:
            return (True, f"Maximum iterations ({self.max_iterations}) reached")

        # Check consensus level
        if synthesized_feedback.consensus_level >= self.consensus_threshold:
            # Check average scores
            avg_score = sum(synthesized_feedback.average_scores.values()) / len(synthesized_feedback.average_scores)
            if avg_score >= self.min_score_threshold:
                return (
                    True,
                    f"High consensus ({synthesized_feedback.consensus_level:.1%}) "
                    f"and scores ({avg_score:.1f}/10)"
                )

        # Check if no priority changes
        if len(synthesized_feedback.priority_changes) == 0:
            return (True, "No priority changes suggested - design is stable")

        # Not converged yet
        return (
            False,
            f"Consensus: {synthesized_feedback.consensus_level:.1%}, "
            f"{len(synthesized_feedback.priority_changes)} changes needed"
        )

    def suggest_next_steps(self, has_converged: bool, reason: str) -> List[str]:
        """
        Suggest next steps based on convergence status.

        Args:
            has_converged: Whether design has converged
            reason: Reason for convergence status

        Returns:
            List of suggested next steps
        """
        if has_converged:
            return [
                "✅ Design is ready for development",
                "Save final design spec to project prompts directory",
                "Begin feature extraction and implementation"
            ]
        else:
            return [
                "Continue iteration based on persona feedback",
                "Address priority changes in next iteration",
                "Re-review with personas after improvements"
            ]
