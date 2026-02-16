"""
Tests for Human Input System
============================

Tests the feature_request_human_input MCP tool and database integration.
"""

import json
import pytest
from pathlib import Path
from sqlalchemy import text

from api.database import create_database, Feature


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory with database."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def db_session(temp_project_dir):
    """Create a database session for testing."""
    engine, SessionLocal = create_database(temp_project_dir)
    session = SessionLocal()

    # Ensure migrations have run
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(features)"))
        columns = [row[1] for row in result.fetchall()]
        assert "needs_human_input" in columns, "Migration not run"
        assert "human_input_request" in columns, "Migration not run"
        assert "human_input_response" in columns, "Migration not run"

    yield session
    session.close()
    engine.dispose()


def test_human_input_columns_exist(db_session):
    """Test that human input columns were added by migration."""
    # Create a test feature
    feature = Feature(
        priority=1,
        category="test",
        name="Test Feature",
        description="Test description",
        steps=["step1", "step2"],
        passes=False,
        in_progress=False,
        needs_human_input=False,
    )
    db_session.add(feature)
    db_session.commit()

    # Verify columns are accessible
    assert feature.needs_human_input is False
    assert feature.human_input_request is None
    assert feature.human_input_response is None


def test_feature_request_human_input(db_session):
    """Test requesting human input for a feature."""
    # Create a feature in progress
    feature = Feature(
        priority=1,
        category="auth",
        name="Implement OAuth",
        description="Add OAuth authentication",
        steps=["Create OAuth client", "Add login flow"],
        passes=False,
        in_progress=True,
        needs_human_input=False,
    )
    db_session.add(feature)
    db_session.commit()
    feature_id = feature.id

    # Simulate requesting human input
    request_data = {
        "prompt": "Need OAuth credentials for Google API",
        "fields": [
            {
                "id": "client_id",
                "label": "OAuth Client ID",
                "type": "text",
                "required": True,
                "placeholder": "Enter your Google OAuth client ID"
            },
            {
                "id": "client_secret",
                "label": "OAuth Client Secret",
                "type": "text",
                "required": True,
                "placeholder": "Enter your Google OAuth client secret"
            },
            {
                "id": "redirect_uri",
                "label": "Redirect URI",
                "type": "text",
                "required": False,
                "placeholder": "http://localhost:3000/auth/callback"
            }
        ]
    }

    # Update feature to request human input
    feature.needs_human_input = True
    feature.in_progress = False
    feature.human_input_request = request_data
    db_session.commit()

    # Verify state
    db_session.refresh(feature)
    assert feature.needs_human_input is True
    assert feature.in_progress is False
    assert feature.human_input_request == request_data
    assert feature.human_input_response is None


def test_respond_to_human_input(db_session):
    """Test responding to a human input request."""
    # Create a feature waiting for input
    request_data = {
        "prompt": "Need API key",
        "fields": [
            {
                "id": "api_key",
                "label": "API Key",
                "type": "text",
                "required": True
            }
        ]
    }

    feature = Feature(
        priority=1,
        category="test",
        name="Test Feature",
        description="Test",
        steps=["step1"],
        passes=False,
        in_progress=False,
        needs_human_input=True,
        human_input_request=request_data,
    )
    db_session.add(feature)
    db_session.commit()
    feature_id = feature.id

    # Provide human response
    response_data = {
        "api_key": "sk-test-key-123456"
    }

    feature.human_input_response = response_data
    feature.needs_human_input = False
    db_session.commit()

    # Verify state
    db_session.refresh(feature)
    assert feature.needs_human_input is False
    assert feature.human_input_response == response_data
    assert feature.in_progress is False  # Ready to be picked up again


def test_feature_to_dict_includes_human_input(db_session):
    """Test that Feature.to_dict() includes human input fields."""
    feature = Feature(
        priority=1,
        category="test",
        name="Test Feature",
        description="Test",
        steps=["step1"],
        passes=False,
        in_progress=False,
        needs_human_input=True,
        human_input_request={"prompt": "test", "fields": []},
        human_input_response={"field1": "value1"},
    )
    db_session.add(feature)
    db_session.commit()

    # Convert to dict
    feature_dict = feature.to_dict()

    # Verify human input fields are included
    assert "needs_human_input" in feature_dict
    assert "human_input_request" in feature_dict
    assert "human_input_response" in feature_dict
    assert feature_dict["needs_human_input"] is True
    assert feature_dict["human_input_request"] == {"prompt": "test", "fields": []}
    assert feature_dict["human_input_response"] == {"field1": "value1"}


def test_multiple_field_types(db_session):
    """Test human input request with multiple field types."""
    request_data = {
        "prompt": "Configure deployment settings",
        "fields": [
            {
                "id": "environment",
                "label": "Environment",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "dev", "label": "Development"},
                    {"value": "staging", "label": "Staging"},
                    {"value": "prod", "label": "Production"}
                ]
            },
            {
                "id": "enable_ssl",
                "label": "Enable SSL",
                "type": "boolean",
                "required": True
            },
            {
                "id": "notes",
                "label": "Additional Notes",
                "type": "textarea",
                "required": False,
                "placeholder": "Any special deployment instructions"
            }
        ]
    }

    feature = Feature(
        priority=1,
        category="deploy",
        name="Deploy Application",
        description="Deploy to production",
        steps=["Configure", "Deploy"],
        passes=False,
        in_progress=True,
        needs_human_input=False,
    )
    db_session.add(feature)
    db_session.commit()

    # Request human input with multiple field types
    feature.needs_human_input = True
    feature.in_progress = False
    feature.human_input_request = request_data
    db_session.commit()

    # Provide response
    response_data = {
        "environment": "prod",
        "enable_ssl": True,
        "notes": "Deploy during maintenance window"
    }

    feature.human_input_response = response_data
    feature.needs_human_input = False
    db_session.commit()

    # Verify
    db_session.refresh(feature)
    assert feature.needs_human_input is False
    assert feature.human_input_response == response_data


def test_query_features_needing_human_input(db_session):
    """Test querying for features that need human input."""
    # Create several features
    features = [
        Feature(
            priority=1,
            category="test",
            name="Feature 1",
            description="Needs input",
            steps=["step1"],
            passes=False,
            in_progress=False,
            needs_human_input=True,
            human_input_request={"prompt": "test", "fields": []},
        ),
        Feature(
            priority=2,
            category="test",
            name="Feature 2",
            description="In progress",
            steps=["step1"],
            passes=False,
            in_progress=True,
            needs_human_input=False,
        ),
        Feature(
            priority=3,
            category="test",
            name="Feature 3",
            description="Needs input",
            steps=["step1"],
            passes=False,
            in_progress=False,
            needs_human_input=True,
            human_input_request={"prompt": "test2", "fields": []},
        ),
    ]

    for f in features:
        db_session.add(f)
    db_session.commit()

    # Query for features needing human input
    needing_input = db_session.query(Feature).filter(
        Feature.needs_human_input == True
    ).order_by(Feature.priority).all()

    # Verify
    assert len(needing_input) == 2
    assert needing_input[0].name == "Feature 1"
    assert needing_input[1].name == "Feature 3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
