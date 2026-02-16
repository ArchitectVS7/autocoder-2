"""
Path Resolution for AutoCoder Runtime Files
===========================================

Central module for resolving paths to autocoder-generated runtime files.
"""

from pathlib import Path


def get_autocoder_dir(project_dir: Path) -> Path:
    """Return the .autocoder directory path and ensure it exists."""
    autocoder_dir = project_dir / ".autocoder"
    autocoder_dir.mkdir(exist_ok=True)
    return autocoder_dir


def get_pause_drain_path(project_dir: Path) -> Path:
    """Return the path to the .pause_drain signal file.

    This file is created to request a graceful pause (drain mode).
    When this file exists, the orchestrator will:
    1. Stop spawning new agents
    2. Wait for running agents to finish
    3. Enter paused state
    4. Resume when file is removed
    """
    return get_autocoder_dir(project_dir) / ".pause_drain"


def get_agent_lock_path(project_dir: Path) -> Path:
    """Return the path to the .agent.lock file."""
    return get_autocoder_dir(project_dir) / ".agent.lock"


def get_progress_cache_path(project_dir: Path) -> Path:
    """Return the path to the .progress_cache file."""
    return get_autocoder_dir(project_dir) / ".progress_cache"
