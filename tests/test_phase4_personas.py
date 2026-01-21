"""
Test suite for Phase 4: Persona-Based Design Iteration

Tests cover:
- Task 4.1.1: JSON-based persona definitions
- Task 4.1.2: 7 built-in personas
- Task 4.1.3: Persona loader and validator
- Task 4.1.4: Persona schema with evaluation_rubric
"""

import pytest
import json
import tempfile
from pathlib import Path
from design.persona_system import (
    Persona,
    EvaluationCriterion,
    SampleFeedback,
    PersonaLoader,
    PersonaValidator,
    PersonaExpertiseArea,
    get_default_personas_dir,
    create_personas_directory
)


# ============================================================================
# Task 4.1.1: JSON-based Persona Definitions
# ============================================================================

class TestPersonaDataClass:
    """Test the Persona dataclass and its methods."""

    def test_create_basic_persona(self):
        """Test creating a basic persona with minimum required fields."""
        rubric = {
            "usability": EvaluationCriterion(
                name="usability",
                weight=0.6,
                description="How easy is it to use"
            ),
            "aesthetics": EvaluationCriterion(
                name="aesthetics",
                weight=0.4,
                description="How good it looks"
            )
        }

        persona = Persona(
            id="test_persona",
            name="Test User",
            age=30,
            background="Test background",
            expertise=["testing"],
            bias="Test bias",
            personality="Test personality",
            typical_concerns=["concern1"],
            evaluation_rubric=rubric
        )

        assert persona.id == "test_persona"
        assert persona.name == "Test User"
        assert persona.age == 30
        assert len(persona.evaluation_rubric) == 2

    def test_persona_validation_empty_id(self):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Persona ID cannot be empty"):
            Persona(
                id="",
                name="Test",
                age=30,
                background="bg",
                expertise=["test"],
                bias="bias",
                personality="personality",
                typical_concerns=["concern"],
                evaluation_rubric={
                    "test": EvaluationCriterion("test", 1.0, "desc")
                }
            )

    def test_persona_validation_empty_name(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Persona name cannot be empty"):
            Persona(
                id="test",
                name="",
                age=30,
                background="bg",
                expertise=["test"],
                bias="bias",
                personality="personality",
                typical_concerns=["concern"],
                evaluation_rubric={
                    "test": EvaluationCriterion("test", 1.0, "desc")
                }
            )

    def test_persona_validation_negative_age(self):
        """Test that negative age raises ValueError."""
        with pytest.raises(ValueError, match="Age must be non-negative"):
            Persona(
                id="test",
                name="Test",
                age=-5,
                background="bg",
                expertise=["test"],
                bias="bias",
                personality="personality",
                typical_concerns=["concern"],
                evaluation_rubric={
                    "test": EvaluationCriterion("test", 1.0, "desc")
                }
            )

    def test_persona_validation_no_expertise(self):
        """Test that empty expertise list raises ValueError."""
        with pytest.raises(ValueError, match="must have at least one expertise"):
            Persona(
                id="test",
                name="Test",
                age=30,
                background="bg",
                expertise=[],
                bias="bias",
                personality="personality",
                typical_concerns=["concern"],
                evaluation_rubric={
                    "test": EvaluationCriterion("test", 1.0, "desc")
                }
            )

    def test_persona_validation_no_rubric(self):
        """Test that empty rubric raises ValueError."""
        with pytest.raises(ValueError, match="must have evaluation rubric"):
            Persona(
                id="test",
                name="Test",
                age=30,
                background="bg",
                expertise=["test"],
                bias="bias",
                personality="personality",
                typical_concerns=["concern"],
                evaluation_rubric={}
            )

    def test_persona_validation_rubric_weights_sum(self):
        """Test that rubric weights must sum to 1.0."""
        with pytest.raises(ValueError, match="weights must sum to 1.0"):
            Persona(
                id="test",
                name="Test",
                age=30,
                background="bg",
                expertise=["test"],
                bias="bias",
                personality="personality",
                typical_concerns=["concern"],
                evaluation_rubric={
                    "test1": EvaluationCriterion("test1", 0.3, "desc"),
                    "test2": EvaluationCriterion("test2", 0.5, "desc")
                }
            )

    def test_persona_to_dict(self):
        """Test converting persona to dictionary."""
        rubric = {
            "usability": EvaluationCriterion("usability", 0.6, "Ease of use"),
            "aesthetics": EvaluationCriterion("aesthetics", 0.4, "Visual appeal")
        }

        sample_feedback = SampleFeedback(
            positive="Great design!",
            negative="Too complex",
            suggestion="Simplify the interface"
        )

        persona = Persona(
            id="test",
            name="Test",
            age=30,
            background="bg",
            expertise=["testing"],
            bias="bias",
            personality="personality",
            typical_concerns=["concern1", "concern2"],
            evaluation_rubric=rubric,
            sample_feedback=sample_feedback
        )

        persona_dict = persona.to_dict()

        assert persona_dict["id"] == "test"
        assert persona_dict["name"] == "Test"
        assert persona_dict["age"] == 30
        assert "evaluation_rubric" in persona_dict
        assert "usability" in persona_dict["evaluation_rubric"]
        assert persona_dict["evaluation_rubric"]["usability"]["weight"] == 0.6
        assert persona_dict["sample_feedback"]["positive"] == "Great design!"

    def test_persona_from_dict(self):
        """Test creating persona from dictionary."""
        persona_dict = {
            "id": "test",
            "name": "Test User",
            "age": 30,
            "background": "Test background",
            "expertise": ["testing", "qa"],
            "bias": "Test bias",
            "personality": "Test personality",
            "typical_concerns": ["concern1", "concern2"],
            "evaluation_rubric": {
                "usability": {
                    "weight": 0.6,
                    "description": "Ease of use"
                },
                "aesthetics": {
                    "weight": 0.4,
                    "description": "Visual appeal"
                }
            },
            "sample_feedback": {
                "positive": "Great!",
                "negative": "Too complex",
                "suggestion": "Simplify"
            }
        }

        persona = Persona.from_dict(persona_dict)

        assert persona.id == "test"
        assert persona.name == "Test User"
        assert persona.age == 30
        assert len(persona.expertise) == 2
        assert len(persona.evaluation_rubric) == 2
        assert persona.evaluation_rubric["usability"].weight == 0.6
        assert persona.sample_feedback.positive == "Great!"

    def test_persona_from_dict_no_sample_feedback(self):
        """Test creating persona from dict without sample feedback."""
        persona_dict = {
            "id": "test",
            "name": "Test",
            "age": 30,
            "background": "bg",
            "expertise": ["test"],
            "bias": "bias",
            "personality": "personality",
            "typical_concerns": ["concern"],
            "evaluation_rubric": {
                "test": {
                    "weight": 1.0,
                    "description": "desc"
                }
            }
        }

        persona = Persona.from_dict(persona_dict)
        assert persona.sample_feedback is None

    def test_persona_json_serialization_roundtrip(self):
        """Test full JSON serialization/deserialization roundtrip."""
        rubric = {
            "test": EvaluationCriterion("test", 1.0, "description")
        }

        original = Persona(
            id="test",
            name="Test",
            age=30,
            background="bg",
            expertise=["testing"],
            bias="bias",
            personality="personality",
            typical_concerns=["concern"],
            evaluation_rubric=rubric
        )

        # to dict -> JSON -> dict -> Persona
        persona_dict = original.to_dict()
        json_str = json.dumps(persona_dict)
        loaded_dict = json.loads(json_str)
        restored = Persona.from_dict(loaded_dict)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.age == original.age


class TestEvaluationCriterion:
    """Test the EvaluationCriterion dataclass."""

    def test_create_valid_criterion(self):
        """Test creating a valid evaluation criterion."""
        criterion = EvaluationCriterion(
            name="usability",
            weight=0.5,
            description="How easy it is to use"
        )

        assert criterion.name == "usability"
        assert criterion.weight == 0.5
        assert criterion.description == "How easy it is to use"

    def test_criterion_weight_validation_too_low(self):
        """Test that weight < 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
            EvaluationCriterion(
                name="test",
                weight=-0.1,
                description="desc"
            )

    def test_criterion_weight_validation_too_high(self):
        """Test that weight > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
            EvaluationCriterion(
                name="test",
                weight=1.5,
                description="desc"
            )

    def test_criterion_empty_name(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Criterion name cannot be empty"):
            EvaluationCriterion(
                name="",
                weight=0.5,
                description="desc"
            )

    def test_criterion_empty_description(self):
        """Test that empty description raises ValueError."""
        with pytest.raises(ValueError, match="Criterion description cannot be empty"):
            EvaluationCriterion(
                name="test",
                weight=0.5,
                description=""
            )


# ============================================================================
# Task 4.1.2: 7 Built-in Personas
# ============================================================================

class TestBuiltInPersonas:
    """Test that all 7 built-in personas are correctly defined."""

    def test_all_personas_exist(self):
        """Test that all 7 persona JSON files exist."""
        personas_dir = get_default_personas_dir()

        expected_personas = [
            "accessibility_advocate",
            "power_user",
            "novice_user",
            "mobile_first",
            "brand_aesthetics",
            "security_conscious",
            "performance_optimizer"
        ]

        for persona_id in expected_personas:
            persona_file = personas_dir / f"{persona_id}.json"
            assert persona_file.exists(), f"Missing persona file: {persona_id}.json"

    def test_load_sarah_accessibility_advocate(self):
        """Test loading Sarah Chen (Accessibility Advocate) persona."""
        loader = PersonaLoader()
        persona = loader.load_persona("accessibility_advocate")

        assert persona.id == "accessibility_advocate"
        assert persona.name == "Sarah Chen"
        assert persona.age == 34
        assert "WCAG" in " ".join(persona.expertise)
        assert "keyboard_navigation" in persona.evaluation_rubric
        assert "screen_reader" in persona.evaluation_rubric
        assert "color_contrast" in persona.evaluation_rubric
        assert "semantic_html" in persona.evaluation_rubric

        # Verify rubric weights sum to 1.0
        total_weight = sum(c.weight for c in persona.evaluation_rubric.values())
        assert 0.99 <= total_weight <= 1.01

    def test_load_marcus_power_user(self):
        """Test loading Marcus Rodriguez (Power User) persona."""
        loader = PersonaLoader()
        persona = loader.load_persona("power_user")

        assert persona.id == "power_user"
        assert persona.name == "Marcus Rodriguez"
        assert persona.age == 29
        assert "Keyboard shortcuts" in persona.expertise
        assert "efficiency" in persona.evaluation_rubric
        assert "bulk_operations" in persona.evaluation_rubric

        total_weight = sum(c.weight for c in persona.evaluation_rubric.values())
        assert 0.99 <= total_weight <= 1.01

    def test_load_elena_novice_user(self):
        """Test loading Elena Martinez (Novice User) persona."""
        loader = PersonaLoader()
        persona = loader.load_persona("novice_user")

        assert persona.id == "novice_user"
        assert persona.name == "Elena Martinez"
        assert persona.age == 42
        assert "onboarding" in persona.evaluation_rubric
        assert "clarity" in persona.evaluation_rubric
        assert "safety" in persona.evaluation_rubric

        total_weight = sum(c.weight for c in persona.evaluation_rubric.values())
        assert 0.99 <= total_weight <= 1.01

    def test_load_david_mobile_first(self):
        """Test loading David Kim (Mobile-First User) persona."""
        loader = PersonaLoader()
        persona = loader.load_persona("mobile_first")

        assert persona.id == "mobile_first"
        assert persona.name == "David Kim"
        assert persona.age == 26
        assert "touch_optimization" in persona.evaluation_rubric
        assert "responsiveness" in persona.evaluation_rubric
        assert "performance" in persona.evaluation_rubric

        total_weight = sum(c.weight for c in persona.evaluation_rubric.values())
        assert 0.99 <= total_weight <= 1.01

    def test_load_aisha_brand_aesthetics(self):
        """Test loading Aisha Patel (Brand/Aesthetics) persona."""
        loader = PersonaLoader()
        persona = loader.load_persona("brand_aesthetics")

        assert persona.id == "brand_aesthetics"
        assert persona.name == "Aisha Patel"
        assert persona.age == 31
        assert "visual_hierarchy" in persona.evaluation_rubric
        assert "brand_consistency" in persona.evaluation_rubric
        assert "aesthetics" in persona.evaluation_rubric

        total_weight = sum(c.weight for c in persona.evaluation_rubric.values())
        assert 0.99 <= total_weight <= 1.01

    def test_load_raj_security_conscious(self):
        """Test loading Raj Sharma (Security Conscious) persona."""
        loader = PersonaLoader()
        persona = loader.load_persona("security_conscious")

        assert persona.id == "security_conscious"
        assert persona.name == "Raj Sharma"
        assert persona.age == 38
        assert "authentication" in persona.evaluation_rubric
        assert "data_protection" in persona.evaluation_rubric
        assert "privacy_compliance" in persona.evaluation_rubric

        total_weight = sum(c.weight for c in persona.evaluation_rubric.values())
        assert 0.99 <= total_weight <= 1.01

    def test_load_lisa_performance_optimizer(self):
        """Test loading Lisa Johnson (Performance Optimizer) persona."""
        loader = PersonaLoader()
        persona = loader.load_persona("performance_optimizer")

        assert persona.id == "performance_optimizer"
        assert persona.name == "Lisa Johnson"
        assert persona.age == 35
        assert "load_time" in persona.evaluation_rubric
        assert "bundle_size" in persona.evaluation_rubric
        assert "resource_optimization" in persona.evaluation_rubric

        total_weight = sum(c.weight for c in persona.evaluation_rubric.values())
        assert 0.99 <= total_weight <= 1.01

    def test_all_personas_have_sample_feedback(self):
        """Test that all built-in personas include sample feedback."""
        loader = PersonaLoader()

        all_persona_ids = [
            "accessibility_advocate",
            "power_user",
            "novice_user",
            "mobile_first",
            "brand_aesthetics",
            "security_conscious",
            "performance_optimizer"
        ]

        for persona_id in all_persona_ids:
            persona = loader.load_persona(persona_id)
            assert persona.sample_feedback is not None, f"{persona_id} missing sample feedback"
            assert persona.sample_feedback.positive
            assert persona.sample_feedback.negative
            assert persona.sample_feedback.suggestion

    def test_all_personas_have_typical_concerns(self):
        """Test that all personas have at least 5 typical concerns."""
        loader = PersonaLoader()

        all_persona_ids = [
            "accessibility_advocate",
            "power_user",
            "novice_user",
            "mobile_first",
            "brand_aesthetics",
            "security_conscious",
            "performance_optimizer"
        ]

        for persona_id in all_persona_ids:
            persona = loader.load_persona(persona_id)
            assert len(persona.typical_concerns) >= 5, \
                f"{persona_id} should have at least 5 concerns, has {len(persona.typical_concerns)}"


# ============================================================================
# Task 4.1.3: Persona Loader and Validator
# ============================================================================

class TestPersonaLoader:
    """Test the PersonaLoader class."""

    def test_create_loader_default_directory(self):
        """Test creating loader with default directory."""
        loader = PersonaLoader()
        assert loader.personas_dir == get_default_personas_dir()

    def test_create_loader_custom_directory(self):
        """Test creating loader with custom directory."""
        custom_dir = Path("/tmp/custom_personas")
        loader = PersonaLoader(custom_dir)
        assert loader.personas_dir == custom_dir

    def test_load_persona_caching(self):
        """Test that personas are cached after first load."""
        loader = PersonaLoader()

        # First load
        persona1 = loader.load_persona("accessibility_advocate")

        # Second load (should come from cache)
        persona2 = loader.load_persona("accessibility_advocate")

        # Should be the same object (cached)
        assert persona1 is persona2

    def test_load_persona_not_found(self):
        """Test loading non-existent persona raises FileNotFoundError."""
        loader = PersonaLoader()

        with pytest.raises(FileNotFoundError, match="Persona file not found"):
            loader.load_persona("nonexistent_persona")

    def test_load_all_personas(self):
        """Test loading all personas from directory."""
        loader = PersonaLoader()
        personas = loader.load_all_personas()

        # Should have exactly 7 built-in personas
        assert len(personas) == 7

        # Verify all expected personas are present
        persona_ids = {p.id for p in personas}
        expected_ids = {
            "accessibility_advocate",
            "power_user",
            "novice_user",
            "mobile_first",
            "brand_aesthetics",
            "security_conscious",
            "performance_optimizer"
        }
        assert persona_ids == expected_ids

    def test_save_and_load_persona(self):
        """Test saving and loading a custom persona."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PersonaLoader(Path(tmpdir))

            # Create custom persona
            rubric = {
                "test": EvaluationCriterion("test", 1.0, "Test criterion")
            }
            persona = Persona(
                id="custom_test",
                name="Custom Tester",
                age=30,
                background="Test background",
                expertise=["testing"],
                bias="Test bias",
                personality="Test personality",
                typical_concerns=["concern1"],
                evaluation_rubric=rubric
            )

            # Save persona
            saved_path = loader.save_persona(persona)
            assert saved_path.exists()

            # Load persona
            loaded = loader.load_persona("custom_test")
            assert loaded.id == "custom_test"
            assert loaded.name == "Custom Tester"

    def test_list_available_personas(self):
        """Test listing available persona IDs."""
        loader = PersonaLoader()
        persona_ids = loader.list_available_personas()

        assert len(persona_ids) == 7
        assert "accessibility_advocate" in persona_ids
        assert "power_user" in persona_ids


class TestPersonaValidator:
    """Test the PersonaValidator class."""

    def test_validate_valid_persona(self):
        """Test validating a valid persona."""
        rubric = {
            "test": EvaluationCriterion("test", 1.0, "Test")
        }
        persona = Persona(
            id="test",
            name="Test",
            age=30,
            background="bg",
            expertise=["test"],
            bias="bias",
            personality="personality",
            typical_concerns=["concern"],
            evaluation_rubric=rubric
        )

        is_valid, errors = PersonaValidator.validate_persona(persona)
        assert is_valid
        assert len(errors) == 0

    def test_validate_built_in_personas(self):
        """Test that all built-in personas are valid."""
        loader = PersonaLoader()
        personas = loader.load_all_personas()

        for persona in personas:
            is_valid, errors = PersonaValidator.validate_persona(persona)
            assert is_valid, f"{persona.id} validation failed: {errors}"
            assert len(errors) == 0

    def test_validate_invalid_rubric_weights(self):
        """Test validation catches invalid rubric weight sums."""
        # This should fail during Persona creation itself
        with pytest.raises(ValueError):
            rubric = {
                "test1": EvaluationCriterion("test1", 0.3, "Test"),
                "test2": EvaluationCriterion("test2", 0.5, "Test")
            }
            Persona(
                id="test",
                name="Test",
                age=30,
                background="bg",
                expertise=["test"],
                bias="bias",
                personality="personality",
                typical_concerns=["concern"],
                evaluation_rubric=rubric
            )


# ============================================================================
# Task 4.1.4: Persona Schema with evaluation_rubric
# ============================================================================

class TestEvaluationRubric:
    """Test evaluation rubric functionality."""

    def test_rubric_with_multiple_criteria(self):
        """Test creating rubric with multiple weighted criteria."""
        rubric = {
            "usability": EvaluationCriterion("usability", 0.4, "Ease of use"),
            "aesthetics": EvaluationCriterion("aesthetics", 0.3, "Visual appeal"),
            "performance": EvaluationCriterion("performance", 0.3, "Speed")
        }

        persona = Persona(
            id="test",
            name="Test",
            age=30,
            background="bg",
            expertise=["test"],
            bias="bias",
            personality="personality",
            typical_concerns=["concern"],
            evaluation_rubric=rubric
        )

        assert len(persona.evaluation_rubric) == 3
        assert persona.evaluation_rubric["usability"].weight == 0.4

    def test_rubric_weights_distribution(self):
        """Test various valid weight distributions."""
        test_cases = [
            # Equal weights
            {
                "c1": EvaluationCriterion("c1", 0.25, "d"),
                "c2": EvaluationCriterion("c2", 0.25, "d"),
                "c3": EvaluationCriterion("c3", 0.25, "d"),
                "c4": EvaluationCriterion("c4", 0.25, "d")
            },
            # Weighted priorities
            {
                "high": EvaluationCriterion("high", 0.5, "d"),
                "medium": EvaluationCriterion("medium", 0.3, "d"),
                "low": EvaluationCriterion("low", 0.2, "d")
            },
            # Single criterion
            {
                "only": EvaluationCriterion("only", 1.0, "d")
            }
        ]

        for rubric in test_cases:
            persona = Persona(
                id="test",
                name="Test",
                age=30,
                background="bg",
                expertise=["test"],
                bias="bias",
                personality="personality",
                typical_concerns=["concern"],
                evaluation_rubric=rubric
            )
            # If we got here, validation passed
            assert persona is not None

    def test_rubric_serialization_preserves_weights(self):
        """Test that rubric weights are preserved through serialization."""
        rubric = {
            "usability": EvaluationCriterion("usability", 0.35, "Ease"),
            "aesthetics": EvaluationCriterion("aesthetics", 0.35, "Look"),
            "performance": EvaluationCriterion("performance", 0.3, "Speed")
        }

        persona = Persona(
            id="test",
            name="Test",
            age=30,
            background="bg",
            expertise=["test"],
            bias="bias",
            personality="personality",
            typical_concerns=["concern"],
            evaluation_rubric=rubric
        )

        # Serialize and deserialize
        persona_dict = persona.to_dict()
        restored = Persona.from_dict(persona_dict)

        # Verify weights preserved
        assert restored.evaluation_rubric["usability"].weight == 0.35
        assert restored.evaluation_rubric["aesthetics"].weight == 0.35
        assert restored.evaluation_rubric["performance"].weight == 0.3

    def test_built_in_personas_rubric_coverage(self):
        """Test that built-in personas have appropriate rubric coverage."""
        loader = PersonaLoader()

        # Map persona to expected rubric criteria count
        expected_criteria = {
            "accessibility_advocate": 4,  # keyboard, screen reader, contrast, semantic
            "power_user": 4,              # efficiency, bulk ops, customization, export/api
            "novice_user": 4,             # onboarding, clarity, safety, guidance
            "mobile_first": 4,            # touch, responsiveness, performance, offline
            "brand_aesthetics": 4,        # visual hierarchy, consistency, aesthetics, typography
            "security_conscious": 4,      # auth, data protection, privacy, input security
            "performance_optimizer": 4    # load time, bundle, resources, runtime
        }

        for persona_id, expected_count in expected_criteria.items():
            persona = loader.load_persona(persona_id)
            actual_count = len(persona.evaluation_rubric)
            assert actual_count == expected_count, \
                f"{persona_id} should have {expected_count} criteria, has {actual_count}"


# ============================================================================
# Utility Functions Tests
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions for persona system."""

    def test_get_default_personas_dir(self):
        """Test getting default personas directory."""
        personas_dir = get_default_personas_dir()
        assert personas_dir.name == "personas"
        assert personas_dir.exists()

    def test_create_personas_directory(self):
        """Test creating personas directory."""
        personas_dir = create_personas_directory()
        assert personas_dir.exists()
        assert personas_dir.is_dir()


# ============================================================================
# Integration Tests
# ============================================================================

class TestPersonaSystemIntegration:
    """Integration tests for the complete persona system."""

    def test_load_validate_all_built_in_personas(self):
        """Test loading and validating all built-in personas."""
        loader = PersonaLoader()
        personas = loader.load_all_personas()

        assert len(personas) == 7

        for persona in personas:
            # Test validation
            is_valid, errors = PersonaValidator.validate_persona(persona)
            assert is_valid, f"{persona.id} invalid: {errors}"

            # Test serialization roundtrip
            persona_dict = persona.to_dict()
            restored = Persona.from_dict(persona_dict)
            assert restored.id == persona.id
            assert restored.name == persona.name

    def test_persona_system_workflow(self):
        """Test complete workflow: create, save, load, validate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PersonaLoader(Path(tmpdir))

            # 1. Create persona
            rubric = {
                "quality": EvaluationCriterion("quality", 0.6, "Quality of code"),
                "speed": EvaluationCriterion("speed", 0.4, "Development speed")
            }
            sample_feedback = SampleFeedback(
                positive="Excellent code quality!",
                negative="Too slow to develop",
                suggestion="Use code generation tools"
            )
            persona = Persona(
                id="developer",
                name="Dev Developer",
                age=28,
                background="Full-stack developer",
                expertise=["React", "Python", "Docker"],
                bias="Prefers modern tools",
                personality="Pragmatic and efficient",
                typical_concerns=["Code quality", "Developer experience"],
                evaluation_rubric=rubric,
                sample_feedback=sample_feedback
            )

            # 2. Validate
            is_valid, errors = PersonaValidator.validate_persona(persona)
            assert is_valid, f"Validation failed: {errors}"

            # 3. Save
            saved_path = loader.save_persona(persona)
            assert saved_path.exists()

            # 4. Clear cache to force fresh load
            loader._cache.clear()

            # 5. Load
            loaded = loader.load_persona("developer")
            assert loaded.id == "developer"
            assert loaded.name == "Dev Developer"
            assert loaded.sample_feedback.positive == "Excellent code quality!"

            # 6. List personas
            persona_ids = loader.list_available_personas()
            assert "developer" in persona_ids
