"""
Checkpoint Auto-Fix Feature Creation
=====================================

Automatically creates fix features when critical issues are detected
by checkpoint agents.
"""

from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from checkpoint_orchestrator import AggregatedCheckpointResult, CheckpointIssue, IssueSeverity
from api.database import Feature


class CheckpointAutoFix:
    """Automatically creates fix features for critical checkpoint issues."""

    def __init__(self, db_session: Session, project_dir: Path):
        """
        Initialize the auto-fix system.

        Args:
            db_session: SQLAlchemy database session
            project_dir: Path to project directory
        """
        self.db = db_session
        self.project_dir = project_dir

    def create_fix_features(
        self,
        checkpoint_result: AggregatedCheckpointResult,
        current_priority: float = 100.0
    ) -> List[Feature]:
        """
        Create fix features for critical issues found in checkpoint.

        Args:
            checkpoint_result: Result from checkpoint orchestrator
            current_priority: Current feature priority (to insert fix before next feature)

        Returns:
            List of created fix features
        """
        fix_features = []

        # Only create fixes for critical issues
        critical_issues = [
            issue for issue in checkpoint_result.issues
            if issue.severity == IssueSeverity.CRITICAL
        ]

        if not critical_issues:
            return fix_features

        # Group issues by location (file) to avoid creating duplicate fix features
        issues_by_location = {}
        for issue in critical_issues:
            location = issue.location or "general"
            if location not in issues_by_location:
                issues_by_location[location] = []
            issues_by_location[location].append(issue)

        # Create one fix feature per location
        for location, issues in issues_by_location.items():
            fix_feature = self._create_fix_feature(
                location=location,
                issues=issues,
                priority=current_priority - 0.5  # Insert before next feature
            )
            fix_features.append(fix_feature)

        return fix_features

    def _create_fix_feature(
        self,
        location: str,
        issues: List[CheckpointIssue],
        priority: float
    ) -> Feature:
        """
        Create a single fix feature for a group of issues.

        Args:
            location: File location where issues were found
            issues: List of issues at this location
            priority: Priority for the fix feature

        Returns:
            Created Feature object
        """
        # Generate feature name
        issue_types = list(set(issue.title for issue in issues))
        if len(issue_types) == 1:
            name = f"Fix: {issue_types[0]} in {location}"
        else:
            name = f"Fix: {len(issues)} issues in {location}"

        # Generate description with all issues
        description_parts = [
            f"**Auto-generated fix feature for critical checkpoint issues in `{location}`**\n"
        ]

        for i, issue in enumerate(issues, 1):
            description_parts.append(f"\n{i}. **{issue.title}**")
            description_parts.append(f"   - {issue.description}")
            if issue.line_number:
                description_parts.append(f"   - Line: {issue.line_number}")
            if issue.suggestion:
                description_parts.append(f"   - Suggestion: {issue.suggestion}")

        description = '\n'.join(description_parts)

        # Generate implementation steps
        steps = []
        for i, issue in enumerate(issues, 1):
            step = f"Fix {issue.title}"
            if issue.location:
                step += f" in {issue.location}"
            if issue.line_number:
                step += f" (line {issue.line_number})"
            if issue.suggestion:
                step += f": {issue.suggestion}"
            steps.append(step)

        # Add verification step
        steps.append("Run checkpoint again to verify all issues are resolved")

        # Create feature in database
        fix_feature = Feature(
            priority=priority,
            category="checkpoint_fix",
            name=name,
            description=description,
            steps=steps,
            passes=False
        )

        self.db.add(fix_feature)
        self.db.commit()

        return fix_feature

    def should_create_fixes(self, checkpoint_result: AggregatedCheckpointResult) -> bool:
        """
        Determine if fix features should be created.

        Args:
            checkpoint_result: Result from checkpoint

        Returns:
            True if fix features should be created
        """
        # Create fixes if there are critical issues
        return checkpoint_result.total_critical > 0

    def get_fix_features(self) -> List[Feature]:
        """
        Get all checkpoint fix features.

        Returns:
            List of fix features
        """
        return (
            self.db.query(Feature)
            .filter(Feature.category == "checkpoint_fix")
            .order_by(Feature.priority.desc())
            .all()
        )

    def mark_fix_completed(self, feature_id: int):
        """
        Mark a fix feature as completed.

        Args:
            feature_id: ID of fix feature
        """
        feature = self.db.query(Feature).filter(Feature.id == feature_id).first()
        if feature and feature.category == "checkpoint_fix":
            feature.passes = True
            self.db.commit()

    def cleanup_completed_fixes(self):
        """Remove completed fix features from the database."""
        completed_fixes = (
            self.db.query(Feature)
            .filter(Feature.category == "checkpoint_fix")
            .filter(Feature.passes == True)
            .all()
        )

        for fix in completed_fixes:
            self.db.delete(fix)

        self.db.commit()

        return len(completed_fixes)


def create_fixes_if_needed(
    checkpoint_result: AggregatedCheckpointResult,
    db_session: Session,
    project_dir: Path,
    current_priority: float = 100.0
) -> List[Feature]:
    """
    Convenience function to create fix features if critical issues are found.

    Args:
        checkpoint_result: Result from checkpoint orchestrator
        db_session: Database session
        project_dir: Project directory
        current_priority: Current feature priority

    Returns:
        List of created fix features (empty if no fixes needed)
    """
    autofix = CheckpointAutoFix(db_session, project_dir)

    if autofix.should_create_fixes(checkpoint_result):
        return autofix.create_fix_features(checkpoint_result, current_priority)

    return []
