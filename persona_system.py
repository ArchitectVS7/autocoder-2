"""
Persona System for Design Iteration

Provides a framework for defining, loading, and validating personas
that can review designs from different perspectives before coding begins.

Based on IMPLEMENTATION_PLAN.md Phase 4: Persona-Based Design Iteration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from pathlib import Path


class PersonaExpertiseArea(Enum):
    """Categories of expertise that personas can have."""
    ACCESSIBILITY = "accessibility"
    UX_DESIGN = "ux_design"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MOBILE = "mobile"
    BRAND_DESIGN = "brand_design"
    POWER_USER = "power_user"


@dataclass
class EvaluationCriterion:
    """A single criterion used by a persona to evaluate designs."""
    name: str
    weight: float  # 0.0 to 1.0
    description: str

    def __post_init__(self):
        """Validate criterion after initialization."""
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {self.weight}")
        if not self.name:
            raise ValueError("Criterion name cannot be empty")
        if not self.description:
            raise ValueError("Criterion description cannot be empty")


@dataclass
class SampleFeedback:
    """Sample feedback examples from a persona."""
    positive: str
    negative: str
    suggestion: str


@dataclass
class Persona:
    """
    Represents a user persona with specific expertise, biases, and evaluation criteria.

    Personas are used during design iteration to provide diverse perspectives
    on proposed designs before implementation begins.
    """
    id: str
    name: str
    age: int
    background: str
    expertise: List[str]
    bias: str
    personality: str
    typical_concerns: List[str]
    evaluation_rubric: Dict[str, EvaluationCriterion]
    sample_feedback: Optional[SampleFeedback] = None

    def __post_init__(self):
        """Validate persona after initialization."""
        if not self.id:
            raise ValueError("Persona ID cannot be empty")
        if not self.name:
            raise ValueError("Persona name cannot be empty")
        if self.age < 0:
            raise ValueError(f"Age must be non-negative, got {self.age}")
        if not self.expertise:
            raise ValueError("Persona must have at least one expertise area")
        if not self.evaluation_rubric:
            raise ValueError("Persona must have evaluation rubric")

        # Validate rubric weights sum to 1.0 (with tolerance for floating point)
        total_weight = sum(criterion.weight for criterion in self.evaluation_rubric.values())
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(
                f"Evaluation rubric weights must sum to 1.0, got {total_weight:.3f}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "background": self.background,
            "expertise": self.expertise,
            "bias": self.bias,
            "personality": self.personality,
            "typical_concerns": self.typical_concerns,
            "evaluation_rubric": {
                name: {
                    "weight": criterion.weight,
                    "description": criterion.description
                }
                for name, criterion in self.evaluation_rubric.items()
            },
            "sample_feedback": {
                "positive": self.sample_feedback.positive,
                "negative": self.sample_feedback.negative,
                "suggestion": self.sample_feedback.suggestion
            } if self.sample_feedback else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Persona":
        """Create persona from dictionary (JSON deserialization)."""
        # Convert evaluation rubric dict to EvaluationCriterion objects
        rubric = {}
        for name, criterion_data in data["evaluation_rubric"].items():
            rubric[name] = EvaluationCriterion(
                name=name,
                weight=criterion_data["weight"],
                description=criterion_data["description"]
            )

        # Convert sample feedback if present
        sample_feedback = None
        if data.get("sample_feedback"):
            sf_data = data["sample_feedback"]
            sample_feedback = SampleFeedback(
                positive=sf_data["positive"],
                negative=sf_data["negative"],
                suggestion=sf_data["suggestion"]
            )

        return cls(
            id=data["id"],
            name=data["name"],
            age=data["age"],
            background=data["background"],
            expertise=data["expertise"],
            bias=data["bias"],
            personality=data["personality"],
            typical_concerns=data["typical_concerns"],
            evaluation_rubric=rubric,
            sample_feedback=sample_feedback
        )


class PersonaLoader:
    """Loads and validates personas from JSON files."""

    def __init__(self, personas_dir: Optional[Path] = None):
        """
        Initialize persona loader.

        Args:
            personas_dir: Directory containing persona JSON files.
                         Defaults to ./personas/
        """
        if personas_dir is None:
            personas_dir = Path(__file__).parent / "personas"
        self.personas_dir = Path(personas_dir)
        self._cache: Dict[str, Persona] = {}

    def load_persona(self, persona_id: str) -> Persona:
        """
        Load a persona from JSON file.

        Args:
            persona_id: ID of the persona to load

        Returns:
            Persona object

        Raises:
            FileNotFoundError: If persona file doesn't exist
            ValueError: If persona JSON is invalid
        """
        # Check cache first
        if persona_id in self._cache:
            return self._cache[persona_id]

        # Load from file
        persona_file = self.personas_dir / f"{persona_id}.json"
        if not persona_file.exists():
            raise FileNotFoundError(f"Persona file not found: {persona_file}")

        with open(persona_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        persona = Persona.from_dict(data)

        # Cache for future use
        self._cache[persona_id] = persona

        return persona

    def load_all_personas(self) -> List[Persona]:
        """
        Load all personas from the personas directory.

        Returns:
            List of Persona objects
        """
        if not self.personas_dir.exists():
            return []

        personas = []
        for persona_file in self.personas_dir.glob("*.json"):
            persona_id = persona_file.stem
            try:
                persona = self.load_persona(persona_id)
                personas.append(persona)
            except Exception as e:
                print(f"Warning: Failed to load persona {persona_id}: {e}")

        return personas

    def save_persona(self, persona: Persona) -> Path:
        """
        Save a persona to JSON file.

        Args:
            persona: Persona to save

        Returns:
            Path to saved file
        """
        # Create personas directory if it doesn't exist
        self.personas_dir.mkdir(parents=True, exist_ok=True)

        persona_file = self.personas_dir / f"{persona.id}.json"

        with open(persona_file, 'w', encoding='utf-8') as f:
            json.dump(persona.to_dict(), f, indent=2, ensure_ascii=False)

        # Update cache
        self._cache[persona.id] = persona

        return persona_file

    def list_available_personas(self) -> List[str]:
        """
        List all available persona IDs.

        Returns:
            List of persona IDs
        """
        if not self.personas_dir.exists():
            return []

        return [f.stem for f in self.personas_dir.glob("*.json")]


class PersonaValidator:
    """Validates persona definitions against schema requirements."""

    @staticmethod
    def validate_persona(persona: Persona) -> tuple[bool, List[str]]:
        """
        Validate a persona against schema requirements.

        Args:
            persona: Persona to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Basic field validation (already done in __post_init__, but double-check)
        if not persona.id:
            errors.append("Persona ID is required")

        if not persona.name:
            errors.append("Persona name is required")

        if persona.age < 0:
            errors.append(f"Age must be non-negative, got {persona.age}")

        if not persona.background:
            errors.append("Background is required")

        if not persona.expertise:
            errors.append("At least one expertise area is required")

        if not persona.bias:
            errors.append("Bias description is required")

        if not persona.personality:
            errors.append("Personality description is required")

        if not persona.typical_concerns:
            errors.append("At least one typical concern is required")

        # Evaluation rubric validation
        if not persona.evaluation_rubric:
            errors.append("Evaluation rubric is required")
        else:
            total_weight = sum(c.weight for c in persona.evaluation_rubric.values())
            if not (0.99 <= total_weight <= 1.01):
                errors.append(
                    f"Evaluation rubric weights must sum to 1.0, got {total_weight:.3f}"
                )

            for criterion_name, criterion in persona.evaluation_rubric.items():
                if not criterion.name:
                    errors.append(f"Criterion name is required")
                if not criterion.description:
                    errors.append(f"Criterion '{criterion_name}' missing description")
                if not (0.0 <= criterion.weight <= 1.0):
                    errors.append(
                        f"Criterion '{criterion_name}' weight must be 0.0-1.0, "
                        f"got {criterion.weight}"
                    )

        # Sample feedback validation (optional but should be complete if present)
        if persona.sample_feedback:
            if not persona.sample_feedback.positive:
                errors.append("Sample feedback missing positive example")
            if not persona.sample_feedback.negative:
                errors.append("Sample feedback missing negative example")
            if not persona.sample_feedback.suggestion:
                errors.append("Sample feedback missing suggestion example")

        return (len(errors) == 0, errors)


def get_default_personas_dir() -> Path:
    """Get the default personas directory path."""
    return Path(__file__).parent / "personas"


def create_personas_directory() -> Path:
    """Create the personas directory if it doesn't exist."""
    personas_dir = get_default_personas_dir()
    personas_dir.mkdir(parents=True, exist_ok=True)
    return personas_dir
