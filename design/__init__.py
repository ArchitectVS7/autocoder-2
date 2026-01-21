"""
Design iteration and persona-based review system.

This module provides multi-persona design validation, iteration workflows,
and human intervention prompts for UX evaluation.
"""

from design.persona_system import Persona, PersonaLoader, PersonaValidator, EvaluationCriterion
from design.iteration import (
    DesignIterationAgent,
    PersonaReviewPanel,
    DesignSynthesisAgent,
    ConvergenceDetector,
    DesignDocument,
)
from design.review import DesignReviewCLI
from design.human_intervention import HumanInterventionHandler

__all__ = [
    "Persona",
    "PersonaLoader",
    "PersonaValidator",
    "EvaluationCriterion",
    "DesignIterationAgent",
    "PersonaReviewPanel",
    "DesignSynthesisAgent",
    "ConvergenceDetector",
    "DesignDocument",
    "DesignReviewCLI",
    "HumanInterventionHandler",
]
