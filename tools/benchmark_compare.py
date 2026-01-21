#!/usr/bin/env python3
"""
Benchmark Comparison Tool
=========================

Compare autocoder performance against alternative approaches.

Usage:
    python benchmark_compare.py --run1 benchmarks/run_123.json --run2 benchmarks/run_456.json
    python benchmark_compare.py --autocoder vs --manual  # Compare to baseline estimates
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import timedelta


class BenchmarkComparator:
    """Compare performance between different runs or approaches."""

    def __init__(self):
        """Initialize comparator."""
        pass

    def load_run_data(self, json_path: Path) -> Dict:
        """Load run data from JSON export.

        Args:
            json_path: Path to JSON file

        Returns:
            Run data dictionary
        """
        with open(json_path, 'r') as f:
            return json.load(f)

    def calculate_metrics(self, run_data: Dict) -> Dict:
        """Calculate metrics from run data.

        Args:
            run_data: Run data dictionary

        Returns:
            Calculated metrics
        """
        run = run_data["run"]
        features = run_data["features"]
        sessions = run_data["sessions"]
        interventions = run_data["interventions"]

        # Parse timestamps
        from datetime import datetime
        start = datetime.fromisoformat(run["start_time"]) if run["start_time"] else None
        end = datetime.fromisoformat(run["end_time"]) if run["end_time"] else None

        runtime = (end - start) if (start and end) else timedelta(0)
        runtime_hours = runtime.total_seconds() / 3600

        # Calculate rates
        first_try_pass = sum(1 for f in features if f["first_try_pass"])
        first_try_rate = (first_try_pass / len(features) * 100) if features else 0

        skipped = sum(1 for f in features if f["was_skipped"])
        skip_rate = (skipped / len(features) * 100) if features else 0

        # Cost
        total_cost = sum(s["api_cost"] for s in sessions)
        cost_per_feature = total_cost / run["features_completed"] if run["features_completed"] > 0 else 0

        # Velocity
        velocity = run["features_completed"] / runtime_hours if runtime_hours > 0 else 0

        return {
            "runtime_hours": runtime_hours,
            "features_completed": run["features_completed"],
            "total_features": run["total_features"],
            "velocity": velocity,
            "first_try_rate": first_try_rate,
            "skip_rate": skip_rate,
            "total_cost": total_cost,
            "cost_per_feature": cost_per_feature,
            "intervention_count": len(interventions),
            "session_count": len(sessions),
        }

    def estimate_baseline(self, approach: str, features_count: int) -> Dict:
        """Estimate metrics for baseline approaches.

        Args:
            approach: Approach name (manual, claude_skill, cursor)
            features_count: Number of features

        Returns:
            Estimated metrics
        """
        if approach == "manual":
            # Senior developer: 2 features/hour average
            hours = features_count / 2
            return {
                "runtime_hours": hours,
                "features_completed": features_count,
                "total_features": features_count,
                "velocity": 2.0,
                "first_try_rate": 95.0,  # Manual coding typically higher quality first-try
                "skip_rate": 0.0,  # No skipping in manual coding
                "total_cost": 0.0,  # No API costs
                "cost_per_feature": 0.0,
                "intervention_count": 0,  # N/A
                "session_count": int(hours / 4),  # Estimate 4-hour sessions
                "estimated": True,
            }

        elif approach == "claude_skill":
            # Claude Code skill: ~30% slower due to more manual interaction
            hours = (features_count / 2) * 1.3
            cost = features_count * 0.30  # Estimate ~$0.30 per feature
            return {
                "runtime_hours": hours,
                "features_completed": features_count,
                "total_features": features_count,
                "velocity": features_count / hours,
                "first_try_rate": 80.0,
                "skip_rate": 5.0,
                "total_cost": cost,
                "cost_per_feature": cost / features_count,
                "intervention_count": features_count * 0.3,  # 30% require intervention
                "session_count": int(hours / 3),
                "estimated": True,
            }

        elif approach == "cursor":
            # Cursor + Copilot: 2x faster than manual, but not as autonomous
            hours = features_count / 4
            cost = 20.0  # Flat subscription
            return {
                "runtime_hours": hours,
                "features_completed": features_count,
                "total_features": features_count,
                "velocity": 4.0,
                "first_try_rate": 85.0,
                "skip_rate": 2.0,
                "total_cost": cost,
                "cost_per_feature": cost / features_count,
                "intervention_count": 0,  # N/A
                "session_count": int(hours / 4),
                "estimated": True,
            }

        else:
            raise ValueError(f"Unknown approach: {approach}")

    def compare(self, run1: Dict, run2: Dict, label1: str = "Run 1", label2: str = "Run 2") -> str:
        """Generate comparison report.

        Args:
            run1: First run metrics
            run2: Second run metrics
            label1: Label for first run
            label2: Label for second run

        Returns:
            Comparison report as string
        """
        report = []

        report.append("╔" + "="*60 + "╗")
        report.append("║" + f"{label1} vs {label2}".center(60) + "║")
        report.append("╠" + "="*60 + "╣")
        report.append("║" + " "*60 + "║")

        # Comparison table
        metrics_to_compare = [
            ("Time to completion", "runtime_hours", "h", False),
            ("Total cost", "total_cost", "$", False),
            ("Features completed", "features_completed", "", True),
            ("Velocity", "velocity", "f/h", True),
            ("First-try success", "first_try_rate", "%", True),
            ("Skip rate", "skip_rate", "%", False),
            ("Human interventions", "intervention_count", "", False),
        ]

        for label, key, unit, higher_is_better in metrics_to_compare:
            val1 = run1.get(key, 0)
            val2 = run2.get(key, 0)

            # Calculate difference
            if val2 != 0:
                diff_pct = ((val1 - val2) / val2) * 100
            else:
                diff_pct = 0

            # Format values
            if unit == "$":
                val1_str = f"${val1:.2f}"
                val2_str = f"${val2:.2f}"
            elif unit == "%":
                val1_str = f"{val1:.1f}%"
                val2_str = f"{val2:.1f}%"
            elif unit == "h":
                val1_str = f"{val1:.1f}h"
                val2_str = f"{val2:.1f}h"
            else:
                val1_str = f"{val1:.1f}{unit}"
                val2_str = f"{val2:.1f}{unit}"

            # Determine winner
            if diff_pct == 0:
                diff_str = "="
            elif (diff_pct > 0 and higher_is_better) or (diff_pct < 0 and not higher_is_better):
                diff_str = f"(+{abs(diff_pct):.0f}%)"
            else:
                diff_str = f"(-{abs(diff_pct):.0f}%)"

            line = f"║  {label:<20} {val1_str:<12} {val2_str:<12} {diff_str:<10} ║"
            report.append(line)

        report.append("║" + " "*60 + "║")

        # Determine winner
        run1_wins = 0
        run2_wins = 0

        for _, key, _, higher_is_better in metrics_to_compare:
            val1 = run1.get(key, 0)
            val2 = run2.get(key, 0)

            if higher_is_better:
                if val1 > val2:
                    run1_wins += 1
                elif val2 > val1:
                    run2_wins += 1
            else:
                if val1 < val2:
                    run1_wins += 1
                elif val2 < val1:
                    run2_wins += 1

        if run1_wins > run2_wins:
            winner = label1
        elif run2_wins > run1_wins:
            winner = label2
        else:
            winner = "Tie"

        report.append(f"║  Winner: {winner:<50} ║")

        # Trade-offs
        report.append("║" + " "*60 + "║")

        if run1["total_cost"] < run2["total_cost"] and run1["runtime_hours"] > run2["runtime_hours"]:
            report.append(f"║  Trade-off: {label1} is cheaper but slower" + " "*17 + "║")
        elif run1["total_cost"] > run2["total_cost"] and run1["runtime_hours"] < run2["runtime_hours"]:
            report.append(f"║  Trade-off: {label1} is faster but more expensive" + " "*9 + "║")

        report.append("║" + " "*60 + "║")
        report.append("╚" + "="*60 + "╝")

        return "\n".join(report)

    def generate_markdown_comparison(self, runs: List[Tuple[str, Dict]]) -> str:
        """Generate markdown comparison table for multiple runs.

        Args:
            runs: List of (label, metrics) tuples

        Returns:
            Markdown table
        """
        if not runs:
            return ""

        md = []

        # Header
        md.append("# Benchmark Comparison")
        md.append("")
        md.append("| Metric | " + " | ".join(label for label, _ in runs) + " |")
        md.append("|--------|" + "|".join("--------" for _ in runs) + "|")

        # Metrics
        metrics_to_show = [
            ("Time to completion (hours)", "runtime_hours", "{:.1f}h"),
            ("Total cost", "total_cost", "${:.2f}"),
            ("Features completed", "features_completed", "{:.0f}"),
            ("Velocity (features/hour)", "velocity", "{:.1f}"),
            ("First-try success rate", "first_try_rate", "{:.1f}%"),
            ("Skip rate", "skip_rate", "{:.1f}%"),
            ("Human interventions", "intervention_count", "{:.0f}"),
        ]

        for label, key, fmt in metrics_to_show:
            values = [fmt.format(metrics.get(key, 0)) for _, metrics in runs]
            md.append(f"| {label} | " + " | ".join(values) + " |")

        md.append("")

        # Recommendation
        md.append("## Recommendation")
        md.append("")

        # Find best on different dimensions
        fastest = min(runs, key=lambda r: r[1]["runtime_hours"])
        cheapest = min(runs, key=lambda r: r[1]["total_cost"])
        highest_quality = max(runs, key=lambda r: r[1]["first_try_rate"])

        md.append(f"- **Fastest:** {fastest[0]} ({fastest[1]['runtime_hours']:.1f}h)")
        md.append(f"- **Cheapest:** {cheapest[0]} (${cheapest[1]['total_cost']:.2f})")
        md.append(f"- **Highest Quality:** {highest_quality[0]} ({highest_quality[1]['first_try_rate']:.1f}% first-try)")
        md.append("")

        return "\n".join(md)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compare autocoder benchmark runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two actual runs
  python benchmark_compare.py --run1 benchmarks/run_1.json --run2 benchmarks/run_2.json

  # Compare autocoder to manual coding estimate
  python benchmark_compare.py --run1 benchmarks/run_1.json --baseline manual

  # Compare multiple runs
  python benchmark_compare.py --run1 benchmarks/run_1.json --run2 benchmarks/run_2.json --run3 benchmarks/run_3.json --markdown
        """
    )

    parser.add_argument("--run1", type=str, help="Path to first run JSON")
    parser.add_argument("--run2", type=str, help="Path to second run JSON")
    parser.add_argument("--run3", type=str, help="Path to third run JSON (optional)")
    parser.add_argument("--baseline", type=str, choices=["manual", "claude_skill", "cursor"],
                        help="Compare to baseline estimate")
    parser.add_argument("--markdown", action="store_true", help="Output as markdown table")
    parser.add_argument("--output", type=str, help="Save output to file")

    args = parser.parse_args()

    comparator = BenchmarkComparator()

    # Load runs
    runs = []

    if args.run1:
        data1 = comparator.load_run_data(Path(args.run1))
        metrics1 = comparator.calculate_metrics(data1)
        runs.append(("Autocoder", metrics1))

    if args.run2:
        data2 = comparator.load_run_data(Path(args.run2))
        metrics2 = comparator.calculate_metrics(data2)
        runs.append(("Run 2", metrics2))

    if args.run3:
        data3 = comparator.load_run_data(Path(args.run3))
        metrics3 = comparator.calculate_metrics(data3)
        runs.append(("Run 3", metrics3))

    if args.baseline and runs:
        # Use feature count from first run
        features_count = runs[0][1]["total_features"]
        baseline_metrics = comparator.estimate_baseline(args.baseline, int(features_count))
        runs.append((args.baseline.replace("_", " ").title(), baseline_metrics))

    # Generate output
    if not runs:
        print("Error: No runs specified", file=sys.stderr)
        sys.exit(1)

    if args.markdown:
        output = comparator.generate_markdown_comparison(runs)
    elif len(runs) == 2:
        output = comparator.compare(runs[0][1], runs[1][1], runs[0][0], runs[1][0])
    else:
        output = comparator.generate_markdown_comparison(runs)

    # Save or print
    if args.output:
        Path(args.output).write_text(output)
        print(f"Comparison saved to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
