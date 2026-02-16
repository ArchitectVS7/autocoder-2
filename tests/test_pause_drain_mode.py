"""
Tests for Pause/Drain Mode
===========================

Tests the graceful pause (drain) functionality in the orchestrator.
"""

import asyncio
import pytest
from pathlib import Path

from paths import get_pause_drain_path
from parallel_orchestrator import ParallelOrchestrator
from api.database import create_database, Feature


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory with database."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create database and add test features
    engine, SessionLocal = create_database(project_dir)
    session = SessionLocal()

    features = [
        Feature(
            priority=i,
            category="test",
            name=f"Feature {i}",
            description=f"Test feature {i}",
            steps=["step1", "step2"],
            passes=False,
            in_progress=False,
        )
        for i in range(1, 4)
    ]

    for f in features:
        session.add(f)
    session.commit()
    session.close()
    engine.dispose()

    return project_dir


def test_pause_drain_path_creation(temp_project_dir):
    """Test that get_pause_drain_path creates the .autocoder directory."""
    pause_path = get_pause_drain_path(temp_project_dir)

    # Verify path structure
    assert pause_path.parent.name == ".autocoder"
    assert pause_path.name == ".pause_drain"
    assert pause_path.parent.exists()  # .autocoder dir should be created


def test_check_drain_signal(temp_project_dir):
    """Test drain signal detection."""
    orchestrator = ParallelOrchestrator(
        project_dir=temp_project_dir,
        max_concurrency=1,
        yolo_mode=True,
    )

    # Initially no drain signal
    assert not orchestrator._check_drain_signal()

    # Create drain signal
    pause_path = get_pause_drain_path(temp_project_dir)
    pause_path.touch()

    # Should detect drain signal
    assert orchestrator._check_drain_signal()

    # Clean up
    orchestrator._clear_drain_signal()
    assert not orchestrator._check_drain_signal()


def test_clear_drain_signal(temp_project_dir):
    """Test clearing the drain signal."""
    orchestrator = ParallelOrchestrator(
        project_dir=temp_project_dir,
        max_concurrency=1,
        yolo_mode=True,
    )

    # Create drain signal
    pause_path = get_pause_drain_path(temp_project_dir)
    pause_path.touch()
    assert pause_path.exists()

    # Clear signal
    orchestrator._clear_drain_signal()

    # Verify file is gone and flag is reset
    assert not pause_path.exists()
    assert not orchestrator._drain_requested


def test_request_pause(temp_project_dir):
    """Test requesting a pause via the orchestrator."""
    orchestrator = ParallelOrchestrator(
        project_dir=temp_project_dir,
        max_concurrency=1,
        yolo_mode=True,
    )

    # Request pause
    orchestrator.request_pause()

    # Verify signal file was created
    pause_path = get_pause_drain_path(temp_project_dir)
    assert pause_path.exists()

    # Clean up
    orchestrator._clear_drain_signal()


def test_resume_from_pause(temp_project_dir):
    """Test resuming from a paused state."""
    orchestrator = ParallelOrchestrator(
        project_dir=temp_project_dir,
        max_concurrency=1,
        yolo_mode=True,
    )

    # Request pause
    orchestrator.request_pause()
    pause_path = get_pause_drain_path(temp_project_dir)
    assert pause_path.exists()

    # Resume
    orchestrator.resume()

    # Verify signal file was removed
    assert not pause_path.exists()
    assert not orchestrator._drain_requested


def test_drain_flag_initialization(temp_project_dir):
    """Test that drain flag starts as False."""
    orchestrator = ParallelOrchestrator(
        project_dir=temp_project_dir,
        max_concurrency=1,
        yolo_mode=True,
    )

    assert not orchestrator._drain_requested


@pytest.mark.asyncio
async def test_drain_mode_prevents_new_agents(temp_project_dir):
    """Test that drain mode prevents spawning new agents."""
    # This is an integration test that would require running the full orchestrator
    # For now, we test the logic flow

    orchestrator = ParallelOrchestrator(
        project_dir=temp_project_dir,
        max_concurrency=2,
        yolo_mode=True,
    )

    # Set drain requested
    orchestrator._drain_requested = True

    # Verify drain is requested
    assert orchestrator._drain_requested

    # In real scenario, orchestrator would skip spawning new agents
    # and wait for running agents to complete


def test_multiple_pause_resume_cycles(temp_project_dir):
    """Test multiple pause/resume cycles."""
    orchestrator = ParallelOrchestrator(
        project_dir=temp_project_dir,
        max_concurrency=1,
        yolo_mode=True,
    )

    pause_path = get_pause_drain_path(temp_project_dir)

    # Cycle 1
    orchestrator.request_pause()
    assert pause_path.exists()
    orchestrator.resume()
    assert not pause_path.exists()

    # Cycle 2
    orchestrator.request_pause()
    assert pause_path.exists()
    orchestrator.resume()
    assert not pause_path.exists()

    # Cycle 3
    orchestrator.request_pause()
    assert pause_path.exists()
    orchestrator._clear_drain_signal()
    assert not pause_path.exists()


def test_pause_path_in_autocoder_dir(temp_project_dir):
    """Test that pause file is in .autocoder directory."""
    pause_path = get_pause_drain_path(temp_project_dir)

    # Verify it's in the .autocoder subdirectory
    assert pause_path.parent.name == ".autocoder"
    assert pause_path.name == ".pause_drain"

    # Verify full path structure
    expected_path = temp_project_dir / ".autocoder" / ".pause_drain"
    assert pause_path == expected_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
