"""
Dependency Detection Engine
============================

Analyzes feature descriptions to automatically detect dependencies between features.
Uses keyword detection, explicit ID references, and category-based analysis.
"""

import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session

from api.database import Feature, FeatureDependency


class DependencyDetector:
    """Detects dependencies between features using multiple strategies."""

    # Keywords that indicate a dependency relationship
    DEPENDENCY_KEYWORDS = [
        "requires",
        "depends on",
        "after",
        "once",
        "when",
        "needs",
        "prerequisite",
        "blocked by",
        "build on",
        "using",
        "leverages",
        "extends",
        "based on",
    ]

    # Category-based implicit dependencies
    CATEGORY_DEPENDENCIES = {
        "authentication": [],  # Base category, no deps
        "authorization": ["authentication"],
        "user_profile": ["authentication"],
        "oauth": ["authentication"],
        "payments": ["authentication", "user_profile"],
        "notifications": ["authentication"],
        "email": [],
        "api": [],
        "frontend": ["api"],
        "dashboard": ["authentication", "api"],
        "admin": ["authentication", "authorization"],
    }

    def __init__(self, db_session: Session):
        """
        Initialize the dependency detector.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    def detect_all_dependencies(self) -> int:
        """
        Analyze all features and detect dependencies between them.

        Returns:
            Number of dependencies detected
        """
        all_features = self.db.query(Feature).all()
        total_detected = 0

        for feature in all_features:
            dependencies = self._detect_for_feature(feature, all_features)
            total_detected += len(dependencies)

            # Store in database
            for dep_data in dependencies:
                # Check if dependency already exists
                existing = (
                    self.db.query(FeatureDependency)
                    .filter_by(
                        feature_id=feature.id,
                        depends_on_feature_id=dep_data["depends_on"],
                    )
                    .first()
                )

                if not existing:
                    dependency = FeatureDependency(
                        feature_id=feature.id,
                        depends_on_feature_id=dep_data["depends_on"],
                        confidence=dep_data["confidence"],
                        detected_method=dep_data["method"],
                        detected_keywords=dep_data.get("keywords"),
                    )
                    self.db.add(dependency)

        self.db.commit()
        return total_detected

    def detect_dependencies(
        self, feature_or_id, all_features: Optional[List[Feature]] = None
    ):
        """
        Detect dependencies for a single feature.

        Can be called in two ways:
        1. detect_dependencies(feature_id) - Returns stored FeatureDependency objects from DB
        2. detect_dependencies(feature, all_features) - Returns dependency dictionaries

        Args:
            feature_or_id: Either a Feature object or feature ID (int)
            all_features: Optional list of all features (required if feature_or_id is Feature)

        Returns:
            If feature_or_id is int: List of FeatureDependency objects from database
            If feature_or_id is Feature: List of dependency dictionaries
        """
        # Case 1: Called with feature ID (integer)
        if isinstance(feature_or_id, int):
            feature_id = feature_or_id
            feature = self.db.query(Feature).filter_by(id=feature_id).first()
            if not feature:
                return []

            # Get or detect dependencies
            all_features = self.db.query(Feature).all()
            dep_dicts = self._detect_for_feature(feature, all_features)

            # Store in database if not already present
            for dep_data in dep_dicts:
                existing = (
                    self.db.query(FeatureDependency)
                    .filter_by(
                        feature_id=feature.id,
                        depends_on_feature_id=dep_data["depends_on"],
                    )
                    .first()
                )

                if not existing:
                    dependency = FeatureDependency(
                        feature_id=feature.id,
                        depends_on_feature_id=dep_data["depends_on"],
                        confidence=dep_data["confidence"],
                        detected_method=dep_data["method"],
                        detected_keywords=dep_data.get("keywords"),
                    )
                    self.db.add(dependency)

            self.db.commit()

            # Return FeatureDependency objects
            return (
                self.db.query(FeatureDependency)
                .filter_by(feature_id=feature_id)
                .all()
            )

        # Case 2: Called with Feature object (original behavior)
        else:
            feature = feature_or_id
            if all_features is None:
                raise ValueError("all_features is required when passing a Feature object")
            return self._detect_for_feature(feature, all_features)

    def _detect_for_feature(
        self, feature: Feature, all_features: List[Feature]
    ) -> List[Dict]:
        """
        Internal method to detect dependencies for a single feature.

        Args:
            feature: The feature to analyze
            all_features: List of all features to check against

        Returns:
            List of dependency dictionaries with metadata
        """
        dependencies = []

        # Strategy 1: Explicit feature ID references
        dependencies.extend(self._detect_id_references(feature, all_features))

        # Strategy 2: Keyword-based detection
        dependencies.extend(self._detect_keywords(feature, all_features))

        # Strategy 3: Category-based detection
        dependencies.extend(self._detect_categories(feature, all_features))

        # Deduplicate and sort by confidence
        return self._deduplicate_and_score(dependencies)

    def _detect_id_references(
        self, feature: Feature, all_features: List[Feature]
    ) -> List[Dict]:
        """
        Find explicit feature ID references like '#5' or 'Feature 12'.

        Args:
            feature: The feature to analyze
            all_features: List of all features

        Returns:
            List of detected dependencies
        """
        dependencies = []
        text = f"{feature.name} {feature.description}"

        # Pattern: #5, Feature 5, feature #5, etc.
        patterns = [
            r"#(\d+)",
            r"[Ff]eature\s+#?(\d+)",
            r"[Tt]ask\s+#?(\d+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                feature_id = int(match)

                # Verify feature exists
                if any(f.id == feature_id for f in all_features):
                    dependencies.append(
                        {
                            "depends_on": feature_id,
                            "confidence": 0.95,
                            "method": "explicit_id_reference",
                            "keywords": [f"#{feature_id}"],
                        }
                    )

        return dependencies

    def _detect_keywords(
        self, feature: Feature, all_features: List[Feature]
    ) -> List[Dict]:
        """
        Detect dependencies using keyword matching.

        Looks for phrases like "After OAuth is implemented" or "Requires authentication".

        Args:
            feature: The feature to analyze
            all_features: List of all features

        Returns:
            List of detected dependencies
        """
        dependencies = []
        text = f"{feature.name} {feature.description}".lower()

        for other_feature in all_features:
            if other_feature.id == feature.id:
                continue

            # Check if other feature is mentioned with a dependency keyword
            other_name = other_feature.name.lower()
            other_category = other_feature.category.lower()

            for keyword in self.DEPENDENCY_KEYWORDS:
                # Pattern: "keyword feature_name" or "keyword feature_category"
                patterns = [
                    rf"{keyword}\s+.*?{re.escape(other_name)}",
                    rf"{keyword}\s+.*?{re.escape(other_category)}",
                    rf"{re.escape(other_name)}.*?{keyword}",
                    rf"{re.escape(other_category)}.*?{keyword}",
                ]

                for pattern in patterns:
                    if re.search(pattern, text):
                        dependencies.append(
                            {
                                "depends_on": other_feature.id,
                                "confidence": 0.75,
                                "method": "keyword_detection",
                                "keywords": [keyword, other_name or other_category],
                            }
                        )
                        break  # Avoid duplicates for same feature

        return dependencies

    def _detect_categories(
        self, feature: Feature, all_features: List[Feature]
    ) -> List[Dict]:
        """
        Detect dependencies based on category relationships.

        For example, 'authorization' features typically depend on 'authentication'.

        Args:
            feature: The feature to analyze
            all_features: List of all features

        Returns:
            List of detected dependencies
        """
        dependencies = []
        feature_category = feature.category.lower()

        # Check if this category has known dependencies
        if feature_category in self.CATEGORY_DEPENDENCIES:
            required_categories = self.CATEGORY_DEPENDENCIES[feature_category]

            for required_category in required_categories:
                # Find features in the required category
                for other_feature in all_features:
                    if (
                        other_feature.category.lower() == required_category
                        and other_feature.id != feature.id
                    ):
                        dependencies.append(
                            {
                                "depends_on": other_feature.id,
                                "confidence": 0.65,
                                "method": "category_based",
                                "keywords": [feature_category, required_category],
                            }
                        )

        return dependencies

    def _deduplicate_and_score(self, dependencies: List[Dict]) -> List[Dict]:
        """
        Remove duplicate dependencies and keep the highest confidence.

        Args:
            dependencies: List of raw dependencies

        Returns:
            Deduplicated list sorted by confidence
        """
        # Group by depends_on ID
        grouped = {}
        for dep in dependencies:
            dep_id = dep["depends_on"]
            if dep_id not in grouped or dep["confidence"] > grouped[dep_id]["confidence"]:
                grouped[dep_id] = dep

        # Sort by confidence (highest first)
        result = list(grouped.values())
        result.sort(key=lambda x: x["confidence"], reverse=True)

        return result

    def get_dependencies_for_feature(self, feature_id: int) -> List[FeatureDependency]:
        """
        Get all dependencies for a specific feature.

        Args:
            feature_id: ID of the feature

        Returns:
            List of FeatureDependency objects
        """
        return (
            self.db.query(FeatureDependency)
            .filter_by(feature_id=feature_id)
            .order_by(FeatureDependency.confidence.desc())
            .all()
        )

    def get_dependent_features(self, feature_id: int) -> List[FeatureDependency]:
        """
        Get all features that depend on this feature.

        Args:
            feature_id: ID of the feature

        Returns:
            List of FeatureDependency objects where other features depend on this one
        """
        return (
            self.db.query(FeatureDependency)
            .filter_by(depends_on_feature_id=feature_id)
            .order_by(FeatureDependency.confidence.desc())
            .all()
        )

    def get_dependency_graph(self, feature_id: int, max_depth: int = 3) -> Dict:
        """
        Build a dependency tree for a feature.

        Args:
            feature_id: Root feature ID
            max_depth: Maximum depth to traverse

        Returns:
            Nested dictionary representing the dependency tree
        """
        feature = self.db.query(Feature).filter_by(id=feature_id).first()
        if not feature:
            return {}

        def build_tree(fid: int, depth: int) -> Dict:
            if depth >= max_depth:
                return {}

            dependents = self.get_dependent_features(fid)
            tree = {}

            for dep in dependents:
                child_feature = self.db.query(Feature).filter_by(id=dep.feature_id).first()
                if child_feature:
                    tree[child_feature.id] = {
                        "name": child_feature.name,
                        "confidence": dep.confidence,
                        "children": build_tree(child_feature.id, depth + 1),
                    }

            return tree

        return {
            "feature_id": feature_id,
            "feature_name": feature.name,
            "dependents": build_tree(feature_id, 0),
        }


def run_dependency_detection(project_dir: Path) -> Dict[str, int]:
    """
    Run dependency detection for a project.

    Args:
        project_dir: Path to the project directory

    Returns:
        Statistics about detected dependencies
    """
    from api.database import create_database

    # Initialize database
    engine, SessionLocal = create_database(project_dir)
    db = SessionLocal()

    try:
        # Run detection
        detector = DependencyDetector(db)
        total_detected = detector.detect_all_dependencies()

        # Gather statistics
        total_features = db.query(Feature).count()
        total_dependencies = db.query(FeatureDependency).count()

        features_with_deps = (
            db.query(FeatureDependency.feature_id)
            .distinct()
            .count()
        )

        return {
            "total_features": total_features,
            "total_dependencies": total_dependencies,
            "features_with_dependencies": features_with_deps,
            "newly_detected": total_detected,
        }
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
        print(f"Running dependency detection on: {project_path}")
        stats = run_dependency_detection(project_path)
        print("\nDependency Detection Results:")
        print(f"  Total features: {stats['total_features']}")
        print(f"  Total dependencies: {stats['total_dependencies']}")
        print(f"  Features with dependencies: {stats['features_with_dependencies']}")
        print(f"  Newly detected: {stats['newly_detected']}")
    else:
        print("Usage: python dependency_detector.py <project_dir>")
