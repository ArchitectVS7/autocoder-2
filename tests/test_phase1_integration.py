#!/usr/bin/env python3
"""
Phase 1 Integration Tests
==========================

Comprehensive integration tests for Phase 1: Skip Management & Dependency Tracking

Tests cover:
1. Database schema and migrations
2. Dependency detection engine
3. Skip impact analysis
4. Blocker classification
5. Human intervention workflow
6. BLOCKERS.md generation
7. Unblock commands
8. Assumptions tracking

Run with: pytest tests/test_phase1_integration.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from api.database import (
    create_database, Feature, FeatureDependency,
    FeatureAssumption, FeatureBlocker
)
from tools.dependency_detector import DependencyDetector
from tools.skip_analyzer import SkipImpactAnalyzer
from tools.blocker_classifier import BlockerClassifier, BlockerType
from design.human_intervention import HumanInterventionHandler
from tools.blockers_md_generator import BlockersMdGenerator
from tools.assumptions_workflow import AssumptionsWorkflow, should_document_assumptions


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def db_session(temp_project_dir):
    """Create a database session for testing."""
    _, SessionLocal = create_database(temp_project_dir)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_features(db_session):
    """Create sample features for testing."""
    features = [
        Feature(
            id=1,
            priority=1,
            category="authentication",
            name="Basic user authentication",
            description="Implement basic username/password authentication",
            steps=["Create login form", "Hash passwords", "Create session"],
            passes=True
        ),
        Feature(
            id=5,
            priority=5,
            category="authentication",
            name="OAuth authentication",
            description="Add OAuth support with Google provider",
            steps=["Set up OAuth client", "Handle callback", "Store tokens"],
            passes=False,
            was_skipped=True,
            skip_count=1,
            blocker_type=BlockerType.ENV_CONFIG.value,  # "environment_config"
            blocker_description="Missing OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET"
        ),
        Feature(
            id=12,
            priority=12,
            category="profile",
            name="User profile OAuth avatar",
            description="After OAuth is implemented (#5), show user's avatar from provider",
            steps=["Get avatar URL from OAuth", "Display in profile", "Handle errors"],
            passes=False
        ),
        Feature(
            id=23,
            priority=23,
            category="integration",
            name="Third-party account linking",
            description="Allow users to link third-party accounts using OAuth feature #5",
            steps=["Link accounts", "Sync data", "Handle disconnects"],
            passes=False
        ),
    ]

    for feature in features:
        db_session.add(feature)
    db_session.commit()

    return features


class TestDatabaseSchema:
    """Test database schema and migrations."""

    def test_feature_table_has_phase1_columns(self, db_session):
        """Test that Feature table has all Phase 1 columns."""
        feature = Feature(
            priority=1,
            category="test",
            name="Test feature",
            description="Test description",
            steps=["Step 1"],
            was_skipped=True,
            skip_count=2,
            blocker_type=BlockerType.ENV_CONFIG.value,  # "environment_config"
            blocker_description="Test blocker",
            is_blocked=True,
            passing_with_mocks=True
        )
        db_session.add(feature)
        db_session.commit()

        # Verify all fields saved correctly
        saved = db_session.query(Feature).filter(Feature.id == feature.id).first()
        assert saved.was_skipped is True
        assert saved.skip_count == 2
        assert saved.blocker_type == BlockerType.ENV_CONFIG.value  # "environment_config"
        assert saved.blocker_description == "Test blocker"
        assert saved.is_blocked is True
        assert saved.passing_with_mocks is True

    def test_feature_dependency_table(self, db_session, sample_features):
        """Test FeatureDependency table."""
        dep = FeatureDependency(
            feature_id=12,
            depends_on_feature_id=5,
            confidence=0.85,
            detected_method="keyword_detection",
            detected_keywords=["after", "oauth"]
        )
        db_session.add(dep)
        db_session.commit()

        # Verify saved correctly
        saved = db_session.query(FeatureDependency).filter(
            FeatureDependency.id == dep.id
        ).first()
        assert saved.feature_id == 12
        assert saved.depends_on_feature_id == 5
        assert saved.confidence == 0.85
        assert saved.detected_method == "keyword_detection"
        assert "oauth" in saved.detected_keywords

    def test_feature_assumption_table(self, db_session, sample_features):
        """Test FeatureAssumption table."""
        assumption = FeatureAssumption(
            feature_id=12,
            depends_on_feature_id=5,
            assumption_text="OAuth will use Google OAuth provider",
            code_location="src/api/users.js:145-152",
            impact_description="If different provider, must update avatar URL parsing",
            status="ACTIVE"
        )
        db_session.add(assumption)
        db_session.commit()

        # Verify saved correctly
        saved = db_session.query(FeatureAssumption).filter(
            FeatureAssumption.id == assumption.id
        ).first()
        assert saved.feature_id == 12
        assert saved.depends_on_feature_id == 5
        assert "Google OAuth" in saved.assumption_text
        assert saved.status == "ACTIVE"

    def test_feature_blocker_table(self, db_session, sample_features):
        """Test FeatureBlocker table."""
        blocker = FeatureBlocker(
            feature_id=5,
            blocker_type="ENV_CONFIG",
            blocker_description="Missing OAuth credentials",
            required_action="Add credentials to .env",
            required_values=["OAUTH_CLIENT_ID", "OAUTH_CLIENT_SECRET"],
            status="ACTIVE"
        )
        db_session.add(blocker)
        db_session.commit()

        # Verify saved correctly
        saved = db_session.query(FeatureBlocker).filter(
            FeatureBlocker.id == blocker.id
        ).first()
        assert saved.blocker_type == "ENV_CONFIG"
        assert "OAUTH_CLIENT_ID" in saved.required_values
        assert saved.status == "ACTIVE"


class TestDependencyDetection:
    """Test dependency detection engine."""

    def test_detect_explicit_id_references(self, db_session, sample_features):
        """Test detection of explicit feature ID references."""
        detector = DependencyDetector(db_session)

        # Feature #12 references "#5" in description
        dependencies = detector.detect_dependencies(12)

        assert len(dependencies) > 0
        assert any(d.depends_on_feature_id == 5 for d in dependencies)

    def test_detect_keyword_dependencies(self, db_session, sample_features):
        """Test keyword-based dependency detection."""
        detector = DependencyDetector(db_session)

        # Feature #12 has "After OAuth is implemented"
        dependencies = detector.detect_dependencies(12)

        # Should detect dependency on OAuth feature
        oauth_dep = next((d for d in dependencies if d.depends_on_feature_id == 5), None)
        assert oauth_dep is not None
        assert oauth_dep.detected_method in ["keyword_detection", "explicit_id_reference"]

    def test_dependency_confidence_scores(self, db_session, sample_features):
        """Test confidence scoring for dependencies."""
        detector = DependencyDetector(db_session)
        dependencies = detector.detect_dependencies(12)

        # Explicit references should have high confidence
        for dep in dependencies:
            if dep.detected_method == "explicit_id_reference":
                assert dep.confidence >= 0.9
            elif dep.detected_method == "keyword_detection":
                assert dep.confidence >= 0.7


class TestSkipImpactAnalysis:
    """Test skip impact analysis."""

    def test_analyze_skip_with_dependents(self, db_session, sample_features):
        """Test impact analysis when skipping a feature with dependents."""
        # First detect dependencies
        detector = DependencyDetector(db_session)
        detector.detect_all_dependencies()

        # Analyze impact of skipping Feature #5
        analyzer = SkipImpactAnalyzer(db_session)
        impact = analyzer.analyze_skip_impact(5)

        assert impact is not None
        assert impact['feature_id'] == 5
        assert impact['immediate_dependents'] >= 2  # Features 12 and 23

    def test_skip_recommendations(self, db_session, sample_features):
        """Test skip recommendations based on impact."""
        detector = DependencyDetector(db_session)
        detector.detect_all_dependencies()

        analyzer = SkipImpactAnalyzer(db_session)
        impact = analyzer.analyze_skip_impact(5)

        # Should recommend implementing with mocks or cascade skip
        # Check the full recommendation (not the short action code)
        recommendation = impact.get('recommendation')
        assert recommendation in ['CASCADE_SKIP', 'IMPLEMENT_WITH_MOCKS', 'REVIEW_DEPENDENCIES', 'SAFE_TO_SKIP']

        # Also verify the short action code is present
        action_code = impact.get('suggested_action')
        assert action_code in ['skip', 'cascade', 'mock', 'review']


class TestBlockerClassification:
    """Test blocker classification system."""

    def test_classify_env_config_blocker(self, db_session):
        """Test classification of environment config blockers."""
        classifier = BlockerClassifier(db_session)

        blocker_type = classifier.classify_blocker_text(
            "Missing OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET environment variables"
        )

        assert blocker_type == BlockerType.ENV_CONFIG

    def test_classify_external_service_blocker(self, db_session):
        """Test classification of external service blockers."""
        classifier = BlockerClassifier(db_session)

        blocker_type = classifier.classify_blocker_text(
            "Need to set up Stripe account and API key"
        )

        assert blocker_type == BlockerType.EXTERNAL_SERVICE

    def test_classify_unclear_requirements_blocker(self, db_session):
        """Test classification of unclear requirements."""
        classifier = BlockerClassifier(db_session)

        blocker_type = classifier.classify_blocker_text(
            "What should the error message say when login fails?"
        )

        assert blocker_type == BlockerType.UNCLEAR_REQUIREMENTS

    def test_extract_required_values(self, db_session):
        """Test extraction of required values from blocker description."""
        classifier = BlockerClassifier(db_session)

        required = classifier.extract_required_values(
            "Missing OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, and OAUTH_PROVIDER"
        )

        assert "OAUTH_CLIENT_ID" in required
        assert "OAUTH_CLIENT_SECRET" in required
        assert "OAUTH_PROVIDER" in required


class TestAssumptionsWorkflow:
    """Test assumptions tracking workflow."""

    def test_check_for_skipped_dependencies(self, db_session, sample_features):
        """Test checking for skipped dependencies."""
        # Set up dependencies
        detector = DependencyDetector(db_session)
        detector.detect_all_dependencies()

        workflow = AssumptionsWorkflow(db_session)

        # Feature #12 depends on skipped Feature #5
        skipped_deps = workflow.check_for_skipped_dependencies(12)

        assert len(skipped_deps) > 0
        assert any(d['dependency_id'] == 5 for d in skipped_deps)

    def test_create_assumption(self, db_session, sample_features):
        """Test creating an assumption."""
        workflow = AssumptionsWorkflow(db_session)

        assumption = workflow.create_assumption(
            feature_id=12,
            depends_on_feature_id=5,
            assumption_text="OAuth will use Google OAuth provider",
            code_location="src/api/users.js:145-152",
            impact_description="If different provider chosen, avatar URL parsing needs update"
        )

        assert assumption.id is not None
        assert assumption.status == "ACTIVE"
        assert assumption.feature_id == 12
        assert assumption.depends_on_feature_id == 5

    def test_get_assumptions_for_review(self, db_session, sample_features):
        """Test getting assumptions for review."""
        workflow = AssumptionsWorkflow(db_session)

        # Create an assumption
        workflow.create_assumption(
            feature_id=12,
            depends_on_feature_id=5,
            assumption_text="Test assumption",
            code_location="test.js:1"
        )

        # Get assumptions for review when Feature #5 is completed
        assumptions = workflow.get_assumptions_for_review(5)

        assert len(assumptions) > 0
        assert assumptions[0].depends_on_feature_id == 5

    def test_validate_assumption(self, db_session, sample_features):
        """Test validating an assumption."""
        workflow = AssumptionsWorkflow(db_session)

        # Create an assumption
        assumption = workflow.create_assumption(
            feature_id=12,
            depends_on_feature_id=5,
            assumption_text="Test assumption",
            code_location="test.js:1"
        )

        # Validate it
        success = workflow.validate_assumption(assumption.id)

        assert success is True

        # Check status changed
        updated = db_session.query(FeatureAssumption).filter(
            FeatureAssumption.id == assumption.id
        ).first()
        assert updated.status == "VALIDATED"
        assert updated.validated_at is not None

    def test_invalidate_assumption(self, db_session, sample_features):
        """Test invalidating an assumption."""
        workflow = AssumptionsWorkflow(db_session)

        # Create an assumption
        assumption = workflow.create_assumption(
            feature_id=12,
            depends_on_feature_id=5,
            assumption_text="Test assumption",
            code_location="test.js:1"
        )

        # Invalidate it
        success, feature_id = workflow.invalidate_assumption(assumption.id)

        assert success is True
        assert feature_id == 12

        # Check status changed
        updated = db_session.query(FeatureAssumption).filter(
            FeatureAssumption.id == assumption.id
        ).first()
        assert updated.status == "INVALID"

    def test_assumption_statistics(self, db_session, sample_features):
        """Test getting assumption statistics."""
        workflow = AssumptionsWorkflow(db_session)

        # Create some assumptions with different statuses
        a1 = workflow.create_assumption(12, 5, "Test 1", "test1.js:1")
        a2 = workflow.create_assumption(23, 5, "Test 2", "test2.js:1")
        workflow.validate_assumption(a1.id)
        workflow.invalidate_assumption(a2.id)

        stats = workflow.get_assumption_statistics()

        assert stats['total'] >= 2
        assert stats['validated'] >= 1
        assert stats['invalid'] >= 1
        assert 0 <= stats['accuracy_rate'] <= 100


class TestHumanInterventionWorkflow:
    """Test human intervention workflow (Task 1.5)."""

    def test_check_for_blockers(self, db_session, sample_features, temp_project_dir):
        """Test checking for active blockers requiring intervention."""
        handler = HumanInterventionHandler(db_session, temp_project_dir)

        # Create a blocker
        blocker = FeatureBlocker(
            feature_id=5,
            blocker_type=BlockerType.ENV_CONFIG.value,  # "environment_config"
            blocker_description="Missing OAUTH_CLIENT_ID",
            required_values=["OAUTH_CLIENT_ID", "OAUTH_CLIENT_SECRET"],
            status="ACTIVE"
        )
        db_session.add(blocker)
        db_session.commit()

        # Check for blockers
        found_blocker = handler.check_for_blockers(5)

        assert found_blocker is not None
        assert found_blocker.feature_id == 5
        assert found_blocker.status == "ACTIVE"

    def test_write_to_env_new_file(self, db_session, temp_project_dir):
        """Test writing values to a new .env file."""
        handler = HumanInterventionHandler(db_session, temp_project_dir)

        values = {
            "OAUTH_CLIENT_ID": "test_client_id",
            "OAUTH_CLIENT_SECRET": "test_secret"
        }

        result = handler._write_to_env(values)

        assert result is True

        # Verify .env file was created
        env_path = temp_project_dir / ".env"
        assert env_path.exists()

        # Verify contents
        content = env_path.read_text()
        assert "OAUTH_CLIENT_ID=test_client_id" in content
        assert "OAUTH_CLIENT_SECRET=test_secret" in content

    def test_write_to_env_existing_file(self, db_session, temp_project_dir):
        """Test writing values to an existing .env file."""
        handler = HumanInterventionHandler(db_session, temp_project_dir)

        # Create existing .env file
        env_path = temp_project_dir / ".env"
        env_path.write_text("EXISTING_VAR=existing_value\n")

        values = {
            "NEW_VAR": "new_value",
            "EXISTING_VAR": "should_skip"  # Should not overwrite
        }

        result = handler._write_to_env(values)

        assert result is True

        # Verify contents
        content = env_path.read_text()
        assert "EXISTING_VAR=existing_value" in content
        assert "NEW_VAR=new_value" in content
        # Should only appear once (the original)
        assert content.count("EXISTING_VAR") == 1

    def test_setup_mock_implementation(self, db_session, sample_features, temp_project_dir):
        """Test setting up mock implementation for blocked feature."""
        handler = HumanInterventionHandler(db_session, temp_project_dir)

        feature = db_session.query(Feature).filter_by(id=5).first()
        blocker = FeatureBlocker(
            feature_id=5,
            blocker_type="EXTERNAL_SERVICE",
            blocker_description="Stripe API not configured",
            status="ACTIVE"
        )
        db_session.add(blocker)
        db_session.commit()

        # Setup mock
        result = handler._setup_mock_implementation(feature, blocker)

        assert result is True
        assert feature.passing_with_mocks is True

        # Verify assumption was created
        assumption = db_session.query(FeatureAssumption).filter_by(
            feature_id=5
        ).first()

        assert assumption is not None
        assert "mock" in assumption.assumption_text.lower()
        assert assumption.status == "ACTIVE"

    def test_add_to_blockers_md(self, db_session, sample_features, temp_project_dir):
        """Test adding blocker to BLOCKERS.md."""
        handler = HumanInterventionHandler(db_session, temp_project_dir)

        feature = db_session.query(Feature).filter_by(id=5).first()
        blocker = FeatureBlocker(
            feature_id=5,
            blocker_type="ENV_CONFIG",
            blocker_description="Missing OAuth credentials",
            required_values=["OAUTH_CLIENT_ID"],
            status="ACTIVE"
        )
        db_session.add(blocker)
        db_session.commit()

        # Add to BLOCKERS.md
        result = handler._add_to_blockers_md(feature, blocker)

        assert result is True

        # Verify BLOCKERS.md was created
        blockers_path = temp_project_dir / "BLOCKERS.md"
        assert blockers_path.exists()

        # Verify contents
        content = blockers_path.read_text()
        assert "OAuth" in content or "OAUTH" in content

    def test_handle_skip_with_intervention_no_intervention_needed(self, db_session, sample_features, temp_project_dir):
        """Test handling skip when no human intervention is needed."""
        handler = HumanInterventionHandler(db_session, temp_project_dir)

        # LEGITIMATE_DEFERRAL doesn't require intervention
        should_pause, action = handler.handle_skip_with_intervention(
            5, "This feature is not needed for MVP"
        )

        assert should_pause is False
        assert action == "SKIP"

        # Verify blocker was created
        blocker = db_session.query(FeatureBlocker).filter_by(feature_id=5).first()
        assert blocker is not None


class TestBlockersMdGeneration:
    """Test BLOCKERS.md generation (Task 1.6)."""

    def test_generate_with_blockers(self, db_session, sample_features):
        """Test generating BLOCKERS.md with active blockers."""
        generator = BlockersMdGenerator(db_session)

        # Create some blockers
        blocker1 = FeatureBlocker(
            feature_id=5,
            blocker_type="ENV_CONFIG",
            blocker_description="Missing OAuth credentials",
            required_values=["OAUTH_CLIENT_ID", "OAUTH_CLIENT_SECRET"],
            status="ACTIVE"
        )
        blocker2 = FeatureBlocker(
            feature_id=12,
            blocker_type="EXTERNAL_SERVICE",
            blocker_description="Stripe API not configured",
            status="ACTIVE"
        )
        db_session.add(blocker1)
        db_session.add(blocker2)
        db_session.commit()

        # Generate content
        content = generator.generate([blocker1, blocker2])

        assert "Blockers Requiring Human Input" in content
        assert "Total blockers: 2" in content
        assert "OAuth" in content or "OAUTH" in content
        assert "Stripe" in content
        assert "Feature #5" in content
        assert "Feature #12" in content

    def test_generate_empty_file(self, db_session):
        """Test generating BLOCKERS.md with no blockers."""
        generator = BlockersMdGenerator(db_session)

        content = generator.generate([])

        assert "Blockers Requiring Human Input" in content
        assert "No active blockers" in content

    def test_group_by_type(self, db_session, sample_features):
        """Test grouping blockers by type."""
        generator = BlockersMdGenerator(db_session)

        blockers = [
            FeatureBlocker(
                feature_id=5,
                blocker_type="ENV_CONFIG",
                blocker_description="Missing env vars",
                status="ACTIVE"
            ),
            FeatureBlocker(
                feature_id=12,
                blocker_type="ENV_CONFIG",
                blocker_description="Missing API keys",
                status="ACTIVE"
            ),
            FeatureBlocker(
                feature_id=23,
                blocker_type="EXTERNAL_SERVICE",
                blocker_description="Service not configured",
                status="ACTIVE"
            ),
        ]

        grouped = generator._group_by_type(blockers)

        assert "ENV_CONFIG" in grouped
        assert "EXTERNAL_SERVICE" in grouped
        assert len(grouped["ENV_CONFIG"]) == 2
        assert len(grouped["EXTERNAL_SERVICE"]) == 1

    def test_update_file(self, db_session, sample_features, temp_project_dir):
        """Test updating BLOCKERS.md file."""
        generator = BlockersMdGenerator(db_session)

        # Create a blocker
        blocker = FeatureBlocker(
            feature_id=5,
            blocker_type="ENV_CONFIG",
            blocker_description="Missing credentials",
            required_values=["API_KEY"],
            status="ACTIVE"
        )
        db_session.add(blocker)
        db_session.commit()

        # Update file
        result = generator.update(temp_project_dir)

        assert result is True

        # Verify file exists and has content
        blockers_file = temp_project_dir / "BLOCKERS.md"
        assert blockers_file.exists()

        content = blockers_file.read_text()
        assert "Feature #5" in content
        assert "API_KEY" in content

    def test_get_summary(self, db_session, sample_features):
        """Test getting blocker summary statistics."""
        generator = BlockersMdGenerator(db_session)

        # Create blockers
        blocker1 = FeatureBlocker(
            feature_id=5,
            blocker_type="ENV_CONFIG",
            blocker_description="Test 1",
            status="ACTIVE"
        )
        blocker2 = FeatureBlocker(
            feature_id=5,
            blocker_type="EXTERNAL_SERVICE",
            blocker_description="Test 2",
            status="ACTIVE"
        )
        blocker3 = FeatureBlocker(
            feature_id=12,
            blocker_type="ENV_CONFIG",
            blocker_description="Test 3",
            status="ACTIVE"
        )
        db_session.add_all([blocker1, blocker2, blocker3])
        db_session.commit()

        summary = generator.get_summary()

        assert summary["total"] == 3
        assert summary["features_blocked"] == 2  # Features 5 and 12
        assert "ENV_CONFIG" in summary["by_type"]
        assert "EXTERNAL_SERVICE" in summary["by_type"]
        assert summary["by_type"]["ENV_CONFIG"] == 2
        assert summary["by_type"]["EXTERNAL_SERVICE"] == 1


class TestUnblockCommands:
    """Test unblock CLI commands (Task 1.7)."""

    def test_cmd_unblock(self, db_session, sample_features, temp_project_dir):
        """Test unblocking a specific feature."""
        from blockers_cli import cmd_unblock

        # Create a blocked feature with blocker
        feature = db_session.query(Feature).filter_by(id=5).first()
        feature.is_blocked = True
        feature.blocker_type = "ENV_CONFIG"
        feature.blocker_description = "Missing credentials"

        blocker = FeatureBlocker(
            feature_id=5,
            blocker_type="ENV_CONFIG",
            blocker_description="Missing credentials",
            status="ACTIVE"
        )
        db_session.add(blocker)
        db_session.commit()

        # Unblock the feature
        result = cmd_unblock(temp_project_dir, 5)

        assert result is True

        # Verify feature is unblocked
        updated_feature = db_session.query(Feature).filter_by(id=5).first()
        assert updated_feature.is_blocked is False
        assert updated_feature.blocker_type is None

        # Verify blocker is resolved
        updated_blocker = db_session.query(FeatureBlocker).filter_by(id=blocker.id).first()
        assert updated_blocker.status == "RESOLVED"
        assert updated_blocker.resolution_action == "MANUAL_UNBLOCK"
        assert updated_blocker.resolved_at is not None

    def test_cmd_unblock_nonexistent_feature(self, db_session, temp_project_dir):
        """Test unblocking a feature that doesn't exist."""
        from blockers_cli import cmd_unblock

        result = cmd_unblock(temp_project_dir, 9999)

        assert result is False

    def test_cmd_unblock_all(self, db_session, sample_features, temp_project_dir):
        """Test unblocking all blocked features."""
        from blockers_cli import cmd_unblock_all

        # Block multiple features
        features = db_session.query(Feature).filter(Feature.id.in_([5, 12])).all()
        for feature in features:
            feature.is_blocked = True
            blocker = FeatureBlocker(
                feature_id=feature.id,
                blocker_type="ENV_CONFIG",
                blocker_description="Test blocker",
                status="ACTIVE"
            )
            db_session.add(blocker)

        db_session.commit()

        # Unblock all
        result = cmd_unblock_all(temp_project_dir)

        assert result is True

        # Verify all features are unblocked
        blocked_count = db_session.query(Feature).filter_by(is_blocked=True).count()
        assert blocked_count == 0

        # Verify all blockers are resolved
        active_blockers = db_session.query(FeatureBlocker).filter_by(status="ACTIVE").count()
        assert active_blockers == 0

    def test_cmd_unblock_all_no_blockers(self, db_session, temp_project_dir):
        """Test unblock-all when there are no blocked features."""
        from blockers_cli import cmd_unblock_all

        result = cmd_unblock_all(temp_project_dir)

        assert result is True

    def test_cmd_show_blockers(self, db_session, sample_features, temp_project_dir):
        """Test showing active blockers."""
        from blockers_cli import cmd_show_blockers

        # Create some blockers
        blocker = FeatureBlocker(
            feature_id=5,
            blocker_type="ENV_CONFIG",
            blocker_description="Missing credentials",
            required_values=["API_KEY"],
            status="ACTIVE"
        )
        db_session.add(blocker)
        db_session.commit()

        # Show blockers
        result = cmd_show_blockers(temp_project_dir, verbose=False)

        assert result is True

    def test_cmd_show_dependencies(self, db_session, sample_features, temp_project_dir):
        """Test showing dependencies for a feature."""
        from blockers_cli import cmd_show_dependencies
        from dependency_detector import DependencyDetector

        # First detect dependencies
        detector = DependencyDetector(db_session)
        detector.detect_all_dependencies()

        # Show dependencies for Feature #12 (which depends on #5)
        result = cmd_show_dependencies(temp_project_dir, 12)

        assert result is True


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_skip_feature_with_dependencies_workflow(self, db_session, sample_features):
        """Test complete workflow: skip feature → detect impact → handle blocker."""
        # 1. Detect dependencies
        detector = DependencyDetector(db_session)
        detector.detect_all_dependencies()

        # 2. Analyze impact of skipping Feature #5
        analyzer = SkipImpactAnalyzer(db_session)
        impact = analyzer.analyze_skip_impact(5)

        assert impact['immediate_dependents'] >= 2

        # 3. Classify blocker
        classifier = BlockerClassifier(db_session)
        blocker_type = classifier.classify_blocker_text(
            "Missing OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET"
        )

        assert blocker_type == BlockerType.ENV_CONFIG

        # 4. Create blocker record
        blocker = FeatureBlocker(
            feature_id=5,
            blocker_type=blocker_type.value,
            blocker_description="Missing OAuth credentials",
            required_values=["OAUTH_CLIENT_ID", "OAUTH_CLIENT_SECRET"],
            status="ACTIVE"
        )
        db_session.add(blocker)
        db_session.commit()

        # Verify workflow completed
        assert blocker.id is not None

    def test_implement_with_assumptions_workflow(self, db_session, sample_features):
        """Test complete workflow: implement dependent feature → document assumptions."""
        # 1. Detect that Feature #12 depends on skipped Feature #5
        detector = DependencyDetector(db_session)
        detector.detect_all_dependencies()

        workflow = AssumptionsWorkflow(db_session)
        skipped_deps = workflow.check_for_skipped_dependencies(12)

        assert len(skipped_deps) > 0

        # 2. Get assumption prompt for agent
        prompt = workflow.get_assumption_prompt(12, 5)

        assert "ASSUMPTION" in prompt
        assert "Feature #5" in prompt or "Feature #12" in prompt

        # 3. Create assumption
        assumption = workflow.create_assumption(
            feature_id=12,
            depends_on_feature_id=5,
            assumption_text="OAuth will use Google OAuth provider",
            code_location="src/api/users.js:145",
            impact_description="Avatar URL parsing may need update"
        )

        assert assumption.id is not None

        # 4. Later, when Feature #5 is completed, review assumptions
        assumptions = workflow.get_assumptions_for_review(5)

        assert len(assumptions) > 0
        assert assumptions[0].id == assumption.id

    def test_complete_skip_to_unblock_cycle(self, db_session, sample_features):
        """Test complete cycle: skip → block → provide values → unblock."""
        # 1. Skip feature with ENV_CONFIG blocker
        feature = db_session.query(Feature).filter(Feature.id == 5).first()
        assert feature.was_skipped is True
        assert feature.blocker_type == BlockerType.ENV_CONFIG.value  # "environment_config"

        # 2. Create blocker record
        blocker = FeatureBlocker(
            feature_id=5,
            blocker_type="ENV_CONFIG",
            blocker_description="Missing OAuth credentials",
            required_values=["OAUTH_CLIENT_ID", "OAUTH_CLIENT_SECRET"],
            status="ACTIVE"
        )
        db_session.add(blocker)
        db_session.commit()

        # 3. User provides values (simulated)
        blocker.status = "RESOLVED"
        blocker.resolution_action = "PROVIDED"
        blocker.resolved_at = datetime.utcnow()

        feature.is_blocked = False

        db_session.commit()

        # 4. Verify unblocked
        assert blocker.status == "RESOLVED"
        assert feature.is_blocked is False


def run_tests():
    """Run all tests with pytest."""
    import subprocess
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)
    return result.returncode == 0


if __name__ == "__main__":
    # Run tests if executed directly
    import sys
    sys.exit(0 if run_tests() else 1)
