#!/usr/bin/env python3
"""
Metrics Collection System
=========================

Collects performance metrics during agent execution for benchmarking and analysis.

Metrics tracked:
- Time to MVP (hours from spec to working prototype)
- Feature completion rate (% passing on first try)
- Rework ratio (features needing fixes / total)
- Skip rate (% features skipped at least once)
- Human interventions (# times user input required)
- Code quality score (static analysis + linting)
- Cost (API calls and estimated cost)
- Lines of code generated
- Test coverage
- Velocity (features per hour)
"""

from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, relationship
import json

Base = declarative_base()


class MetricsRun(Base):
    """Represents a complete project run from start to finish."""

    __tablename__ = "metrics_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    total_features = Column(Integer, default=0)
    features_completed = Column(Integer, default=0)
    run_status = Column(String(50), default="in_progress")  # in_progress, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("MetricsSession", back_populates="run", cascade="all, delete-orphan")
    features = relationship("MetricsFeature", back_populates="run", cascade="all, delete-orphan")
    interventions = relationship("MetricsIntervention", back_populates="run", cascade="all, delete-orphan")

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "project_name": self.project_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_features": self.total_features,
            "features_completed": self.features_completed,
            "run_status": self.run_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MetricsSession(Base):
    """Represents a single agent session within a run."""

    __tablename__ = "metrics_sessions"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("metrics_runs.id"), nullable=False, index=True)
    session_number = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    features_completed = Column(Integer, default=0)
    features_skipped = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)
    api_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    run = relationship("MetricsRun", back_populates="sessions")

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "session_number": self.session_number,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "features_completed": self.features_completed,
            "features_skipped": self.features_skipped,
            "api_calls": self.api_calls,
            "api_cost": self.api_cost,
        }


class MetricsFeature(Base):
    """Tracks metrics for individual feature completion."""

    __tablename__ = "metrics_features"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("metrics_runs.id"), nullable=False, index=True)
    feature_id = Column(Integer, nullable=False, index=True)
    feature_name = Column(String(255), nullable=False)
    first_try_pass = Column(Boolean, default=False)
    attempts_needed = Column(Integer, default=1)
    was_skipped = Column(Boolean, default=False)
    time_to_complete_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    run = relationship("MetricsRun", back_populates="features")

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "feature_id": self.feature_id,
            "feature_name": self.feature_name,
            "first_try_pass": self.first_try_pass,
            "attempts_needed": self.attempts_needed,
            "was_skipped": self.was_skipped,
            "time_to_complete_seconds": self.time_to_complete_seconds,
        }


class MetricsIntervention(Base):
    """Tracks human interventions during the run."""

    __tablename__ = "metrics_interventions"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("metrics_runs.id"), nullable=False, index=True)
    intervention_type = Column(String(50), nullable=False)  # blocker, clarification, error
    description = Column(Text, nullable=False)
    resolution_time_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    run = relationship("MetricsRun", back_populates="interventions")

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "intervention_type": self.intervention_type,
            "description": self.description,
            "resolution_time_seconds": self.resolution_time_seconds,
        }


class MetricsCollector:
    """Collects and stores performance metrics during agent execution."""

    def __init__(self, project_dir: Path, project_name: str):
        """Initialize metrics collector.

        Args:
            project_dir: Path to the project directory
            project_name: Name of the project
        """
        self.project_dir = Path(project_dir)
        self.project_name = project_name

        # Create benchmarks directory
        self.benchmarks_dir = self.project_dir / "benchmarks"
        self.benchmarks_dir.mkdir(exist_ok=True)

        # Create database
        db_path = self.benchmarks_dir / "metrics.db"
        self.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db: Session = SessionLocal()

        # Create new run
        self.run = self._create_run(project_name)
        self.current_session: Optional[MetricsSession] = None
        self.session_start_time: Optional[datetime] = None
        self.feature_start_times: Dict[int, datetime] = {}

    def _create_run(self, project_name: str) -> MetricsRun:
        """Create a new metrics run.

        Args:
            project_name: Name of the project

        Returns:
            Created MetricsRun object
        """
        run = MetricsRun(
            project_name=project_name,
            start_time=datetime.utcnow(),
            run_status="in_progress"
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def set_total_features(self, total: int) -> None:
        """Set the total number of features for this run.

        Args:
            total: Total number of features
        """
        self.run.total_features = total
        self.db.commit()

    def start_session(self, session_number: int) -> None:
        """Start tracking a new session.

        Args:
            session_number: Session number (1-indexed)
        """
        self.session_start_time = datetime.utcnow()
        self.current_session = MetricsSession(
            run_id=self.run.id,
            session_number=session_number,
            start_time=self.session_start_time
        )
        self.db.add(self.current_session)
        self.db.commit()
        self.db.refresh(self.current_session)

    def end_session(self) -> None:
        """End the current session."""
        if self.current_session:
            self.current_session.end_time = datetime.utcnow()
            self.db.commit()

    def start_feature(self, feature_id: int) -> None:
        """Mark the start time for a feature.

        Args:
            feature_id: ID of the feature being started
        """
        self.feature_start_times[feature_id] = datetime.utcnow()

    def track_feature_complete(
        self,
        feature_id: int,
        feature_name: str,
        first_try: bool,
        attempts: int = 1,
        was_skipped: bool = False
    ) -> None:
        """Track feature completion.

        Args:
            feature_id: ID of the feature
            feature_name: Name of the feature
            first_try: Whether it passed on first try
            attempts: Number of attempts needed
            was_skipped: Whether feature was skipped at some point
        """
        # Calculate time to complete
        time_to_complete = None
        if feature_id in self.feature_start_times:
            delta = datetime.utcnow() - self.feature_start_times[feature_id]
            time_to_complete = int(delta.total_seconds())
            del self.feature_start_times[feature_id]

        # Create feature record
        feature = MetricsFeature(
            run_id=self.run.id,
            feature_id=feature_id,
            feature_name=feature_name,
            first_try_pass=first_try,
            attempts_needed=attempts,
            was_skipped=was_skipped,
            time_to_complete_seconds=time_to_complete
        )
        self.db.add(feature)

        # Update run and session counts
        self.run.features_completed += 1
        if self.current_session:
            self.current_session.features_completed += 1

        self.db.commit()

    def track_feature_skip(self, feature_id: int, feature_name: str) -> None:
        """Track feature skip.

        Args:
            feature_id: ID of the feature
            feature_name: Name of the feature
        """
        if self.current_session:
            self.current_session.features_skipped += 1
            self.db.commit()

    def track_api_call(self, cost: float) -> None:
        """Track API call and cost.

        Args:
            cost: Estimated cost of the API call
        """
        if self.current_session:
            self.current_session.api_calls += 1
            self.current_session.api_cost += cost
            self.db.commit()

    def track_intervention(
        self,
        intervention_type: str,
        description: str,
        resolution_time_seconds: Optional[int] = None
    ) -> None:
        """Track human intervention.

        Args:
            intervention_type: Type of intervention (blocker, clarification, error)
            description: Description of the intervention
            resolution_time_seconds: Time to resolve in seconds
        """
        intervention = MetricsIntervention(
            run_id=self.run.id,
            intervention_type=intervention_type,
            description=description,
            resolution_time_seconds=resolution_time_seconds
        )
        self.db.add(intervention)
        self.db.commit()

    def complete_run(self, status: str = "completed") -> None:
        """Mark the run as complete.

        Args:
            status: Final status (completed, failed)
        """
        self.run.end_time = datetime.utcnow()
        self.run.run_status = status
        self.db.commit()

        # Export to JSON for easy analysis
        self._export_to_json()

    def _export_to_json(self) -> None:
        """Export run data to JSON file."""
        export_data = {
            "run": self.run.to_dict(),
            "sessions": [s.to_dict() for s in self.run.sessions],
            "features": [f.to_dict() for f in self.run.features],
            "interventions": [i.to_dict() for i in self.run.interventions],
        }

        # Create filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_run_{self.run.id}_{timestamp}.json"
        filepath = self.benchmarks_dir / filename

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

    def get_runtime(self) -> timedelta:
        """Get total runtime so far.

        Returns:
            Runtime as timedelta
        """
        if self.run.end_time:
            return self.run.end_time - self.run.start_time
        else:
            return datetime.utcnow() - self.run.start_time

    def get_velocity(self) -> float:
        """Calculate current velocity (features per hour).

        Returns:
            Features per hour
        """
        runtime_hours = self.get_runtime().total_seconds() / 3600
        if runtime_hours == 0:
            return 0.0
        return self.run.features_completed / runtime_hours

    def get_first_try_rate(self) -> float:
        """Calculate first-try success rate.

        Returns:
            Percentage of features passing on first try
        """
        features = self.db.query(MetricsFeature).filter(
            MetricsFeature.run_id == self.run.id
        ).all()

        if not features:
            return 0.0

        first_try_count = sum(1 for f in features if f.first_try_pass)
        return (first_try_count / len(features)) * 100

    def get_skip_rate(self) -> float:
        """Calculate skip rate.

        Returns:
            Percentage of features that were skipped
        """
        features = self.db.query(MetricsFeature).filter(
            MetricsFeature.run_id == self.run.id
        ).all()

        if not features:
            return 0.0

        skipped_count = sum(1 for f in features if f.was_skipped)
        return (skipped_count / len(features)) * 100

    def get_total_cost(self) -> float:
        """Calculate total API cost.

        Returns:
            Total cost in dollars
        """
        sessions = self.db.query(MetricsSession).filter(
            MetricsSession.run_id == self.run.id
        ).all()

        return sum(s.api_cost for s in sessions)

    def get_intervention_count(self) -> int:
        """Get total number of interventions.

        Returns:
            Number of interventions
        """
        return self.db.query(MetricsIntervention).filter(
            MetricsIntervention.run_id == self.run.id
        ).count()

    def close(self) -> None:
        """Close database connection."""
        self.db.close()


def estimate_api_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate API cost based on token usage.

    Args:
        model: Model name (e.g., "claude-sonnet-4-5")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in dollars
    """
    # Pricing as of January 2025 (placeholder values)
    pricing = {
        "claude-sonnet-4-5": {"input": 0.003, "output": 0.015},  # per 1K tokens
        "claude-opus-4-5": {"input": 0.015, "output": 0.075},
        "claude-haiku-4-0": {"input": 0.00025, "output": 0.00125},
    }

    # Default to Sonnet if model not found
    rates = pricing.get(model, pricing["claude-sonnet-4-5"])

    input_cost = (input_tokens / 1000) * rates["input"]
    output_cost = (output_tokens / 1000) * rates["output"]

    return input_cost + output_cost


if __name__ == "__main__":
    # Example usage
    from pathlib import Path

    project_dir = Path("test_project")
    project_dir.mkdir(exist_ok=True)

    collector = MetricsCollector(project_dir, "Test Project")
    collector.set_total_features(10)

    # Simulate session
    collector.start_session(1)

    # Simulate features
    for i in range(5):
        collector.start_feature(i)
        collector.track_feature_complete(
            feature_id=i,
            feature_name=f"Feature {i}",
            first_try=(i % 2 == 0),
            attempts=1 if i % 2 == 0 else 2
        )
        collector.track_api_call(0.05)

    collector.end_session()
    collector.complete_run()

    print(f"Runtime: {collector.get_runtime()}")
    print(f"Velocity: {collector.get_velocity():.1f} features/hour")
    print(f"First-try rate: {collector.get_first_try_rate():.1f}%")
    print(f"Total cost: ${collector.get_total_cost():.2f}")

    collector.close()
