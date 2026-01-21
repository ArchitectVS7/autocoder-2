"""
Human Intervention Workflow
===========================

Handles blockers that require human input by pausing agent execution,
prompting the user, and managing the resolution workflow.
"""

import os
import getpass
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session

from api.database import Feature, FeatureBlocker
from blocker_classifier import BlockerClassifier, BlockerType
from skip_analyzer import SkipImpactAnalyzer


class HumanInterventionHandler:
    """Manages human intervention workflow for blockers."""

    def __init__(self, db_session: Session, project_dir: Path):
        """
        Initialize the human intervention handler.

        Args:
            db_session: SQLAlchemy database session
            project_dir: Path to the project directory
        """
        self.db = db_session
        self.project_dir = project_dir
        self.classifier = BlockerClassifier(db_session)
        self.skip_analyzer = SkipImpactAnalyzer(db_session)

    def handle_blocker(
        self, feature: Feature, blocker: FeatureBlocker
    ) -> Tuple[str, Optional[Dict]]:
        """
        Handle a blocker requiring human input.

        Args:
            feature: The feature that is blocked
            blocker: The blocker object

        Returns:
            Tuple of (action, values_dict) where action is:
                - RESUME_IMMEDIATELY: User provided values, continue now
                - SKIP_AND_DEFER: User chose to defer, skip for now
                - IMPLEMENT_WITH_MOCKS: Implement with placeholder values
                - CANCEL_SKIP: User decided to manually handle it
        """
        blocker_type = BlockerType(blocker.blocker_type)

        # Display blocker information
        prompt = self.classifier.get_blocker_prompt(blocker_type, blocker)
        print(prompt, end="")

        # Get user choice
        choice = self._prompt_user_action()

        if choice == 1:  # Provide values now
            values = self._collect_values(blocker)
            if values:
                self._write_to_env(values)
                self.classifier.resolve_blocker(blocker.id, "PROVIDED", values)
                print("\n✓ Values provided and saved to .env")
                print("→ Agent will resume immediately\n")
                return "RESUME_IMMEDIATELY", values
            else:
                print("\n⚠️  No values provided, deferring instead")
                return self.handle_blocker(feature, blocker)  # Retry

        elif choice == 2:  # Defer
            self._add_to_blockers_md(feature, blocker)
            self.classifier.resolve_blocker(blocker.id, "DEFERRED")
            print("\n✓ Added to BLOCKERS.md")
            print("→ Agent will skip this feature and continue with other work\n")
            return "SKIP_AND_DEFER", None

        elif choice == 3:  # Mock
            self._setup_mock_implementation(feature, blocker)
            self.classifier.resolve_blocker(blocker.id, "MOCKED")
            print("\n✓ Feature will be implemented with mocks/placeholders")
            print("→ Agent will continue with mock implementation\n")
            return "IMPLEMENT_WITH_MOCKS", None

        else:
            return "CANCEL_SKIP", None

    def _prompt_user_action(self) -> int:
        """
        Prompt user to select an action.

        Returns:
            Selected action number (1-3)
        """
        while True:
            try:
                choice_str = input().strip()
                choice = int(choice_str)
                if 1 <= choice <= 3:
                    return choice
                else:
                    print("Invalid choice. Please enter 1, 2, or 3: ", end="")
            except (ValueError, EOFError):
                print("Invalid input. Please enter 1, 2, or 3: ", end="")

    def _collect_values(self, blocker: FeatureBlocker) -> Optional[Dict[str, str]]:
        """
        Collect required values from user.

        Args:
            blocker: Blocker object

        Returns:
            Dictionary of collected values or None if cancelled
        """
        if not blocker.required_values:
            return None

        print("\n📝 Please provide the following values:")
        print("   (Press Ctrl+C to cancel)\n")

        values = {}

        try:
            for value_name in blocker.required_values:
                # Check if it looks like a secret (API key, secret, password, token)
                is_secret = any(
                    keyword in value_name.lower()
                    for keyword in ["secret", "key", "password", "token", "credential"]
                )

                if is_secret:
                    # Use getpass for secret values (masked input)
                    value = getpass.getpass(f"  {value_name}: ")
                else:
                    # Normal input for non-secrets
                    value = input(f"  {value_name}: ")

                if value.strip():
                    values[value_name] = value.strip()
                else:
                    print(f"  ⚠️  Skipping empty value for {value_name}")

        except KeyboardInterrupt:
            print("\n\n⚠️  Cancelled. No values saved.")
            return None

        return values if values else None

    def _write_to_env(self, values: Dict[str, str]) -> bool:
        """
        Write values to .env file.

        Args:
            values: Dictionary of environment variables

        Returns:
            True if successful
        """
        env_path = self.project_dir / ".env"

        try:
            # Read existing .env if it exists
            existing_lines = []
            existing_keys = set()

            if env_path.exists():
                with open(env_path, "r") as f:
                    for line in f:
                        existing_lines.append(line)
                        # Extract key from line (handle comments and empty lines)
                        if "=" in line and not line.strip().startswith("#"):
                            key = line.split("=")[0].strip()
                            existing_keys.add(key)

            # Add new values
            with open(env_path, "a") as f:
                # Add separator comment if file has existing content
                if existing_lines:
                    f.write("\n# Added by autocoder skip management\n")

                for key, value in values.items():
                    if key not in existing_keys:
                        f.write(f"{key}={value}\n")
                    else:
                        print(f"  ⚠️  {key} already exists in .env, skipping")

            return True

        except Exception as e:
            print(f"\n❌ Error writing to .env: {e}")
            return False

    def _add_to_blockers_md(self, feature: Feature, blocker: FeatureBlocker) -> bool:
        """
        Add blocker to BLOCKERS.md file.

        Args:
            feature: Blocked feature
            blocker: Blocker object

        Returns:
            True if successful
        """
        from blockers_md_generator import BlockersMdGenerator

        generator = BlockersMdGenerator(self.db)
        generator.update(self.project_dir)
        return True

    def _setup_mock_implementation(self, feature: Feature, blocker: FeatureBlocker) -> bool:
        """
        Mark feature for mock implementation.

        Args:
            feature: Feature to implement with mocks
            blocker: Blocker object

        Returns:
            True if successful
        """
        from api.database import FeatureAssumption

        # Create assumption record
        assumption = FeatureAssumption(
            feature_id=feature.id,
            assumption_text=(
                f"Feature will be implemented with mock/placeholder values "
                f"until blocker is resolved: {blocker.blocker_description}"
            ),
            status="ACTIVE",
        )
        self.db.add(assumption)

        # Mark feature
        feature.passing_with_mocks = True

        self.db.commit()
        return True

    def check_for_blockers(self, feature_id: int) -> Optional[FeatureBlocker]:
        """
        Check if a feature has active blockers requiring intervention.

        Args:
            feature_id: ID of the feature to check

        Returns:
            Active blocker requiring intervention, or None
        """
        blockers = (
            self.db.query(FeatureBlocker)
            .filter_by(feature_id=feature_id, status="ACTIVE")
            .all()
        )

        # Return first blocker that requires human intervention
        for blocker in blockers:
            blocker_type = BlockerType(blocker.blocker_type)
            if self.classifier.requires_human_intervention(blocker_type):
                return blocker

        return None

    def handle_skip_with_intervention(
        self, feature_id: int, skip_reason: str
    ) -> Tuple[bool, str]:
        """
        Handle feature skip with potential human intervention.

        Args:
            feature_id: ID of feature being skipped
            skip_reason: Reason for skipping

        Returns:
            Tuple of (should_pause, action)
        """
        feature = self.db.query(Feature).filter_by(id=feature_id).first()
        if not feature:
            return False, "SKIP"

        # Classify the blocker
        blocker_type = self.classifier.classify_blocker(feature, skip_reason)

        # Create blocker record
        required_values = self.classifier.extract_required_values(skip_reason, blocker_type)
        blocker = self.classifier.create_blocker(
            feature_id=feature_id,
            blocker_type=blocker_type,
            description=skip_reason,
            required_values=required_values,
        )

        # Check if human intervention is required
        if self.classifier.requires_human_intervention(blocker_type):
            # Show skip impact analysis first
            print(self.skip_analyzer.generate_skip_report(feature_id))
            print()  # Extra line for spacing

            # Handle the blocker
            action, values = self.handle_blocker(feature, blocker)

            if action == "RESUME_IMMEDIATELY":
                return False, "RETRY"  # Don't pause, retry the feature
            elif action == "IMPLEMENT_WITH_MOCKS":
                return False, "MOCK"  # Don't pause, implement with mocks
            else:
                return False, "SKIP"  # Skip and continue

        else:
            # No human intervention needed, just skip
            print(f"\n✓ Feature #{feature_id} skipped: {skip_reason}")
            return False, "SKIP"


def handle_feature_skip(
    project_dir: Path, feature_id: int, skip_reason: str
) -> Tuple[bool, str]:
    """
    Handle a feature skip with potential human intervention.

    Args:
        project_dir: Path to the project directory
        feature_id: ID of the feature being skipped
        skip_reason: Reason for skipping

    Returns:
        Tuple of (should_pause, action)
    """
    from api.database import create_database

    # Initialize database
    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        handler = HumanInterventionHandler(db, project_dir)
        return handler.handle_skip_with_intervention(feature_id, skip_reason)
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) > 3:
        project_path = Path(sys.argv[1])
        feature_id = int(sys.argv[2])
        skip_reason = " ".join(sys.argv[3:])

        should_pause, action = handle_feature_skip(project_path, feature_id, skip_reason)

        print(f"\n✓ Action: {action}")
        print(f"  Should pause: {should_pause}")
    else:
        print("Usage: python human_intervention.py <project_dir> <feature_id> <skip_reason>")
