"""
Skip Impact Analyzer
===================

Analyzes the impact of skipping a feature by examining dependencies
and providing recommendations for how to proceed.
"""

from typing import Dict, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session

from api.database import Feature, FeatureDependency
from tools.dependency_detector import DependencyDetector


class SkipImpactAnalyzer:
    """Analyzes the impact of skipping a feature."""

    def __init__(self, db_session: Session):
        """
        Initialize the skip impact analyzer.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.detector = DependencyDetector(db_session)

    def analyze_skip_impact(self, feature_id: int) -> Dict:
        """
        Analyze the impact of skipping a feature.

        Args:
            feature_id: ID of the feature to skip

        Returns:
            Dictionary with impact analysis and recommendations
        """
        feature = self.db.query(Feature).filter_by(id=feature_id).first()
        if not feature:
            return {"error": f"Feature {feature_id} not found"}

        # Get all features that depend on this one
        dependents = self.detector.get_dependent_features(feature_id)

        # Build full dependency tree
        dep_tree = self.detector.get_dependency_graph(feature_id, max_depth=3)

        # Calculate impact metrics
        immediate_count = len(dependents)
        total_impact = self._count_all_descendants(dep_tree)

        # Generate recommendations
        recommendation = self._suggest_action(dependents, total_impact)

        # Build detailed impact report
        return {
            "feature_id": feature_id,
            "feature_name": feature.name,
            "feature_category": feature.category,
            "immediate_dependents": immediate_count,
            "total_impact": total_impact,
            "dependency_tree": dep_tree,
            "dependent_features": [
                {
                    "id": d.feature_id,
                    "name": self.db.query(Feature).filter_by(id=d.feature_id).first().name,
                    "confidence": d.confidence,
                    "method": d.detected_method,
                }
                for d in dependents
            ],
            "recommendation": recommendation,
            "suggested_action": self._get_action_code(recommendation),
        }

    def _count_all_descendants(self, tree: Dict, count: int = 0) -> int:
        """
        Count all descendants in a dependency tree recursively.

        Args:
            tree: Dependency tree dictionary
            count: Current count

        Returns:
            Total count of descendants
        """
        if "dependents" not in tree:
            return count

        dependents = tree["dependents"]
        count += len(dependents)

        for dep_id, dep_data in dependents.items():
            if "children" in dep_data and dep_data["children"]:
                count = self._count_all_descendants({"dependents": dep_data["children"]}, count)

        return count

    def _suggest_action(self, dependents: List[FeatureDependency], total_impact: int) -> str:
        """
        Suggest the best action when skipping a feature.

        Args:
            dependents: List of dependent features
            total_impact: Total number of features affected

        Returns:
            Recommendation string
        """
        if not dependents:
            return "SAFE_TO_SKIP"
        elif len(dependents) >= 5 or total_impact >= 10:
            return "CASCADE_SKIP"  # Skip all dependents too
        elif total_impact <= 3:
            return "IMPLEMENT_WITH_MOCKS"  # Use placeholders
        else:
            return "REVIEW_DEPENDENCIES"  # Manual review recommended

    def _get_action_code(self, recommendation: str) -> str:
        """
        Get action code for recommendation.

        Args:
            recommendation: Recommendation string

        Returns:
            Action code
        """
        actions = {
            "SAFE_TO_SKIP": "skip",
            "CASCADE_SKIP": "cascade",
            "IMPLEMENT_WITH_MOCKS": "mock",
            "REVIEW_DEPENDENCIES": "review",
        }
        return actions.get(recommendation, "review")

    def generate_skip_report(self, feature_id: int) -> str:
        """
        Generate a formatted skip impact report.

        Args:
            feature_id: ID of the feature to skip

        Returns:
            Formatted report string
        """
        analysis = self.analyze_skip_impact(feature_id)

        if "error" in analysis:
            return f"❌ {analysis['error']}"

        report = []
        report.append("\n⚠️  SKIP IMPACT ANALYSIS")
        report.append("━" * 50)
        report.append(f"\nSkipping Feature #{feature_id}: \"{analysis['feature_name']}\"")
        report.append(f"Category: {analysis['feature_category']}")

        if analysis["immediate_dependents"] == 0:
            report.append("\n✅ No downstream dependencies detected.")
            report.append("This feature can be safely skipped without impacting other work.")
        else:
            report.append(f"\n⚠️  Downstream impact ({analysis['immediate_dependents']} features depend on this):")

            for dep in analysis["dependent_features"]:
                confidence_icon = "🔴" if dep["confidence"] >= 0.8 else "🟡" if dep["confidence"] >= 0.6 else "⚪"
                report.append(f"  {confidence_icon} Feature #{dep['id']}: {dep['name']}")
                report.append(f"      Confidence: {dep['confidence']:.0%} (detected via {dep['method']})")

            if analysis["total_impact"] > analysis["immediate_dependents"]:
                indirect = analysis["total_impact"] - analysis["immediate_dependents"]
                report.append(f"\n  + {indirect} more features indirectly affected (cascade depth: 2-3 levels)")

        # Add recommendation
        report.append("\n📋 RECOMMENDATION")
        report.append("━" * 50)

        recommendation = analysis["recommendation"]

        if recommendation == "SAFE_TO_SKIP":
            report.append("✅ Safe to skip")
            report.append("   No dependent features detected. Proceed with skip.")

        elif recommendation == "CASCADE_SKIP":
            report.append("⚠️  CASCADE SKIP recommended")
            report.append("   Large downstream impact detected.")
            report.append("   Consider skipping all dependent features too to avoid implementation issues.")

        elif recommendation == "IMPLEMENT_WITH_MOCKS":
            report.append("💡 IMPLEMENT WITH MOCKS recommended")
            report.append("   Implement dependent features with documented assumptions and placeholders.")
            report.append("   Mark them for review when this feature is eventually implemented.")

        elif recommendation == "REVIEW_DEPENDENCIES":
            report.append("🔍 MANUAL REVIEW recommended")
            report.append("   Moderate downstream impact. Review each dependent feature individually.")

        # Add action options
        report.append("\n🎯 ACTIONS")
        report.append("━" * 50)
        report.append("  [1] Skip all dependent features (cascade)")
        report.append("  [2] Implement dependents with mocks/placeholders")
        report.append("  [3] Cancel skip (implement this feature now)")
        report.append("  [4] Continue anyway (expert mode)")

        return "\n".join(report)

    def cascade_skip(self, feature_id: int, reason: str = "Depends on skipped feature") -> List[int]:
        """
        Skip a feature and all its dependents recursively.

        Args:
            feature_id: ID of the feature to skip
            reason: Reason for cascading skip

        Returns:
            List of feature IDs that were cascaded
        """
        cascaded = []
        dependents = self.detector.get_dependent_features(feature_id)

        for dep in dependents:
            dependent_feature = self.db.query(Feature).filter_by(id=dep.feature_id).first()
            if dependent_feature and not dependent_feature.was_skipped:
                # Mark as skipped
                dependent_feature.was_skipped = True
                dependent_feature.skip_count += 1
                dependent_feature.blocker_type = "CASCADE_SKIP"
                dependent_feature.blocker_description = f"{reason}: Feature #{feature_id}"

                # Move to end of queue
                max_priority = self.db.query(Feature.priority).order_by(Feature.priority.desc()).first()
                if max_priority:
                    dependent_feature.priority = max_priority[0] + 1

                cascaded.append(dep.feature_id)

                # Recursively cascade
                cascaded.extend(self.cascade_skip(dep.feature_id, reason))

        self.db.commit()
        return cascaded

    def mark_for_mock_implementation(self, feature_id: int, dependency_id: int) -> bool:
        """
        Mark a feature to be implemented with mocks/placeholders.

        Args:
            feature_id: Feature to implement with mocks
            dependency_id: Feature it depends on (that was skipped)

        Returns:
            True if successful
        """
        from api.database import FeatureAssumption

        feature = self.db.query(Feature).filter_by(id=feature_id).first()
        dependency = self.db.query(Feature).filter_by(id=dependency_id).first()

        if not feature or not dependency:
            return False

        # Create assumption record
        assumption = FeatureAssumption(
            feature_id=feature_id,
            depends_on_feature_id=dependency_id,
            assumption_text=f"Feature will be implemented using mocks/placeholders until Feature #{dependency_id} ({dependency.name}) is completed.",
            status="ACTIVE",
        )
        self.db.add(assumption)

        # Mark feature for mock implementation
        feature.passing_with_mocks = True

        self.db.commit()
        return True


def analyze_skip(project_dir: Path, feature_id: int) -> None:
    """
    Analyze and display skip impact for a feature.

    Args:
        project_dir: Path to the project directory
        feature_id: ID of the feature to analyze
    """
    from api.database import create_database

    # Initialize database
    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        analyzer = SkipImpactAnalyzer(db)
        report = analyzer.generate_skip_report(feature_id)
        print(report)
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) > 2:
        project_path = Path(sys.argv[1])
        feature_id = int(sys.argv[2])
        analyze_skip(project_path, feature_id)
    else:
        print("Usage: python skip_analyzer.py <project_dir> <feature_id>")
