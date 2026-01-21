"""
Database Models and Connection
==============================

SQLite database schema for feature storage using SQLAlchemy.
"""

import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String, Text, Float, DateTime, ForeignKey, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, relationship
from sqlalchemy.types import JSON
from datetime import datetime

Base = declarative_base()


class Feature(Base):
    """Feature model representing a test case/feature to implement."""

    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    priority = Column(Integer, nullable=False, default=999, index=True)
    category = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    steps = Column(JSON, nullable=False)  # Stored as JSON array
    passes = Column(Boolean, nullable=False, default=False, index=True)
    in_progress = Column(Boolean, nullable=False, default=False, index=True)
    # Dependencies: list of feature IDs that must be completed before this feature
    # NULL/empty = no dependencies (backwards compatible)
    dependencies = Column(JSON, nullable=True, default=None)

    # Phase 1: Skip Management fields
    was_skipped = Column(Boolean, default=False, index=True)
    skip_count = Column(Integer, default=0)
    blocker_type = Column(String(50), nullable=True)  # ENV_CONFIG, EXTERNAL_SERVICE, etc.
    blocker_description = Column(Text, nullable=True)
    is_blocked = Column(Boolean, default=False, index=True)
    passing_with_mocks = Column(Boolean, default=False)

    # Relationships
    dependencies = relationship("FeatureDependency", foreign_keys="FeatureDependency.feature_id", back_populates="feature")
    dependent_features = relationship("FeatureDependency", foreign_keys="FeatureDependency.depends_on_feature_id", back_populates="depends_on")
    assumptions = relationship("FeatureAssumption", foreign_keys="FeatureAssumption.feature_id", back_populates="feature")
    blockers = relationship("FeatureBlocker", back_populates="feature")

    def to_dict(self) -> dict:
        """Convert feature to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "priority": self.priority,
            "category": self.category,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            # Handle legacy NULL values gracefully - treat as False
            "passes": self.passes if self.passes is not None else False,
            "in_progress": self.in_progress if self.in_progress is not None else False,
            # Dependencies: NULL/empty treated as empty list for backwards compat
            "dependencies": self.dependencies if self.dependencies else [],
            # Phase 1: Skip Management fields
            "was_skipped": self.was_skipped,
            "skip_count": self.skip_count,
            "blocker_type": self.blocker_type,
            "blocker_description": self.blocker_description,
            "is_blocked": self.is_blocked,
            "passing_with_mocks": self.passing_with_mocks,
        }


class FeatureDependency(Base):
    """Tracks dependencies between features."""

    __tablename__ = "feature_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False, index=True)
    depends_on_feature_id = Column(Integer, ForeignKey("features.id"), nullable=False, index=True)
    confidence = Column(Float, default=1.0)  # 0.0-1.0 confidence score
    detected_method = Column(String(50), nullable=False)  # 'explicit_id', 'keyword', 'category'
    detected_keywords = Column(JSON, nullable=True)  # Keywords that triggered detection
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    feature = relationship("Feature", foreign_keys=[feature_id], back_populates="dependencies")
    depends_on = relationship("Feature", foreign_keys=[depends_on_feature_id], back_populates="dependent_features")

    def to_dict(self) -> dict:
        """Convert dependency to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "feature_id": self.feature_id,
            "depends_on_feature_id": self.depends_on_feature_id,
            "confidence": self.confidence,
            "detected_method": self.detected_method,
            "detected_keywords": self.detected_keywords,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FeatureAssumption(Base):
    """Tracks assumptions made when implementing features with dependencies on skipped features."""

    __tablename__ = "feature_assumptions"

    id = Column(Integer, primary_key=True, index=True)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False, index=True)
    depends_on_feature_id = Column(Integer, ForeignKey("features.id"), nullable=True, index=True)
    assumption_text = Column(Text, nullable=False)
    code_location = Column(String(500), nullable=True)  # File path and line numbers
    impact_description = Column(Text, nullable=True)  # What happens if assumption is wrong
    status = Column(String(50), default="ACTIVE")  # ACTIVE, VALIDATED, INVALID, NEEDS_REVIEW
    created_at = Column(DateTime, default=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)

    # Relationships
    feature = relationship("Feature", foreign_keys=[feature_id], back_populates="assumptions")

    def to_dict(self) -> dict:
        """Convert assumption to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "feature_id": self.feature_id,
            "depends_on_feature_id": self.depends_on_feature_id,
            "assumption_text": self.assumption_text,
            "code_location": self.code_location,
            "impact_description": self.impact_description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
        }


class FeatureBlocker(Base):
    """Tracks blockers that prevent feature implementation."""

    __tablename__ = "feature_blockers"

    id = Column(Integer, primary_key=True, index=True)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False, index=True)
    blocker_type = Column(String(50), nullable=False)  # ENV_CONFIG, EXTERNAL_SERVICE, etc.
    blocker_description = Column(Text, nullable=False)
    required_action = Column(Text, nullable=True)  # What user needs to do
    required_values = Column(JSON, nullable=True)  # List of env vars or config needed
    status = Column(String(50), default="ACTIVE", index=True)  # ACTIVE, RESOLVED, DEFERRED
    resolution_action = Column(String(50), nullable=True)  # PROVIDED, DEFERRED, MOCKED
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    feature = relationship("Feature", back_populates="blockers")

    def to_dict(self) -> dict:
        """Convert blocker to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "feature_id": self.feature_id,
            "blocker_type": self.blocker_type,
            "blocker_description": self.blocker_description,
            "required_action": self.required_action,
            "required_values": self.required_values,
            "status": self.status,
            "resolution_action": self.resolution_action,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    def get_dependencies_safe(self) -> list[int]:
        """Safely extract dependencies, handling NULL and malformed data."""
        if self.dependencies is None:
            return []
        if isinstance(self.dependencies, list):
            return [d for d in self.dependencies if isinstance(d, int)]
        return []


class Checkpoint(Base):
    """Stores checkpoint execution results for historical tracking and analysis."""

    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    checkpoint_number = Column(Integer, nullable=False, index=True)
    features_completed = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    decision = Column(String(50), nullable=False)  # PAUSE, CONTINUE, CONTINUE_WITH_WARNINGS
    total_critical = Column(Integer, default=0)
    total_warnings = Column(Integer, default=0)
    total_info = Column(Integer, default=0)
    execution_time_ms = Column(Float, default=0.0)
    report_filepath = Column(String(500), nullable=True)  # Path to markdown report
    result_json = Column(JSON, nullable=True)  # Full result object as JSON

    def to_dict(self) -> dict:
        """Convert checkpoint to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "checkpoint_number": self.checkpoint_number,
            "features_completed": self.features_completed,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "decision": self.decision,
            "total_critical": self.total_critical,
            "total_warnings": self.total_warnings,
            "total_info": self.total_info,
            "execution_time_ms": self.execution_time_ms,
            "report_filepath": self.report_filepath,
            "result_json": self.result_json,
        }


def get_database_path(project_dir: Path) -> Path:
    """Return the path to the SQLite database for a project."""
    return project_dir / "features.db"


def get_database_url(project_dir: Path) -> str:
    """Return the SQLAlchemy database URL for a project.

    Uses POSIX-style paths (forward slashes) for cross-platform compatibility.
    """
    db_path = get_database_path(project_dir)
    return f"sqlite:///{db_path.as_posix()}"


def _migrate_add_in_progress_column(engine) -> None:
    """Add in_progress column to existing databases that don't have it."""
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("PRAGMA table_info(features)"))
        columns = [row[1] for row in result.fetchall()]

        if "in_progress" not in columns:
            # Add the column with default value
            conn.execute(text("ALTER TABLE features ADD COLUMN in_progress BOOLEAN DEFAULT 0"))
            conn.commit()


def _migrate_fix_null_boolean_fields(engine) -> None:
    """Fix NULL values in passes and in_progress columns."""
    with engine.connect() as conn:
        # Fix NULL passes values
        conn.execute(text("UPDATE features SET passes = 0 WHERE passes IS NULL"))
        # Fix NULL in_progress values
        conn.execute(text("UPDATE features SET in_progress = 0 WHERE in_progress IS NULL"))
        conn.commit()


def _migrate_add_dependencies_column(engine) -> None:
    """Add dependencies column to existing databases that don't have it.

    Uses NULL default for backwards compatibility - existing features
    without dependencies will have NULL which is treated as empty list.
    """
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("PRAGMA table_info(features)"))
        columns = [row[1] for row in result.fetchall()]

        if "dependencies" not in columns:
            # Use TEXT for SQLite JSON storage, NULL default for backwards compat
            conn.execute(text("ALTER TABLE features ADD COLUMN dependencies TEXT DEFAULT NULL"))
            conn.commit()


def _is_network_path(path: Path) -> bool:
    """Detect if path is on a network filesystem.

    WAL mode doesn't work reliably on network filesystems (NFS, SMB, CIFS)
    and can cause database corruption. This function detects common network
    path patterns so we can fall back to DELETE mode.

    Args:
        path: The path to check

    Returns:
        True if the path appears to be on a network filesystem
    """
    path_str = str(path.resolve())

    if sys.platform == "win32":
        # Windows UNC paths: \\server\share or \\?\UNC\server\share
        if path_str.startswith("\\\\"):
            return True
        # Mapped network drives - check if the drive is a network drive
        try:
            import ctypes
            drive = path_str[:2]  # e.g., "Z:"
            if len(drive) == 2 and drive[1] == ":":
                # DRIVE_REMOTE = 4
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive + "\\")
                if drive_type == 4:  # DRIVE_REMOTE
                    return True
        except (AttributeError, OSError):
            pass
    else:
        # Unix: Check mount type via /proc/mounts or mount command
        try:
            with open("/proc/mounts", "r") as f:
                mounts = f.read()
                # Check each mount point to find which one contains our path
                for line in mounts.splitlines():
                    parts = line.split()
                    if len(parts) >= 3:
                        mount_point = parts[1]
                        fs_type = parts[2]
                        # Check if path is under this mount point and if it's a network FS
                        if path_str.startswith(mount_point):
                            if fs_type in ("nfs", "nfs4", "cifs", "smbfs", "fuse.sshfs"):
                                return True
        except (FileNotFoundError, PermissionError):
            pass

    return False


def _migrate_add_phase1_columns(engine) -> None:
    """Add Phase 1 skip management columns to existing databases."""
    from sqlalchemy import text

    with engine.connect() as conn:
        # Check which columns exist
        result = conn.execute(text("PRAGMA table_info(features)"))
        columns = [row[1] for row in result.fetchall()]

        # Add new columns if they don't exist
        new_columns = [
            ("was_skipped", "BOOLEAN DEFAULT 0"),
            ("skip_count", "INTEGER DEFAULT 0"),
            ("blocker_type", "VARCHAR(50)"),
            ("blocker_description", "TEXT"),
            ("is_blocked", "BOOLEAN DEFAULT 0"),
            ("passing_with_mocks", "BOOLEAN DEFAULT 0"),
        ]

        for column_name, column_type in new_columns:
            if column_name not in columns:
                conn.execute(text(f"ALTER TABLE features ADD COLUMN {column_name} {column_type}"))

        conn.commit()


def create_database(project_dir: Path) -> tuple:
    """
    Create database and return engine + session maker.

    Args:
        project_dir: Directory containing the project

    Returns:
        Tuple of (engine, SessionLocal)
    """
    db_url = get_database_url(project_dir)
    engine = create_engine(db_url, connect_args={
        "check_same_thread": False,
        "timeout": 30  # Wait up to 30s for locks
    })
    Base.metadata.create_all(bind=engine)

    # Choose journal mode based on filesystem type
    # WAL mode doesn't work reliably on network filesystems and can cause corruption
    is_network = _is_network_path(project_dir)
    journal_mode = "DELETE" if is_network else "WAL"

    with engine.connect() as conn:
        conn.execute(text(f"PRAGMA journal_mode={journal_mode}"))
        conn.execute(text("PRAGMA busy_timeout=30000"))
        conn.commit()

    # Migrate existing databases
    _migrate_add_in_progress_column(engine)
    _migrate_fix_null_boolean_fields(engine)
    _migrate_add_dependencies_column(engine)

    # Migrate existing databases to add Phase 1 columns
    _migrate_add_phase1_columns(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


# Global session maker - will be set when server starts
_session_maker: Optional[sessionmaker] = None


def set_session_maker(session_maker: sessionmaker) -> None:
    """Set the global session maker."""
    global _session_maker
    _session_maker = session_maker


def get_db() -> Session:
    """
    Dependency for FastAPI to get database session.

    Yields a database session and ensures it's closed after use.
    """
    if _session_maker is None:
        raise RuntimeError("Database not initialized. Call set_session_maker first.")

    db = _session_maker()
    try:
        yield db
    finally:
        db.close()
