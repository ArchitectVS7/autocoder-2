"""
Blockers CLI
===========

Command-line interface for managing blockers - unblock features,
show active blockers, and manage blocker status.
"""

import argparse
import sys
from pathlib import Path
from sqlalchemy.orm import Session

from api.database import create_database, Feature, FeatureBlocker
from tools.blockers_md_generator import BlockersMdGenerator, print_blockers_summary
from tools.blocker_classifier import BlockerClassifier


def cmd_unblock(project_dir: Path, feature_id: int) -> bool:
    """
    Unblock a specific feature.

    Args:
        project_dir: Path to the project directory
        feature_id: ID of the feature to unblock

    Returns:
        True if successful
    """
    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        feature = db.query(Feature).filter_by(id=feature_id).first()
        if not feature:
            print(f"❌ Feature #{feature_id} not found")
            return False

        if not feature.is_blocked:
            print(f"⚠️  Feature #{feature_id} is not blocked")
            return False

        # Resolve all active blockers for this feature
        blockers = (
            db.query(FeatureBlocker)
            .filter_by(feature_id=feature_id, status="ACTIVE")
            .all()
        )

        for blocker in blockers:
            from datetime import datetime

            blocker.status = "RESOLVED"
            blocker.resolution_action = "MANUAL_UNBLOCK"
            blocker.resolved_at = datetime.utcnow()

        # Update feature status
        feature.is_blocked = False
        feature.blocker_type = None
        feature.blocker_description = None

        # Reset priority to move back to queue
        # Find the current lowest priority non-blocked feature
        lowest_priority = (
            db.query(Feature.priority)
            .filter(Feature.is_blocked == False)
            .filter(Feature.passes == False)
            .order_by(Feature.priority.asc())
            .first()
        )

        if lowest_priority:
            feature.priority = lowest_priority[0]

        db.commit()

        # Update BLOCKERS.md
        generator = BlockersMdGenerator(db)
        generator.update(project_dir)

        print(f"✓ Feature #{feature_id} '{feature.name}' unblocked")
        print("✓ Removed from BLOCKERS.md")
        print("→ Agent will retry this feature in next session\n")

        return True

    finally:
        db.close()


def cmd_unblock_all(project_dir: Path) -> bool:
    """
    Unblock all blocked features.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if successful
    """
    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        # Get all blocked features
        blocked_features = db.query(Feature).filter_by(is_blocked=True).all()

        if not blocked_features:
            print("✨ No blocked features found\n")
            return True

        # Unblock each feature
        for feature in blocked_features:
            # Resolve all active blockers
            blockers = (
                db.query(FeatureBlocker)
                .filter_by(feature_id=feature.id, status="ACTIVE")
                .all()
            )

            for blocker in blockers:
                from datetime import datetime

                blocker.status = "RESOLVED"
                blocker.resolution_action = "MANUAL_UNBLOCK"
                blocker.resolved_at = datetime.utcnow()

            # Update feature status
            feature.is_blocked = False
            feature.blocker_type = None
            feature.blocker_description = None

        db.commit()

        # Update BLOCKERS.md
        generator = BlockersMdGenerator(db)
        generator.update(project_dir)

        print(f"✓ Unblocked {len(blocked_features)} features:")
        for feature in blocked_features:
            print(f"  • #{feature.id} {feature.name}")

        print("\n→ Agent will retry all unblocked features in next session\n")

        return True

    finally:
        db.close()


def cmd_show_blockers(project_dir: Path, verbose: bool = False) -> bool:
    """
    Show all active blockers.

    Args:
        project_dir: Path to the project directory
        verbose: Show detailed information

    Returns:
        True if successful
    """
    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        blockers = (
            db.query(FeatureBlocker)
            .filter_by(status="ACTIVE")
            .all()
        )

        if not blockers:
            print("\n✨ No active blockers! All features are ready to implement.\n")
            return True

        print(f"\nActive Blockers ({len(blockers)}):\n")

        for blocker in blockers:
            feature = db.query(Feature).filter_by(id=blocker.feature_id).first()
            if not feature:
                continue

            # Format blocker type
            blocker_type_display = blocker.blocker_type.replace("_", " ").title()

            print(f"#{feature.id}  {feature.name} [{blocker_type_display}]")

            if verbose:
                print(f"    Description: {blocker.blocker_description}")
                if blocker.required_values:
                    print(f"    Required: {', '.join(blocker.required_values)}")
                if blocker.required_action:
                    print(f"    Action: {blocker.required_action}")

                print(f"    Unblock: python start.py --unblock {feature.id}")
            else:
                desc = blocker.blocker_description
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                print(f"    {desc}")

            print()

        if not verbose:
            print("💡 Run with --verbose for more details\n")

        return True

    finally:
        db.close()


def cmd_show_dependencies(project_dir: Path, feature_id: int) -> bool:
    """
    Show dependencies for a feature.

    Args:
        project_dir: Path to the project directory
        feature_id: ID of the feature

    Returns:
        True if successful
    """
    from dependency_detector import DependencyDetector

    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        feature = db.query(Feature).filter_by(id=feature_id).first()
        if not feature:
            print(f"❌ Feature #{feature_id} not found")
            return False

        detector = DependencyDetector(db)

        # Get dependencies (features this one depends on)
        dependencies = detector.get_dependencies_for_feature(feature_id)

        # Get dependents (features that depend on this one)
        dependents = detector.get_dependent_features(feature_id)

        print(f"\nFeature #{feature_id}: {feature.name}")
        print("=" * 60)

        if dependencies:
            print(f"\n📦 Dependencies ({len(dependencies)}) - This feature depends on:")
            for dep in dependencies:
                dep_feature = db.query(Feature).filter_by(id=dep.depends_on_feature_id).first()
                if dep_feature:
                    confidence_icon = (
                        "🔴"
                        if dep.confidence >= 0.8
                        else "🟡"
                        if dep.confidence >= 0.6
                        else "⚪"
                    )
                    status = "✓" if dep_feature.passes else "⏳"
                    print(
                        f"  {confidence_icon} #{dep_feature.id} {dep_feature.name} "
                        f"({dep.confidence:.0%}) {status}"
                    )
                    print(f"      Detected via: {dep.detected_method}")
        else:
            print("\n📦 No dependencies found - This feature can be implemented independently")

        if dependents:
            print(f"\n⬆️  Dependents ({len(dependents)}) - These features depend on this one:")
            for dep in dependents:
                dep_feature = db.query(Feature).filter_by(id=dep.feature_id).first()
                if dep_feature:
                    confidence_icon = (
                        "🔴"
                        if dep.confidence >= 0.8
                        else "🟡"
                        if dep.confidence >= 0.6
                        else "⚪"
                    )
                    status = "✓" if dep_feature.passes else "⏳"
                    print(
                        f"  {confidence_icon} #{dep_feature.id} {dep_feature.name} "
                        f"({dep.confidence:.0%}) {status}"
                    )
        else:
            print("\n⬆️  No dependent features - Safe to defer or skip")

        print()
        return True

    finally:
        db.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Manage feature blockers")

    parser.add_argument("--project-dir", type=str, help="Project directory path")
    parser.add_argument(
        "--unblock", type=int, metavar="FEATURE_ID", help="Unblock a specific feature"
    )
    parser.add_argument("--unblock-all", action="store_true", help="Unblock all features")
    parser.add_argument("--show-blockers", action="store_true", help="Show active blockers")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information")
    parser.add_argument(
        "--dependencies",
        type=int,
        metavar="FEATURE_ID",
        help="Show dependencies for a feature",
    )

    args = parser.parse_args()

    # Get project directory
    if args.project_dir:
        project_dir = Path(args.project_dir).resolve()
    else:
        # Try to use current directory
        project_dir = Path.cwd()

        # Check if features.db exists
        if not (project_dir / "features.db").exists():
            print("❌ No project specified and no features.db found in current directory")
            print("\nUsage:")
            print("  python blockers_cli.py --project-dir /path/to/project --show-blockers")
            print("  python blockers_cli.py --project-dir /path/to/project --unblock 5")
            print("  python blockers_cli.py --project-dir /path/to/project --unblock-all")
            return 1

    # Execute command
    if args.unblock:
        success = cmd_unblock(project_dir, args.unblock)
        return 0 if success else 1

    elif args.unblock_all:
        success = cmd_unblock_all(project_dir)
        return 0 if success else 1

    elif args.show_blockers:
        success = cmd_show_blockers(project_dir, args.verbose)
        return 0 if success else 1

    elif args.dependencies:
        success = cmd_show_dependencies(project_dir, args.dependencies)
        return 0 if success else 1

    else:
        print("❌ No command specified")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
