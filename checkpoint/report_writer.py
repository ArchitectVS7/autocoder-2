"""
Checkpoint Report Writer
========================

Saves checkpoint reports to disk in markdown format and optionally to database.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from checkpoint_orchestrator import AggregatedCheckpointResult, CheckpointDecision, IssueSeverity


class CheckpointReportWriter:
    """Writes checkpoint reports to markdown files and database."""

    def __init__(self, project_dir: Path, db_session: Optional[Session] = None):
        """
        Initialize the checkpoint report writer.

        Args:
            project_dir: Path to project directory
            db_session: Optional database session for storing reports
        """
        self.project_dir = project_dir
        self.checkpoints_dir = project_dir / "checkpoints"
        self.db_session = db_session

        # Ensure checkpoints directory exists
        self.checkpoints_dir.mkdir(exist_ok=True)

    def save_report(
        self,
        result: AggregatedCheckpointResult,
        feature_name: str = ""
    ) -> Path:
        """
        Save checkpoint report to markdown file and optionally database.

        Args:
            result: Aggregated checkpoint result
            feature_name: Optional name of last completed feature

        Returns:
            Path to saved markdown file
        """
        # Generate filename
        filename = self._generate_filename(result)
        filepath = self.checkpoints_dir / filename

        # Generate markdown content
        markdown = self._generate_markdown(result, feature_name)

        # Write to file
        with open(filepath, 'w') as f:
            f.write(markdown)

        # Optionally save to database
        if self.db_session:
            self._save_to_database(result, str(filepath))

        return filepath

    def _generate_filename(self, result: AggregatedCheckpointResult) -> str:
        """
        Generate filename for checkpoint report.

        Format: checkpoint_<number>_<features>_features.md

        Args:
            result: Aggregated checkpoint result

        Returns:
            Filename string
        """
        number_str = str(result.checkpoint_number).zfill(2)
        return f"checkpoint_{number_str}_{result.features_completed}_features.md"

    def _generate_markdown(
        self,
        result: AggregatedCheckpointResult,
        feature_name: str = ""
    ) -> str:
        """
        Generate markdown content for checkpoint report.

        Args:
            result: Aggregated checkpoint result
            feature_name: Optional name of last completed feature

        Returns:
            Markdown string
        """
        lines = []

        # Header
        lines.append(f"# Checkpoint #{result.checkpoint_number}")
        lines.append("")
        lines.append(f"**Date:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Features Completed:** {result.features_completed}")
        if feature_name:
            lines.append(f"**Last Feature:** {feature_name}")
        lines.append(f"**Execution Time:** {result.total_execution_time_ms:.0f}ms")
        lines.append("")

        # Decision
        decision_emoji = {
            CheckpointDecision.PAUSE: "❌",
            CheckpointDecision.CONTINUE: "✅",
            CheckpointDecision.CONTINUE_WITH_WARNINGS: "⚠️"
        }.get(result.decision, "❓")

        lines.append(f"## Decision: {decision_emoji} {result.decision.value}")
        lines.append("")

        # Summary statistics
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Critical Issues:** {result.total_critical}")
        lines.append(f"- **Warnings:** {result.total_warnings}")
        lines.append(f"- **Info Items:** {result.total_info}")
        lines.append(f"- **Checkpoints Run:** {len(result.results)}")
        lines.append("")

        # Detailed results per checkpoint type
        if result.results:
            lines.append("## Checkpoint Results")
            lines.append("")

            for checkpoint_result in result.results:
                # Checkpoint type header
                status_emoji = {
                    "PASS": "✅",
                    "PASS_WITH_WARNINGS": "⚠️",
                    "FAIL": "❌"
                }.get(checkpoint_result.status, "❓")

                lines.append(f"### {status_emoji} {checkpoint_result.checkpoint_type}")
                lines.append("")
                lines.append(f"**Status:** {checkpoint_result.status}")
                lines.append(f"**Execution Time:** {checkpoint_result.execution_time_ms:.0f}ms")
                lines.append("")

                # Issues
                if checkpoint_result.issues:
                    lines.append("#### Issues Found")
                    lines.append("")

                    # Group issues by severity
                    critical_issues = [i for i in checkpoint_result.issues if i.severity == IssueSeverity.CRITICAL]
                    warning_issues = [i for i in checkpoint_result.issues if i.severity == IssueSeverity.WARNING]
                    info_issues = [i for i in checkpoint_result.issues if i.severity == IssueSeverity.INFO]

                    # Critical issues
                    if critical_issues:
                        lines.append("##### 🔴 Critical Issues")
                        lines.append("")
                        for issue in critical_issues:
                            lines.append(f"**{issue.title}**")
                            lines.append("")
                            lines.append(f"{issue.description}")
                            lines.append("")
                            if issue.location:
                                lines.append(f"*Location:* `{issue.location}`")
                                if issue.line_number:
                                    lines.append(f" (Line {issue.line_number})")
                                lines.append("")
                            if issue.suggestion:
                                lines.append(f"*Suggestion:* {issue.suggestion}")
                                lines.append("")
                            lines.append("---")
                            lines.append("")

                    # Warnings
                    if warning_issues:
                        lines.append("##### 🟡 Warnings")
                        lines.append("")
                        for issue in warning_issues:
                            lines.append(f"**{issue.title}**")
                            lines.append("")
                            lines.append(f"{issue.description}")
                            lines.append("")
                            if issue.location:
                                lines.append(f"*Location:* `{issue.location}`")
                                if issue.line_number:
                                    lines.append(f" (Line {issue.line_number})")
                                lines.append("")
                            if issue.suggestion:
                                lines.append(f"*Suggestion:* {issue.suggestion}")
                                lines.append("")
                            lines.append("---")
                            lines.append("")

                    # Info items
                    if info_issues:
                        lines.append("##### 🔵 Informational")
                        lines.append("")
                        for issue in info_issues:
                            lines.append(f"- **{issue.title}**: {issue.description}")
                        lines.append("")

                else:
                    lines.append("*No issues found*")
                    lines.append("")

                # Metadata
                if checkpoint_result.metadata:
                    lines.append("#### Metadata")
                    lines.append("")
                    for key, value in checkpoint_result.metadata.items():
                        lines.append(f"- **{key}:** {value}")
                    lines.append("")

        # Footer with action items if any
        if result.decision == CheckpointDecision.PAUSE:
            lines.append("## ⚠️ Action Required")
            lines.append("")
            lines.append("Development has been **paused** due to critical issues.")
            lines.append("")
            lines.append("**Next Steps:**")
            lines.append("1. Review and fix all critical issues listed above")
            lines.append("2. Re-run the checkpoint to verify fixes")
            lines.append("3. Resume development once all critical issues are resolved")
            lines.append("")
        elif result.decision == CheckpointDecision.CONTINUE_WITH_WARNINGS:
            lines.append("## 💡 Recommendations")
            lines.append("")
            lines.append("Development can continue, but please address warnings when possible.")
            lines.append("")

        # Generated timestamp
        lines.append("---")
        lines.append("")
        lines.append(f"*Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*")

        return "\n".join(lines)

    def _save_to_database(
        self,
        result: AggregatedCheckpointResult,
        filepath: str
    ) -> None:
        """
        Save checkpoint result to database.

        Args:
            result: Aggregated checkpoint result
            filepath: Path where markdown file was saved
        """
        # Import here to avoid circular dependency
        try:
            from api.database import Checkpoint

            checkpoint = Checkpoint(
                checkpoint_number=result.checkpoint_number,
                features_completed=result.features_completed,
                timestamp=result.timestamp,
                decision=result.decision.value,
                total_critical=result.total_critical,
                total_warnings=result.total_warnings,
                total_info=result.total_info,
                execution_time_ms=result.total_execution_time_ms,
                report_filepath=filepath,
                result_json=result.to_dict()
            )

            self.db_session.add(checkpoint)
            self.db_session.commit()

        except ImportError:
            # Checkpoint table not yet added to database schema
            pass
        except Exception as e:
            # Log error but don't fail if database save fails
            print(f"Warning: Could not save checkpoint to database: {e}")

    def get_latest_checkpoint_path(self) -> Optional[Path]:
        """
        Get path to the most recent checkpoint report.

        Returns:
            Path to latest checkpoint markdown file, or None if no checkpoints exist
        """
        checkpoints = list(self.checkpoints_dir.glob("checkpoint_*.md"))
        if not checkpoints:
            return None

        # Sort by modification time (most recent first)
        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return checkpoints[0]

    def list_checkpoints(self) -> list[Path]:
        """
        List all checkpoint reports, sorted by checkpoint number.

        Returns:
            List of paths to checkpoint markdown files
        """
        checkpoints = list(self.checkpoints_dir.glob("checkpoint_*.md"))

        # Sort by filename (which includes checkpoint number)
        checkpoints.sort()

        return checkpoints

    def read_checkpoint(self, checkpoint_number: int) -> Optional[str]:
        """
        Read a specific checkpoint report.

        Args:
            checkpoint_number: Checkpoint number to read

        Returns:
            Markdown content of checkpoint, or None if not found
        """
        # Find checkpoint file with this number
        pattern = f"checkpoint_{str(checkpoint_number).zfill(2)}_*.md"
        matches = list(self.checkpoints_dir.glob(pattern))

        if not matches:
            return None

        # Read first match
        with open(matches[0], 'r') as f:
            return f.read()
