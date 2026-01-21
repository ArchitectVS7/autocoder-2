#!/usr/bin/env python3
"""
Real-Time Performance Dashboard
================================

Live CLI dashboard showing autocoder performance metrics during execution.

Features:
- Real-time updates (1 second refresh)
- Runtime and ETA calculation
- Velocity tracking
- Cost tracking
- Quality metrics
- Efficiency metrics
"""

import time
from datetime import timedelta
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from metrics_collector import MetricsCollector


class PerformanceDashboard:
    """Real-time performance dashboard for autocoder execution."""

    def __init__(self, metrics_collector: MetricsCollector, target_quality: int = 85, target_coverage: int = 80):
        """Initialize dashboard.

        Args:
            metrics_collector: Metrics collector instance
            target_quality: Target code quality score (default: 85/100)
            target_coverage: Target test coverage percentage (default: 80%)
        """
        self.metrics = metrics_collector
        self.console = Console()
        self.target_quality = target_quality
        self.target_coverage = target_coverage

        # Quality metrics (updated externally)
        self.code_quality_score: Optional[int] = None
        self.test_coverage: Optional[float] = None
        self.accessibility_score: Optional[str] = None

    def _format_duration(self, delta: timedelta) -> str:
        """Format timedelta as human-readable string.

        Args:
            delta: Time duration

        Returns:
            Formatted string (e.g., "3h 24m")
        """
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def _calculate_eta(self, completed: int, total: int, velocity: float) -> str:
        """Calculate estimated time to completion.

        Args:
            completed: Features completed so far
            total: Total features
            velocity: Current velocity (features/hour)

        Returns:
            ETA string (e.g., "16h remaining")
        """
        if velocity == 0 or completed >= total:
            return "N/A"

        remaining_features = total - completed
        hours_remaining = remaining_features / velocity

        delta = timedelta(hours=hours_remaining)
        return f"{self._format_duration(delta)} remaining"

    def _get_status_icon(self, value: float, target: float, higher_is_better: bool = True) -> str:
        """Get status icon based on value vs target.

        Args:
            value: Current value
            target: Target value
            higher_is_better: Whether higher values are better

        Returns:
            Status icon (✓, ⚠️, or ✗)
        """
        if higher_is_better:
            if value >= target:
                return "✓"
            elif value >= target * 0.9:
                return "⚠️"
            else:
                return "✗"
        else:
            if value <= target:
                return "✓"
            elif value <= target * 1.1:
                return "⚠️"
            else:
                return "✗"

    def render(self) -> Table:
        """Render dashboard as rich table.

        Returns:
            Rich Table object
        """
        # Get current metrics
        runtime = self.metrics.get_runtime()
        completed = self.metrics.run.features_completed
        total = self.metrics.run.total_features
        velocity = self.metrics.get_velocity()
        first_try_rate = self.metrics.get_first_try_rate()
        skip_rate = self.metrics.get_skip_rate()
        total_cost = self.metrics.get_total_cost()
        intervention_count = self.metrics.get_intervention_count()

        # Calculate percentages
        pct_complete = (completed / total * 100) if total > 0 else 0
        needed_fixes = 100 - first_try_rate if completed > 0 else 0

        # Create main table
        table = Table(
            title="[bold cyan]AUTOCODER PERFORMANCE[/bold cyan]",
            show_header=False,
            border_style="cyan",
            padding=(0, 1)
        )

        # Runtime stats
        table.add_row("[bold]Runtime:[/bold]", self._format_duration(runtime))
        table.add_row(
            "[bold]Features completed:[/bold]",
            f"{completed}/{total} ([cyan]{pct_complete:.0f}%[/cyan])"
        )

        # Velocity and ETA
        eta = self._calculate_eta(completed, total, velocity)
        table.add_row("[bold]Velocity:[/bold]", f"{velocity:.1f} features/hour")
        table.add_row("[bold]Estimated completion:[/bold]", eta)

        # Separator
        table.add_row("", "")

        # Efficiency metrics
        table.add_row("[bold yellow]Efficiency:[/bold yellow]", "")

        first_try_icon = self._get_status_icon(first_try_rate, 60)
        table.add_row(
            "  Pass on first try:",
            f"{completed - int(completed * needed_fixes / 100)}/{completed} "
            f"([cyan]{first_try_rate:.0f}%[/cyan]) {first_try_icon}"
        )

        table.add_row(
            "  Needed fixes:",
            f"{int(completed * needed_fixes / 100)}/{completed} ([cyan]{needed_fixes:.0f}%[/cyan])"
        )

        skip_icon = self._get_status_icon(skip_rate, 30, higher_is_better=False)
        table.add_row(
            "  Skipped features:",
            f"{int(total * skip_rate / 100)}/{total} ([cyan]{skip_rate:.0f}%[/cyan]) {skip_icon}"
        )

        # Separator
        table.add_row("", "")

        # Cost tracking
        table.add_row("[bold yellow]Cost tracking:[/bold yellow]", "")

        sessions = len(self.metrics.run.sessions) if self.metrics.run.sessions else 0
        api_calls = sum(s.api_calls for s in self.metrics.run.sessions) if self.metrics.run.sessions else 0
        cost_per_feature = total_cost / completed if completed > 0 else 0

        table.add_row("  API calls:", f"{api_calls:,}")
        table.add_row("  Estimated cost:", f"[cyan]${total_cost:.2f}[/cyan]")
        table.add_row("  Cost per feature:", f"${cost_per_feature:.2f}")
        table.add_row("  Sessions:", f"{sessions}")

        # Separator
        table.add_row("", "")

        # Quality metrics
        table.add_row("[bold yellow]Quality metrics:[/bold yellow]", "")

        if self.code_quality_score is not None:
            quality_icon = self._get_status_icon(self.code_quality_score, self.target_quality)
            table.add_row(
                "  Code quality:",
                f"[cyan]{self.code_quality_score}/100[/cyan] {quality_icon}"
            )
        else:
            table.add_row("  Code quality:", "[dim]Not yet measured[/dim]")

        if self.test_coverage is not None:
            coverage_icon = self._get_status_icon(self.test_coverage, self.target_coverage)
            table.add_row(
                "  Test coverage:",
                f"[cyan]{self.test_coverage:.0f}%[/cyan] (target: {self.target_coverage}%) {coverage_icon}"
            )
        else:
            table.add_row("  Test coverage:", "[dim]Not yet measured[/dim]")

        if self.accessibility_score:
            table.add_row("  Accessibility:", f"[cyan]{self.accessibility_score}[/cyan] ✓")
        else:
            table.add_row("  Accessibility:", "[dim]Not yet measured[/dim]")

        # Separator
        table.add_row("", "")

        # Human interventions
        if intervention_count > 0:
            table.add_row(
                "[bold yellow]Human interventions:[/bold yellow]",
                f"[cyan]{intervention_count}[/cyan]"
            )

        return table

    def render_compact(self) -> Panel:
        """Render compact dashboard view.

        Returns:
            Rich Panel object
        """
        runtime = self.metrics.get_runtime()
        completed = self.metrics.run.features_completed
        total = self.metrics.run.total_features
        velocity = self.metrics.get_velocity()
        total_cost = self.metrics.get_total_cost()

        pct = (completed / total * 100) if total > 0 else 0

        content = Text()
        content.append(f"Runtime: {self._format_duration(runtime)} | ", style="dim")
        content.append(f"Progress: {completed}/{total} ({pct:.0f}%) | ", style="cyan")
        content.append(f"Velocity: {velocity:.1f} f/h | ", style="green")
        content.append(f"Cost: ${total_cost:.2f}", style="yellow")

        return Panel(content, title="Autocoder", border_style="cyan")

    def start_live_display(self, refresh_per_second: float = 1.0, compact: bool = False) -> None:
        """Start live updating dashboard.

        Args:
            refresh_per_second: Refresh rate (default: 1 Hz)
            compact: Use compact view (default: False)
        """
        with Live(self.render_compact() if compact else self.render(),
                  console=self.console,
                  refresh_per_second=refresh_per_second) as live:
            try:
                while self.metrics.run.run_status == "in_progress":
                    time.sleep(1 / refresh_per_second)
                    live.update(self.render_compact() if compact else self.render())

                # Final update when complete
                live.update(self.render_compact() if compact else self.render())
            except KeyboardInterrupt:
                pass

    def update_quality_metrics(self, code_quality: Optional[int] = None,
                               test_coverage: Optional[float] = None,
                               accessibility: Optional[str] = None) -> None:
        """Update quality metrics.

        Args:
            code_quality: Code quality score (0-100)
            test_coverage: Test coverage percentage (0-100)
            accessibility: Accessibility score (e.g., "WCAG AA")
        """
        if code_quality is not None:
            self.code_quality_score = code_quality
        if test_coverage is not None:
            self.test_coverage = test_coverage
        if accessibility is not None:
            self.accessibility_score = accessibility

    def print_summary(self) -> None:
        """Print final summary after completion."""
        self.console.print("\n")
        self.console.print(self.render())
        self.console.print("\n")

        # Additional stats
        runtime = self.metrics.get_runtime()
        velocity = self.metrics.get_velocity()
        first_try_rate = self.metrics.get_first_try_rate()

        self.console.print(f"[bold green]✓ Run completed in {self._format_duration(runtime)}[/bold green]")
        self.console.print(f"  Average velocity: {velocity:.1f} features/hour")
        self.console.print(f"  First-try success rate: {first_try_rate:.0f}%")
        self.console.print(f"  Total cost: ${self.metrics.get_total_cost():.2f}")
        self.console.print("\n")


def create_progress_bar() -> Progress:
    """Create a rich progress bar for feature completion.

    Returns:
        Rich Progress object
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=Console()
    )


if __name__ == "__main__":
    # Example usage
    from metrics_collector import MetricsCollector
    from pathlib import Path
    import random

    project_dir = Path("test_project")
    project_dir.mkdir(exist_ok=True)

    # Create collector
    collector = MetricsCollector(project_dir, "Test Dashboard")
    collector.set_total_features(50)

    # Create dashboard
    dashboard = PerformanceDashboard(collector)

    # Simulate work in background
    import threading

    def simulate_work():
        collector.start_session(1)

        for i in range(50):
            collector.start_feature(i)
            time.sleep(0.2)  # Simulate work

            # Random success/failure
            first_try = random.random() > 0.4
            collector.track_feature_complete(
                feature_id=i,
                feature_name=f"Feature {i}",
                first_try=first_try,
                attempts=1 if first_try else 2
            )

            # Random API cost
            collector.track_api_call(random.uniform(0.02, 0.10))

            # Occasional skip
            if random.random() > 0.9:
                collector.track_feature_skip(i, f"Feature {i}")

        collector.end_session()
        collector.complete_run()

        # Update quality metrics at end
        dashboard.update_quality_metrics(
            code_quality=87,
            test_coverage=82,
            accessibility="WCAG AA"
        )

    # Start simulation in background
    thread = threading.Thread(target=simulate_work, daemon=True)
    thread.start()

    # Show live dashboard
    try:
        dashboard.start_live_display()
        dashboard.print_summary()
    finally:
        collector.close()
