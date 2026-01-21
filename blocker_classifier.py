"""
Blocker Classification System
=============================

Classifies reasons for skipping features into categorized blocker types
and determines which require human intervention.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session

from api.database import Feature, FeatureBlocker


class BlockerType(Enum):
    """Types of blockers that can prevent feature implementation."""

    ENV_CONFIG = "environment_config"
    EXTERNAL_SERVICE = "external_service"
    TECH_PREREQUISITE = "technical_prerequisite"
    UNCLEAR_REQUIREMENTS = "unclear_requirements"
    LEGITIMATE_DEFERRAL = "legitimate_deferral"


class BlockerClassifier:
    """Classifies blocker types and manages blocking workflow."""

    # Keywords that indicate different blocker types
    BLOCKER_INDICATORS = {
        BlockerType.ENV_CONFIG: [
            "environment variable",
            "env var",
            "missing env",
            "secret",
            "credentials",
            "config",
            "missing .env",
            "configuration",
            "CLIENT_ID",
            "API_KEY",
            "SECRET",
        ],
        BlockerType.EXTERNAL_SERVICE: [
            "stripe",
            "sendgrid",
            "twilio",
            "aws",
            "google cloud",
            "third-party",
            "external service",
            "need account",
            "sign up for",
            "service not configured",
            "set up account",
            "api key",  # When combined with service names, indicates external service setup
        ],
        BlockerType.TECH_PREREQUISITE: [
            "depends on",
            "requires",
            "needs feature",
            "api endpoint",
            "database",
            "not built yet",
            "prerequisite",
            "blocked by",
        ],
        BlockerType.UNCLEAR_REQUIREMENTS: [
            "unclear",
            "ambiguous",
            "not sure",
            "what should",
            "need clarification",
            "specification",
            "requirements",
            "don't know",
        ],
        BlockerType.LEGITIMATE_DEFERRAL: [
            "polish",
            "nice to have",
            "low priority",
            "can wait",
            "later",
            "defer",
            "not critical",
            "optional",
        ],
    }

    # Which blocker types require human intervention
    REQUIRES_HUMAN_INTERVENTION = {
        BlockerType.ENV_CONFIG,
        BlockerType.EXTERNAL_SERVICE,
        BlockerType.UNCLEAR_REQUIREMENTS,
    }

    def __init__(self, db_session: Session):
        """
        Initialize the blocker classifier.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    def classify_blocker(
        self, feature: Feature, skip_reason: str, agent_classification: Optional[str] = None
    ) -> BlockerType:
        """
        Classify a blocker type based on skip reason.

        Args:
            feature: The feature being skipped
            skip_reason: Reason provided for skipping
            agent_classification: Optional pre-classification from agent

        Returns:
            BlockerType enum value
        """
        # If agent already classified, validate it
        if agent_classification:
            try:
                return BlockerType(agent_classification)
            except ValueError:
                pass  # Fall through to automatic classification

        # Automatic classification based on keywords
        skip_reason_lower = skip_reason.lower()
        scores = {}

        for blocker_type, keywords in self.BLOCKER_INDICATORS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in skip_reason_lower)
            scores[blocker_type] = score

        # Return the highest scoring type
        if max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]

        # Default to unclear requirements if no match
        return BlockerType.UNCLEAR_REQUIREMENTS

    def classify_blocker_text(self, skip_reason: str) -> BlockerType:
        """
        Classify a blocker type based on skip reason text only.

        This is a convenience method for testing and simple classification
        without requiring a full Feature object.

        Args:
            skip_reason: Reason text for skipping

        Returns:
            BlockerType enum value
        """
        # Use the main classification logic with just the text
        skip_reason_lower = skip_reason.lower()
        scores = {}

        for blocker_type, keywords in self.BLOCKER_INDICATORS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in skip_reason_lower)
            scores[blocker_type] = score

        # Return the highest scoring type
        if max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]

        # Default to unclear requirements if no match
        return BlockerType.UNCLEAR_REQUIREMENTS

    def requires_human_intervention(self, blocker_type: BlockerType) -> bool:
        """
        Check if a blocker type requires human input.

        Args:
            blocker_type: The type of blocker

        Returns:
            True if human intervention is required
        """
        return blocker_type in self.REQUIRES_HUMAN_INTERVENTION

    def create_blocker(
        self,
        feature_id: int,
        blocker_type: BlockerType,
        description: str,
        required_action: Optional[str] = None,
        required_values: Optional[List[str]] = None,
    ) -> FeatureBlocker:
        """
        Create a blocker record in the database.

        Args:
            feature_id: ID of the blocked feature
            blocker_type: Type of blocker
            description: Description of the blocker
            required_action: What the user needs to do
            required_values: List of required values (e.g., env var names)

        Returns:
            Created FeatureBlocker object
        """
        blocker = FeatureBlocker(
            feature_id=feature_id,
            blocker_type=blocker_type.value,
            blocker_description=description,
            required_action=required_action,
            required_values=required_values,
            status="ACTIVE",
        )

        self.db.add(blocker)

        # Update feature status
        feature = self.db.query(Feature).filter_by(id=feature_id).first()
        if feature:
            feature.is_blocked = True
            feature.blocker_type = blocker_type.value
            feature.blocker_description = description
            feature.was_skipped = True
            feature.skip_count += 1

        self.db.commit()
        return blocker

    def extract_required_values(
        self, description: str, blocker_type: Optional[BlockerType] = None
    ) -> Optional[List[str]]:
        """
        Extract required values from blocker description.

        For ENV_CONFIG blockers, tries to extract environment variable names.
        If blocker_type is not provided, will auto-detect from description.

        Args:
            description: Blocker description
            blocker_type: Optional type of blocker (auto-detected if None)

        Returns:
            List of required values or None
        """
        # Auto-detect blocker type if not provided
        if blocker_type is None:
            blocker_type = self.classify_blocker_text(description)

        if blocker_type != BlockerType.ENV_CONFIG:
            return None

        import re

        # Pattern: UPPERCASE_WITH_UNDERSCORES or quoted strings
        patterns = [
            r"\b([A-Z][A-Z0-9_]{2,})\b",  # UPPERCASE_VARS
            r"`([^`]+)`",  # `backtick quoted`
            r'"([^"]+)"',  # "double quoted"
        ]

        values = set()
        for pattern in patterns:
            matches = re.findall(pattern, description)
            values.update(matches)

        return list(values) if values else None

    def get_blocker_prompt(self, blocker_type: BlockerType, blocker: FeatureBlocker) -> str:
        """
        Generate a user-facing prompt for a blocker.

        Args:
            blocker_type: Type of blocker
            blocker: Blocker object

        Returns:
            Formatted prompt string
        """
        feature = self.db.query(Feature).filter_by(id=blocker.feature_id).first()
        if not feature:
            return "Error: Feature not found"

        prompt = []
        prompt.append("\n🛑 HUMAN INPUT REQUIRED")
        prompt.append("━" * 50)
        prompt.append(f"\nFeature #{feature.id}: \"{feature.name}\"")
        prompt.append(f"Blocker Type: {self._format_blocker_type(blocker_type)}")
        prompt.append(f"\n{blocker.blocker_description}")

        if blocker.required_values:
            prompt.append("\nRequired information:")
            for value in blocker.required_values:
                prompt.append(f"  • {value}")

        if blocker.required_action:
            prompt.append(f"\n{blocker.required_action}")

        prompt.append("\n🎯 ACTIONS")
        prompt.append("━" * 50)
        prompt.append("  [1] Provide values now (continue immediately)")
        prompt.append("  [2] Defer (I'll add to .env later)")
        prompt.append("  [3] Mock (use fake values for now)")
        prompt.append("\nSelect action (1-3): ")

        return "\n".join(prompt)

    def _format_blocker_type(self, blocker_type: BlockerType) -> str:
        """
        Format blocker type for display.

        Args:
            blocker_type: Blocker type enum

        Returns:
            Formatted string
        """
        type_names = {
            BlockerType.ENV_CONFIG: "Environment Configuration",
            BlockerType.EXTERNAL_SERVICE: "External Service Setup",
            BlockerType.TECH_PREREQUISITE: "Technical Prerequisite",
            BlockerType.UNCLEAR_REQUIREMENTS: "Requirements Clarification",
            BlockerType.LEGITIMATE_DEFERRAL: "Deferred Feature",
        }
        return type_names.get(blocker_type, blocker_type.value)

    def resolve_blocker(
        self, blocker_id: int, resolution_action: str, values: Optional[Dict] = None
    ) -> bool:
        """
        Resolve a blocker.

        Args:
            blocker_id: ID of the blocker to resolve
            resolution_action: How it was resolved (PROVIDED, DEFERRED, MOCKED)
            values: Optional values provided

        Returns:
            True if successful
        """
        from datetime import datetime

        blocker = self.db.query(FeatureBlocker).filter_by(id=blocker_id).first()
        if not blocker:
            return False

        blocker.status = "RESOLVED"
        blocker.resolution_action = resolution_action
        blocker.resolved_at = datetime.utcnow()

        # Update feature status
        feature = self.db.query(Feature).filter_by(id=blocker.feature_id).first()
        if feature:
            # Check if there are other active blockers
            other_blockers = (
                self.db.query(FeatureBlocker)
                .filter_by(feature_id=feature.id, status="ACTIVE")
                .filter(FeatureBlocker.id != blocker_id)
                .count()
            )

            if other_blockers == 0:
                feature.is_blocked = False
                feature.blocker_type = None
                feature.blocker_description = None

                if resolution_action == "MOCKED":
                    feature.passing_with_mocks = True

        self.db.commit()
        return True

    def get_active_blockers(self) -> List[FeatureBlocker]:
        """
        Get all active blockers.

        Returns:
            List of active FeatureBlocker objects
        """
        return self.db.query(FeatureBlocker).filter_by(status="ACTIVE").all()

    def get_blockers_by_type(self, blocker_type: BlockerType) -> List[FeatureBlocker]:
        """
        Get all active blockers of a specific type.

        Args:
            blocker_type: Type of blockers to retrieve

        Returns:
            List of FeatureBlocker objects
        """
        return (
            self.db.query(FeatureBlocker)
            .filter_by(status="ACTIVE", blocker_type=blocker_type.value)
            .all()
        )


def classify_and_create_blocker(
    project_dir: Path,
    feature_id: int,
    skip_reason: str,
    agent_classification: Optional[str] = None,
) -> Tuple[BlockerType, bool]:
    """
    Classify a blocker and create a record for it.

    Args:
        project_dir: Path to the project directory
        feature_id: ID of the feature being blocked
        skip_reason: Reason for skipping
        agent_classification: Optional pre-classification from agent

    Returns:
        Tuple of (BlockerType, requires_human_intervention)
    """
    from api.database import create_database

    # Initialize database
    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        classifier = BlockerClassifier(db)
        feature = db.query(Feature).filter_by(id=feature_id).first()

        if not feature:
            return BlockerType.UNCLEAR_REQUIREMENTS, False

        # Classify the blocker
        blocker_type = classifier.classify_blocker(feature, skip_reason, agent_classification)

        # Extract required values if applicable
        required_values = classifier.extract_required_values(skip_reason, blocker_type)

        # Create blocker record
        blocker = classifier.create_blocker(
            feature_id=feature_id,
            blocker_type=blocker_type,
            description=skip_reason,
            required_values=required_values,
        )

        # Check if human intervention required
        requires_human = classifier.requires_human_intervention(blocker_type)

        return blocker_type, requires_human

    finally:
        db.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) > 3:
        project_path = Path(sys.argv[1])
        feature_id = int(sys.argv[2])
        skip_reason = sys.argv[3]

        blocker_type, requires_human = classify_and_create_blocker(
            project_path, feature_id, skip_reason
        )

        print(f"\n✓ Blocker classified as: {blocker_type.value}")
        print(f"  Requires human intervention: {'Yes' if requires_human else 'No'}")
    else:
        print("Usage: python blocker_classifier.py <project_dir> <feature_id> <skip_reason>")
