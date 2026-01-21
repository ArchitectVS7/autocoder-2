"""
BLOCKERS.md Auto-Generation
===========================

Automatically generates and updates a BLOCKERS.md file with all active
blockers requiring human attention.
"""

from datetime import datetime
from typing import List, Dict
from pathlib import Path
from sqlalchemy.orm import Session

from api.database import Feature, FeatureBlocker
from blocker_classifier import BlockerType


class BlockersMdGenerator:
    """Generates BLOCKERS.md checklist file."""

    def __init__(self, db_session: Session):
        """
        Initialize the BLOCKERS.md generator.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    def generate(self, blockers: List[FeatureBlocker]) -> str:
        """
        Generate BLOCKERS.md content.

        Args:
            blockers: List of active blockers

        Returns:
            Markdown content string
        """
        if not blockers:
            return self._generate_empty_blockers_file()

        # Group blockers by type
        grouped = self._group_by_type(blockers)

        # Build the document
        lines = []
        lines.append("# Blockers Requiring Human Input")
        lines.append("")
        lines.append(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total blockers: {len(blockers)}")
        lines.append("")

        # Generate sections for each blocker type
        for blocker_type, items in grouped.items():
            section = self._render_section(blocker_type, items)
            if section:
                lines.append(section)
                lines.append("")

        # Add quick commands section
        lines.append(self._render_commands_section())

        return "\n".join(lines)

    def _generate_empty_blockers_file(self) -> str:
        """
        Generate BLOCKERS.md for when there are no blockers.

        Returns:
            Markdown content string
        """
        lines = []
        lines.append("# Blockers Requiring Human Input")
        lines.append("")
        lines.append(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("✨ **No active blockers!** All features are ready to implement.")
        lines.append("")
        return "\n".join(lines)

    def _group_by_type(self, blockers: List[FeatureBlocker]) -> Dict[str, List[FeatureBlocker]]:
        """
        Group blockers by type.

        Args:
            blockers: List of blockers

        Returns:
            Dictionary mapping blocker type to list of blockers
        """
        grouped = {}

        for blocker in blockers:
            blocker_type = blocker.blocker_type
            if blocker_type not in grouped:
                grouped[blocker_type] = []
            grouped[blocker_type].append(blocker)

        return grouped

    def _render_section(self, blocker_type: str, blockers: List[FeatureBlocker]) -> str:
        """
        Render a section for a specific blocker type.

        Args:
            blocker_type: Type of blockers in this section
            blockers: List of blockers of this type

        Returns:
            Markdown section string
        """
        # Get section title
        section_titles = {
            BlockerType.ENV_CONFIG.value: "## Environment Variables Needed",
            BlockerType.EXTERNAL_SERVICE.value: "## External Services to Configure",
            BlockerType.UNCLEAR_REQUIREMENTS.value: "## Requirements Clarifications Needed",
            BlockerType.TECH_PREREQUISITE.value: "## Technical Prerequisites",
        }

        title = section_titles.get(blocker_type, f"## {blocker_type.replace('_', ' ').title()}")

        lines = [title, ""]

        for blocker in blockers:
            feature = self.db.query(Feature).filter_by(id=blocker.feature_id).first()
            if not feature:
                continue

            # Feature item
            lines.append(f"- [ ] **Feature #{feature.id}: {feature.name}**")

            # Description
            lines.append(f"  - {blocker.blocker_description}")

            # Required values (for env config)
            if blocker.required_values:
                for value in blocker.required_values:
                    # Try to provide helpful hints about where to get the value
                    hint = self._get_value_hint(value)
                    if hint:
                        lines.append(f"  - `{value}` - {hint}")
                    else:
                        lines.append(f"  - `{value}`")

            # Required action
            if blocker.required_action:
                lines.append(f"  - {blocker.required_action}")

            # Unblock command
            lines.append(f"  - **To unblock:** `python start.py --unblock {feature.id}`")
            lines.append("")

        return "\n".join(lines)

    def _get_value_hint(self, value_name: str) -> str:
        """
        Get a helpful hint about where to obtain a value.

        Args:
            value_name: Name of the environment variable

        Returns:
            Hint string or empty string
        """
        value_lower = value_name.lower()

        hints = {
            "stripe": "Get from Stripe Dashboard > Developers > API Keys",
            "sendgrid": "Get from SendGrid Dashboard > Settings > API Keys",
            "twilio": "Get from Twilio Console > Account Settings",
            "google": "Get from Google Cloud Console",
            "oauth_client_id": "Get from OAuth provider's developer console",
            "oauth_client_secret": "Get from OAuth provider's developer console",
            "api_key": "Get from service provider's API settings",
            "secret": "Generate a secure random string",
            "database_url": "Format: postgresql://user:pass@localhost/dbname",
            "jwt_secret": "Generate a secure random string (e.g., openssl rand -hex 32)",
        }

        for keyword, hint in hints.items():
            if keyword in value_lower:
                return hint

        return ""

    def _render_commands_section(self) -> str:
        """
        Render the quick commands section.

        Returns:
            Markdown section string
        """
        lines = []
        lines.append("---")
        lines.append("")
        lines.append("## Quick Commands")
        lines.append("")
        lines.append("```bash")
        lines.append("# Unblock specific feature")
        lines.append("python start.py --unblock <feature_id>")
        lines.append("")
        lines.append("# Unblock all (agent will retry all blocked features)")
        lines.append("python start.py --unblock-all")
        lines.append("")
        lines.append("# View blocker details")
        lines.append("python start.py --show-blockers")
        lines.append("```")
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        lines.append("- After providing values, the agent will automatically retry blocked features in the next session")
        lines.append("- Environment variables should be added to the `.env` file in the project root")
        lines.append("- For sensitive values (API keys, secrets), never commit them to version control")
        lines.append("")

        return "\n".join(lines)

    def update(self, project_dir: Path) -> bool:
        """
        Update BLOCKERS.md file for a project.

        Args:
            project_dir: Path to the project directory

        Returns:
            True if successful
        """
        try:
            # Get all active blockers
            blockers = (
                self.db.query(FeatureBlocker)
                .filter_by(status="ACTIVE")
                .all()
            )

            # Generate content
            content = self.generate(blockers)

            # Write to file
            blockers_file = project_dir / "BLOCKERS.md"
            blockers_file.write_text(content, encoding="utf-8")

            return True

        except Exception as e:
            print(f"❌ Error updating BLOCKERS.md: {e}")
            return False

    def get_summary(self) -> Dict:
        """
        Get a summary of active blockers.

        Returns:
            Dictionary with blocker statistics
        """
        blockers = (
            self.db.query(FeatureBlocker)
            .filter_by(status="ACTIVE")
            .all()
        )

        grouped = self._group_by_type(blockers)

        return {
            "total": len(blockers),
            "by_type": {k: len(v) for k, v in grouped.items()},
            "features_blocked": len(set(b.feature_id for b in blockers)),
        }


def update_blockers_md(project_dir: Path) -> bool:
    """
    Update BLOCKERS.md file for a project.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if successful
    """
    from api.database import create_database

    # Initialize database
    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        generator = BlockersMdGenerator(db)
        return generator.update(project_dir)
    finally:
        db.close()


def print_blockers_summary(project_dir: Path) -> None:
    """
    Print a summary of active blockers.

    Args:
        project_dir: Path to the project directory
    """
    from api.database import create_database

    # Initialize database
    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        generator = BlockersMdGenerator(db)
        summary = generator.get_summary()

        if summary["total"] == 0:
            print("\n✨ No active blockers! All features are ready to implement.\n")
        else:
            print(f"\nActive Blockers ({summary['total']}):")
            print("━" * 50)

            for blocker_type, count in summary["by_type"].items():
                type_display = blocker_type.replace("_", " ").title()
                print(f"  {type_display}: {count}")

            print(f"\nFeatures blocked: {summary['features_blocked']}")
            print(f"\n💡 Run 'python start.py --show-blockers' for details\n")

    finally:
        db.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])

        if len(sys.argv) > 2 and sys.argv[2] == "--summary":
            print_blockers_summary(project_path)
        else:
            success = update_blockers_md(project_path)
            if success:
                print(f"\n✓ BLOCKERS.md updated successfully")
                print(f"  Location: {project_path / 'BLOCKERS.md'}")
            else:
                print("\n❌ Failed to update BLOCKERS.md")
    else:
        print("Usage: python blockers_md_generator.py <project_dir> [--summary]")
