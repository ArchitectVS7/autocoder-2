#!/usr/bin/env python3
"""
Assumptions CLI Tool
====================

Command-line interface for viewing and managing implementation assumptions.

Usage:
    # Show all assumptions for a feature
    python assumptions_cli.py --project-dir /path/to/project --feature 12

    # Show all active assumptions in the project
    python assumptions_cli.py --project-dir /path/to/project --show-all

    # Review assumptions when a previously skipped feature is implemented
    python assumptions_cli.py --project-dir /path/to/project --review 5

    # Mark an assumption as validated or invalid
    python assumptions_cli.py --project-dir /path/to/project --validate-assumption 3
    python assumptions_cli.py --project-dir /path/to/project --invalidate-assumption 3
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from api.database import create_database, Feature, FeatureAssumption


class AssumptionsCLI:
    """CLI for managing implementation assumptions."""

    def __init__(self, project_dir: Path):
        """Initialize CLI with project directory.

        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = Path(project_dir)
        if not self.project_dir.exists():
            raise ValueError(f"Project directory does not exist: {project_dir}")

        # Create database connection
        _, SessionLocal = create_database(self.project_dir)
        self.session: Session = SessionLocal()

    def __del__(self):
        """Close database session."""
        if hasattr(self, 'session'):
            self.session.close()

    def show_feature_assumptions(self, feature_id: int, verbose: bool = False) -> None:
        """Show all assumptions for a specific feature.

        Args:
            feature_id: ID of the feature
            verbose: Show detailed information
        """
        feature = self.session.query(Feature).filter(Feature.id == feature_id).first()
        if not feature:
            print(f"❌ Feature #{feature_id} not found")
            return

        assumptions = self.session.query(FeatureAssumption).filter(
            FeatureAssumption.feature_id == feature_id
        ).all()

        print(f"\n{'='*60}")
        print(f"Feature #{feature_id}: {feature.name}")
        print(f"{'='*60}\n")

        if not assumptions:
            print("✓ No assumptions documented for this feature")
            return

        print(f"Total assumptions: {len(assumptions)}\n")

        for assumption in assumptions:
            status_icon = self._get_status_icon(assumption.status)
            print(f"{status_icon} Assumption #{assumption.id} [{assumption.status}]")

            if assumption.depends_on_feature_id:
                dep_feature = self.session.query(Feature).filter(
                    Feature.id == assumption.depends_on_feature_id
                ).first()
                if dep_feature:
                    print(f"   Depends on: Feature #{dep_feature.id} - {dep_feature.name}")

            print(f"   Assumption: {assumption.assumption_text}")

            if assumption.code_location:
                print(f"   Location: {assumption.code_location}")

            if assumption.impact_description:
                print(f"   Impact: {assumption.impact_description}")

            if verbose:
                print(f"   Created: {assumption.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if assumption.validated_at:
                    print(f"   Validated: {assumption.validated_at.strftime('%Y-%m-%d %H:%M:%S')}")

            print()

    def show_all_assumptions(self, status_filter: Optional[str] = None) -> None:
        """Show all assumptions in the project.

        Args:
            status_filter: Filter by status (ACTIVE, VALIDATED, INVALID, NEEDS_REVIEW)
        """
        query = self.session.query(FeatureAssumption)
        if status_filter:
            query = query.filter(FeatureAssumption.status == status_filter)

        assumptions = query.all()

        print(f"\n{'='*60}")
        print("All Implementation Assumptions")
        if status_filter:
            print(f"Status: {status_filter}")
        print(f"{'='*60}\n")

        if not assumptions:
            print("✓ No assumptions found")
            return

        # Group by status
        by_status: Dict[str, List[FeatureAssumption]] = {}
        for assumption in assumptions:
            if assumption.status not in by_status:
                by_status[assumption.status] = []
            by_status[assumption.status].append(assumption)

        # Display by status
        status_order = ["ACTIVE", "NEEDS_REVIEW", "INVALID", "VALIDATED"]
        for status in status_order:
            if status not in by_status:
                continue

            count = len(by_status[status])
            status_icon = self._get_status_icon(status)
            print(f"\n{status_icon} {status} ({count})")
            print("-" * 60)

            for assumption in by_status[status]:
                feature = self.session.query(Feature).filter(
                    Feature.id == assumption.feature_id
                ).first()

                print(f"\n  Feature #{feature.id}: {feature.name}")
                print(f"  Assumption: {assumption.assumption_text}")

                if assumption.depends_on_feature_id:
                    dep_feature = self.session.query(Feature).filter(
                        Feature.id == assumption.depends_on_feature_id
                    ).first()
                    if dep_feature:
                        print(f"  Depends on: Feature #{dep_feature.id} - {dep_feature.name}")

                if assumption.code_location:
                    print(f"  Location: {assumption.code_location}")

        print()

    def review_assumptions_for_completed_feature(self, feature_id: int) -> None:
        """Review all assumptions made about a feature that was just completed.

        This should be called when a previously skipped feature is implemented.

        Args:
            feature_id: ID of the feature that was just completed
        """
        feature = self.session.query(Feature).filter(Feature.id == feature_id).first()
        if not feature:
            print(f"❌ Feature #{feature_id} not found")
            return

        # Find all assumptions that depend on this feature
        assumptions = self.session.query(FeatureAssumption).filter(
            FeatureAssumption.depends_on_feature_id == feature_id,
            FeatureAssumption.status == "ACTIVE"
        ).all()

        print(f"\n{'='*60}")
        print(f"✓ Feature #{feature_id} '{feature.name}' marked as passing")
        print(f"{'='*60}\n")

        if not assumptions:
            print("✓ No assumptions to review (no features made assumptions about this one)")
            return

        print(f"⚠️  ASSUMPTION REVIEW REQUIRED\n")
        print(f"{len(assumptions)} features made assumptions about this implementation:\n")

        for assumption in assumptions:
            dependent_feature = self.session.query(Feature).filter(
                Feature.id == assumption.feature_id
            ).first()

            print(f"\nFeature #{dependent_feature.id}: {dependent_feature.name}")
            print(f"  Assumption: \"{assumption.assumption_text}\"")
            if assumption.code_location:
                print(f"  Location: {assumption.code_location}")
            if assumption.impact_description:
                print(f"  Impact if wrong: {assumption.impact_description}")

            # Mark for review
            assumption.status = "NEEDS_REVIEW"

        self.session.commit()

        print(f"\n{'='*60}")
        print(f"✓ Marked {len(assumptions)} assumptions for review")
        print(f"{'='*60}\n")
        print("Next steps:")
        print(f"1. Review the implementation of Feature #{feature_id}")
        print(f"2. Check if the assumptions were correct")
        print(f"3. Use --validate-assumption or --invalidate-assumption to update status")
        print(f"4. If invalid, consider marking dependent features for rework\n")

    def validate_assumption(self, assumption_id: int) -> None:
        """Mark an assumption as validated (correct).

        Args:
            assumption_id: ID of the assumption
        """
        assumption = self.session.query(FeatureAssumption).filter(
            FeatureAssumption.id == assumption_id
        ).first()

        if not assumption:
            print(f"❌ Assumption #{assumption_id} not found")
            return

        assumption.status = "VALIDATED"
        assumption.validated_at = datetime.utcnow()
        self.session.commit()

        feature = self.session.query(Feature).filter(
            Feature.id == assumption.feature_id
        ).first()

        print(f"\n✓ Assumption #{assumption_id} marked as VALIDATED")
        print(f"  Feature: #{feature.id} - {feature.name}")
        print(f"  Assumption: {assumption.assumption_text}")
        print(f"  → No rework needed for this feature\n")

    def invalidate_assumption(self, assumption_id: int) -> None:
        """Mark an assumption as invalid (incorrect).

        Args:
            assumption_id: ID of the assumption
        """
        assumption = self.session.query(FeatureAssumption).filter(
            FeatureAssumption.id == assumption_id
        ).first()

        if not assumption:
            print(f"❌ Assumption #{assumption_id} not found")
            return

        assumption.status = "INVALID"
        assumption.validated_at = datetime.utcnow()
        self.session.commit()

        feature = self.session.query(Feature).filter(
            Feature.id == assumption.feature_id
        ).first()

        print(f"\n⚠️  Assumption #{assumption_id} marked as INVALID")
        print(f"  Feature: #{feature.id} - {feature.name}")
        print(f"  Assumption: {assumption.assumption_text}")
        print(f"  → Feature #{feature.id} may need rework\n")

        # Suggest marking feature for review
        print("Recommended action:")
        print(f"  - Review the implementation in: {assumption.code_location or 'see feature files'}")
        print(f"  - Consider creating a fix feature")
        print(f"  - Impact: {assumption.impact_description or 'Unknown'}\n")

    def _get_status_icon(self, status: str) -> str:
        """Get icon for assumption status.

        Args:
            status: Assumption status

        Returns:
            Status icon
        """
        icons = {
            "ACTIVE": "📝",
            "NEEDS_REVIEW": "⚠️",
            "VALIDATED": "✅",
            "INVALID": "❌",
        }
        return icons.get(status, "❓")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage implementation assumptions for autocoder projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show assumptions for a feature
  python assumptions_cli.py --project-dir my-app --feature 12

  # Show all active assumptions
  python assumptions_cli.py --project-dir my-app --show-all

  # Review assumptions when Feature #5 is implemented
  python assumptions_cli.py --project-dir my-app --review 5

  # Validate/invalidate assumptions
  python assumptions_cli.py --project-dir my-app --validate-assumption 3
  python assumptions_cli.py --project-dir my-app --invalidate-assumption 3
        """
    )

    parser.add_argument(
        "--project-dir",
        type=str,
        required=True,
        help="Path to project directory (can be absolute path or registered name)"
    )

    parser.add_argument(
        "--feature",
        type=int,
        help="Show assumptions for a specific feature ID"
    )

    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all assumptions in the project"
    )

    parser.add_argument(
        "--status",
        type=str,
        choices=["ACTIVE", "NEEDS_REVIEW", "VALIDATED", "INVALID"],
        help="Filter assumptions by status (use with --show-all)"
    )

    parser.add_argument(
        "--review",
        type=int,
        metavar="FEATURE_ID",
        help="Review assumptions for a feature that was just completed"
    )

    parser.add_argument(
        "--validate-assumption",
        type=int,
        metavar="ASSUMPTION_ID",
        help="Mark an assumption as validated (correct)"
    )

    parser.add_argument(
        "--invalidate-assumption",
        type=int,
        metavar="ASSUMPTION_ID",
        help="Mark an assumption as invalid (needs rework)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output with timestamps"
    )

    args = parser.parse_args()

    # Resolve project directory (support registry names)
    project_dir = Path(args.project_dir)
    if not project_dir.is_absolute():
        # Try to resolve from registry
        try:
            from registry import ProjectRegistry
            registry = ProjectRegistry()
            resolved = registry.get_project_path(args.project_dir)
            if resolved:
                project_dir = Path(resolved)
        except ImportError:
            pass

    # Validate at least one action is specified
    if not any([args.feature, args.show_all, args.review,
                args.validate_assumption, args.invalidate_assumption]):
        parser.error("Must specify one of: --feature, --show-all, --review, "
                     "--validate-assumption, --invalidate-assumption")

    try:
        cli = AssumptionsCLI(project_dir)

        if args.feature:
            cli.show_feature_assumptions(args.feature, verbose=args.verbose)
        elif args.show_all:
            cli.show_all_assumptions(status_filter=args.status)
        elif args.review:
            cli.review_assumptions_for_completed_feature(args.review)
        elif args.validate_assumption:
            cli.validate_assumption(args.validate_assumption)
        elif args.invalidate_assumption:
            cli.invalidate_assumption(args.invalidate_assumption)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
